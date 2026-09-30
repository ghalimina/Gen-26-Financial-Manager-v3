#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/precompute_rankings.py — Background Pre-computation of Universe Rankings
# Pre-computes and caches full 244-stock rankings to disk for instantaneous (sub-10ms)
# web dashboard serving.
# =============================================================================

import os
import sys
import json
import time
import logging

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_horizon_engine import MultiHorizonEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PrecomputeRankings")

DATA_DIR = os.path.join(WORKSPACE, "data")
PRECOMPUTED_FILE = os.path.join(DATA_DIR, "precomputed_rankings.json")


def precompute():
    logger.info("Starting background pre-computation of universe rankings...")
    t0 = time.time()
    
    # 1. Compute Core Top Liquid Universe
    core_rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="core", force_refresh=True)
    logger.info(f"Core rankings pre-computed: {len(core_rankings)} stocks in {time.time()-t0:.2f}s")
    
    # 2. Compute Full Active Universe
    t1 = time.time()
    all_rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all", force_refresh=True)
    logger.info(f"All rankings pre-computed: {len(all_rankings)} stocks in {time.time()-t1:.2f}s")

    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mtime": time.time(),
        "core": core_rankings,
        "all": all_rankings
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_path = f"{PRECOMPUTED_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, PRECOMPUTED_FILE)
    logger.info(f"Successfully saved precomputed rankings to {PRECOMPUTED_FILE} (Total time: {time.time()-t0:.2f}s)")


if __name__ == "__main__":
    precompute()
