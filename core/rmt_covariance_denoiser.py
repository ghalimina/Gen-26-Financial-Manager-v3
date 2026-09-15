#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/rmt_covariance_denoiser.py — Random Matrix Theory (RMT) Covariance Denoiser
# Implements Marcos López de Prado's Marchenko-Pastur Denoising Framework:
# 1. Computes empirical correlation matrix eigenvalues and spectral density.
# 2. Identifies theoretical noise bounds (lambda_min, lambda_max).
# 3. Applies Constant Residual Eigenvalue Shrinkage to purge noise while
#    preserving authentic market and sector signals.
# 4. Dramatically reduces condition number kappa(C), preventing portfolio optimizer collapse.
# =============================================================================

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class RmtCovarianceDenoiser:
    """
    Marchenko-Pastur Random Matrix Theory (RMT) Covariance & Correlation Denoising Engine.
    """

    @staticmethod
    def marchenko_pastur_limits(variance: float, t_samples: int, n_assets: int) -> Tuple[float, float]:
        """
        Calculates theoretical Marchenko-Pastur spectral limits:
        q = T / N
        lambda_min = sigma^2 * (1 - sqrt(1 / q))^2
        lambda_max = sigma^2 * (1 + sqrt(1 / q))^2
        """
        q = float(t_samples) / max(float(n_assets), 1.0)
        q_inv_sqrt = math.sqrt(1.0 / q)
        lambda_min = variance * ((1.0 - q_inv_sqrt) ** 2)
        lambda_max = variance * ((1.0 + q_inv_sqrt) ** 2)
        return lambda_min, lambda_max

    @classmethod
    def denoise_correlation_matrix(
        cls,
        empirical_corr: np.ndarray,
        t_samples: int,
        shrink_noise: bool = True
    ) -> Dict[str, Any]:
        """
        Purges random noise from an empirical correlation matrix using RMT:
        - Decomposes C = V * Lambda * V^T
        - Replaces eigenvalues lambda <= lambda_max with their average
        - Reconstructs cleaned correlation matrix C_clean
        - Normalizes diagonal to 1.0
        """
        corr = np.asarray(empirical_corr, dtype=float)
        n_assets = corr.shape[0]

        # Initial condition number
        cond_before = float(np.linalg.cond(corr))

        # Eigenvalue decomposition (eigh for symmetric matrices)
        eigenvalues, eigenvectors = np.linalg.eigh(corr)

        # Sort descending
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Find noise upper bound
        lambda_min, lambda_max = cls.marchenko_pastur_limits(
            variance=1.0,
            t_samples=t_samples,
            n_assets=n_assets
        )

        # Separate signals and noise
        signal_mask = eigenvalues > lambda_max
        noise_mask = ~signal_mask

        num_signals = int(np.sum(signal_mask))
        num_noise = int(np.sum(noise_mask))

        cleaned_eigenvalues = eigenvalues.copy()

        if num_noise > 0 and shrink_noise:
            # Constant residual shrinkage: set all noise eigenvalues to their mean
            mean_noise_eigenvalue = np.mean(eigenvalues[noise_mask])
            cleaned_eigenvalues[noise_mask] = mean_noise_eigenvalue

        # Reconstruct cleaned correlation matrix
        diag_clean = np.diag(cleaned_eigenvalues)
        cleaned_corr = eigenvectors @ diag_clean @ eigenvectors.T

        # Normalize diagonal to 1.0
        diag_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(cleaned_corr)))
        normalized_corr = diag_inv_sqrt @ cleaned_corr @ diag_inv_sqrt
        np.fill_diagonal(normalized_corr, 1.0)

        cond_after = float(np.linalg.cond(normalized_corr))

        return {
            "cleaned_matrix": normalized_corr,
            "eigenvalues_original": [round(float(e), 4) for e in eigenvalues],
            "eigenvalues_cleaned": [round(float(e), 4) for e in cleaned_eigenvalues],
            "lambda_min": round(lambda_min, 4),
            "lambda_max": round(lambda_max, 4),
            "num_signal_components": num_signals,
            "num_noise_components": num_noise,
            "noise_fraction_pct": round((num_noise / max(n_assets, 1)) * 100.0, 1),
            "condition_number_before": round(cond_before, 2),
            "condition_number_after": round(cond_after, 2),
            "stability_gain_factor": round(cond_before / max(cond_after, 1e-4), 2)
        }

    @classmethod
    def denoise_covariance_matrix(
        cls,
        empirical_cov: np.ndarray,
        t_samples: int
    ) -> np.ndarray:
        """
        Denoises full covariance matrix by decomposing into standard deviations and correlation,
        denoising correlation via RMT, and scaling back with empirical volatilities.
        """
        cov = np.asarray(empirical_cov, dtype=float)
        vols = np.sqrt(np.diag(cov))
        vols_inv = np.diag(1.0 / np.maximum(vols, 1e-6))

        # Corr = D^-1 * Cov * D^-1
        corr = vols_inv @ cov @ vols_inv
        res = cls.denoise_correlation_matrix(corr, t_samples=t_samples)
        clean_corr = res["cleaned_matrix"]

        # Re-scale: Cov_clean = D * Corr_clean * D
        d_mat = np.diag(vols)
        return d_mat @ clean_corr @ d_mat
