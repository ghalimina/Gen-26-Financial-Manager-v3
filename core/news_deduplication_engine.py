#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/news_deduplication_engine.py — Cross-Feed News Deduplication & Story Clustering
# Part of GEN-26 Expanded Architecture Version 2.0
# Prevents artificial sentiment score inflation caused by multi-source syndicate reporting.
# =============================================================================

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.data_sources_registry import DataSourceRegistry

logger = logging.getLogger("GEN26.NewsDeduplication")


class NewsDeduplicationEngine:
    """
    Groups duplicate reports of the same corporate or macroeconomic event across
    multiple intelligence feeds (Reuters, Mubasher, Zawya, Enterprise, Al Borsa)
    into single canonical event clusters with weighted consensus sentiment.
    """

    SIMILARITY_THRESHOLD: float = 0.30

    SYNONYM_MAP = {
        "cib": "commercial_international_bank",
        "البنك التجاري الدولي": "commercial_international_bank",
        "comi": "commercial_international_bank",
        "elsewedy": "elsewedy_electric",
        "السويدي": "elsewedy_electric",
        "swdy": "elsewedy_electric",
        "talaat": "talaat_moustafa_group",
        "طلعت مصطفى": "talaat_moustafa_group",
        "tmgh": "talaat_moustafa_group",
        "أرباح": "earnings",
        "نتائج": "earnings",
        "profits": "earnings",
        "عقد": "contract",
        "صفقة": "contract",
        "توزيعات": "dividends",
        "كوبون": "dividends"
    }

    @classmethod
    def _normalize_and_tokenize(cls, text: str) -> set:
        if not text:
            return set()
        cleaned = text.lower()
        # Clean punctuation
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        # Arabic char normalization
        cleaned = re.sub(r'[أإآ]', 'ا', cleaned)
        cleaned = re.sub(r'ة', 'ه', cleaned)
        cleaned = re.sub(r'ى', 'ي', cleaned)

        # Apply synonym mapping
        for k, v in cls.SYNONYM_MAP.items():
            if k in cleaned:
                cleaned = cleaned.replace(k, f" {v} ")

        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
        return set(tokens)

    @classmethod
    def compute_similarity(cls, text_a: str, text_b: str) -> float:
        """
        Computes Jaccard token similarity with synonym normalization.
        """
        set_a = cls._normalize_and_tokenize(text_a)
        set_b = cls._normalize_and_tokenize(text_b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        if union == 0:
            return 0.0
        return float(intersection / union)

    @classmethod
    def cluster_and_deduplicate(
        cls,
        raw_articles: List[Dict[str, Any]],
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Processes a raw list of articles and partitions them into distinct event clusters.
        Returns deduplicated unique events and cluster diagnostics.
        """
        if not raw_articles:
            return {
                "raw_count": 0,
                "unique_clusters_count": 0,
                "reduction_pct": 0.0,
                "clusters": []
            }

        thresh = similarity_threshold if similarity_threshold is not None else cls.SIMILARITY_THRESHOLD
        clusters = []

        for item in raw_articles:
            headline = item.get("headline") or item.get("title") or ""
            ticker = (item.get("ticker") or item.get("symbol") or "GENERAL").upper()
            source = (item.get("source") or item.get("source_name") or "UNKNOWN").upper()
            src_weight = DataSourceRegistry.get_source_reliability_weight(source)
            sent_score = float(item.get("sentiment_score", 0.0))

            assigned = False
            for cluster in clusters:
                # Same ticker check
                same_ticker = (cluster["ticker"] == ticker and ticker != "GENERAL")
                general_match = (ticker == "GENERAL" or cluster["ticker"] == "GENERAL")

                sim = cls.compute_similarity(headline, cluster["canonical_headline"])

                # If same ticker and some topical overlap, or general high similarity
                if (same_ticker and sim >= 0.15) or (same_ticker and len(cls._normalize_and_tokenize(headline).intersection(cls._normalize_and_tokenize(cluster["canonical_headline"]))) >= 1) or sim >= thresh:
                    # Add to existing cluster
                    cluster["articles"].append(item)
                    cluster["sources"].append(source)
                    cluster["source_weights"].append(src_weight)
                    cluster["raw_sentiments"].append(sent_score)

                    # Update canonical article if new item is from a higher tier source
                    if src_weight > cluster["max_source_weight"]:
                        cluster["canonical_headline"] = headline
                        cluster["canonical_article"] = item
                        cluster["max_source_weight"] = src_weight

                    assigned = True
                    break

            if not assigned:
                # Create a new event cluster
                clusters.append({
                    "cluster_id": f"CLUS_{len(clusters)+1:04d}_{ticker}",
                    "ticker": ticker,
                    "canonical_headline": headline,
                    "canonical_article": item,
                    "max_source_weight": src_weight,
                    "sources": [source],
                    "source_weights": [src_weight],
                    "raw_sentiments": [sent_score],
                    "articles": [item]
                })

        # Calculate weighted sentiment and confidence for each cluster
        deduplicated_clusters = []
        for c in clusters:
            weights = c["source_weights"]
            sentiments = c["raw_sentiments"]
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_sentiment = sum(s * w for s, w in zip(sentiments, weights)) / total_weight
            else:
                weighted_sentiment = float(sum(sentiments) / len(sentiments)) if sentiments else 0.0

            article_count = len(c["articles"])
            unique_sources = len(set(c["sources"]))

            # Multi-source corroboration boost for confidence
            corroboration_factor = min(1.0, 0.60 + 0.15 * unique_sources)

            deduplicated_clusters.append({
                "cluster_id": c["cluster_id"],
                "ticker": c["ticker"],
                "canonical_headline": c["canonical_headline"],
                "primary_source": c["canonical_article"].get("source") or c["sources"][0],
                "articles_in_cluster": article_count,
                "reporting_sources": list(set(c["sources"])),
                "cluster_sentiment_score": round(float(weighted_sentiment), 4),
                "corroboration_confidence": round(float(corroboration_factor), 2),
                "timestamp_latest": c["canonical_article"].get("timestamp") or datetime.now().isoformat()
            })

        raw_count = len(raw_articles)
        unique_count = len(deduplicated_clusters)
        reduction_pct = round(((raw_count - unique_count) / raw_count) * 100.0, 1) if raw_count > 0 else 0.0

        return {
            "raw_count": raw_count,
            "unique_clusters_count": unique_count,
            "reduction_pct": reduction_pct,
            "clusters": deduplicated_clusters
        }


if __name__ == "__main__":
    print("Testing NewsDeduplicationEngine...")
    sample_news = [
        {"headline": "CIB reports 45% net profit growth in Q2 2026", "source": "REUTERS", "ticker": "COMI.CA", "sentiment_score": 0.85},
        {"headline": "البنك التجاري الدولي يحقق نموا 45% في أرباح الربع الثاني", "source": "MUBASHER", "ticker": "COMI.CA", "sentiment_score": 0.80},
        {"headline": "Commercial International Bank Q2 net profit surges 45 pct", "source": "ZAWYA", "ticker": "COMI.CA", "sentiment_score": 0.82},
        {"headline": "Elsewedy Electric signs 200M USD power transmission contract", "source": "ENTERPRISE", "ticker": "SWDY.CA", "sentiment_score": 0.90},
        {"headline": "السويدي اليكتريك توقع عقدا بقيمة 200 مليون دولار", "source": "AL_BORSA", "ticker": "SWDY.CA", "sentiment_score": 0.88}
    ]
    res = NewsDeduplicationEngine.cluster_and_deduplicate(sample_news)
    print(json.dumps(res, indent=2, ensure_ascii=False))
