#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/gnn_sector_contagion_engine.py — Graph Neural Network (GNN) Contagion Engine
# Implements Kipf & Welling Graph Convolutional Networks (GCN) for EGX:
# 1. Models stock network topology via economic adjacency (supply chains, credit links, GDRs).
# 2. Computes Symmetrically Normalized Laplacian Propagation (A_hat = D^-0.5 * A_tilde * D^-0.5).
# 3. Predicts systemic shock spillover when an anchor stock or sector leader drops.
# 4. Measures Node Contagion Centrality to identify potential domino risk epicenters.
# =============================================================================

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class GnnSectorContagionEngine:
    """
    Graph Convolutional Network (GCN) Engine for Systemic Financial Contagion Modeling.
    """

    CORE_NODES = [
        "COMI.CA",  # Banking anchor
        "FWRY.CA",  # Fintech & payments
        "EFIH.CA",  # Digital payments & state contracts
        "SWDY.CA",  # Industrial cables & infrastructure
        "TMGH.CA",  # Megaproject real estate
        "ORAS.CA",  # Global construction
        "EGAL.CA",  # Basic materials & aluminum exports
        "ABUK.CA",  # Fertilizers & gas input
        "ETEL.CA",  # Sovereign telecom infrastructure
        "HRHO.CA"   # Investment banking & margin brokerage
    ]

    # Topological economic linkages between key EGX pillars
    # Format: (Node_A, Node_B, Edge_Weight)
    ECONOMIC_LINKS = [
        ("COMI.CA", "HRHO.CA", 0.85),  # Joint banking & capital markets exposure
        ("COMI.CA", "TMGH.CA", 0.70),  # Major syndicated real estate credit
        ("COMI.CA", "SWDY.CA", 0.65),  # Corporate credit & trade finance
        ("FWRY.CA", "EFIH.CA", 0.80),  # Direct digital fintech competition & synergy
        ("FWRY.CA", "COMI.CA", 0.60),  # Digital banking channel clearing
        ("SWDY.CA", "ORAS.CA", 0.82),  # Infrastructure EPC supply consortiums
        ("SWDY.CA", "EGAL.CA", 0.75),  # Metal inputs for cable manufacturing
        ("ABUK.CA", "EGAL.CA", 0.60),  # Heavy energy intensive export sector
        ("TMGH.CA", "ORAS.CA", 0.72),  # Major contracting & civil works
        ("ETEL.CA", "FWRY.CA", 0.65),  # Telecom cash collection networks
        ("ETEL.CA", "EFIH.CA", 0.60),  # Government telecom data infrastructure
    ]

    @classmethod
    def build_adjacency_matrix(cls) -> Tuple[np.ndarray, List[str]]:
        """Constructs symmetric adjacency matrix with self-loops."""
        nodes = cls.CORE_NODES
        n = len(nodes)
        node_map = {nodes[i]: i for i in range(n)}
        adj = np.zeros((n, n), dtype=float)

        # Self-loops (A_tilde = A + I)
        np.fill_diagonal(adj, 1.0)

        for u, v, w in cls.ECONOMIC_LINKS:
            if u in node_map and v in node_map:
                i, j = node_map[u], node_map[v]
                adj[i, j] = w
                adj[j, i] = w

        return adj, nodes

    @classmethod
    def normalized_graph_laplacian(cls, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Computes Kipf & Welling symmetrically normalized Laplacian:
        A_hat = D^-0.5 * A_tilde * D^-0.5
        """
        degrees = np.sum(adj_matrix, axis=1)
        deg_inv_sqrt = 1.0 / np.sqrt(np.maximum(degrees, 1e-6))
        d_mat_inv_sqrt = np.diag(deg_inv_sqrt)
        return d_mat_inv_sqrt @ adj_matrix @ d_mat_inv_sqrt

    @classmethod
    def simulate_shock_contagion(
        cls,
        shock_origin: str = "COMI.CA",
        shock_magnitude_pct: float = -5.0,
        propagation_steps: int = 2
    ) -> Dict[str, Any]:
        """
        Simulates systemic contagion shock propagation across the EGX network:
        - Injects initial impulse vector X_0 at shock_origin
        - Multiplies recursively by A_hat with damping factor alpha = 0.75
        """
        adj, nodes = cls.build_adjacency_matrix()
        a_hat = cls.normalized_graph_laplacian(adj)
        n = len(nodes)

        sym_clean = shock_origin.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        origin_idx = nodes.index(sym_clean) if sym_clean in nodes else 0

        # Initial impulse feature vector
        impulse = np.zeros(n, dtype=float)
        impulse[origin_idx] = shock_magnitude_pct

        damping = 0.75
        state = impulse.copy()

        # Multi-hop Graph Convolutional propagation
        for step in range(propagation_steps):
            state = damping * (a_hat @ state) + (1.0 - damping) * impulse

        results = []
        for i, node in enumerate(nodes):
            spillover = state[i]
            is_origin = (i == origin_idx)
            results.append({
                "ticker": node,
                "projected_shock_pct": round(float(spillover), 2),
                "is_shock_epicenter": is_origin,
                "vulnerability_tier": "CRITICAL" if abs(spillover) >= 2.5 else ("ELEVATED" if abs(spillover) >= 1.0 else "MODERATE")
            })

        results.sort(key=lambda x: abs(x["projected_shock_pct"]), reverse=True)

        # Measure systemic centrality: sum of column edge weights
        centralities = np.sum(adj, axis=0) - 1.0  # exclude self loop
        most_central_idx = int(np.argmax(centralities))

        return {
            "shock_origin": nodes[origin_idx],
            "initial_shock_pct": shock_magnitude_pct,
            "propagation_hops": propagation_steps,
            "most_central_systemic_node": nodes[most_central_idx],
            "spillover_projections": results,
            "summary_ar": (
                f"محاكاة صدمة بيانية: هبوط سهم {nodes[origin_idx]} بنسبة {shock_magnitude_pct:.1f}% "
                f"يؤدي إلى انتقال عدوى مباشرة لأقرب الأسهم ارتباطاً، وعلى رأسها {results[1]['ticker']} "
                f"(هبوط متوقع {results[1]['projected_shock_pct']:.2f}%)."
            )
        }
