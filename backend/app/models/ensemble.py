"""
SkyGuard AI - Multi-Tier Ensemble Meta-Classifier
Combines Physics-Informed Rules, Temporal Autoencoder Residuals,
Multivariate Isolation Forest, and Streaming Statistical Filters.
"""

from typing import Dict, Any
from backend.app.core.config import config


class AnomalyEnsembleMetaScorer:
    def __init__(self):
        self.w_physics = config.weight_physics
        self.w_ae = config.weight_autoencoder
        self.w_if = config.weight_isolation_forest
        self.w_stat = config.weight_statistical_zscore

    def evaluate(
        self,
        physics_res: Dict[str, Any],
        ae_res: Dict[str, Any],
        if_res: Dict[str, Any],
        stat_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes weighted consensus anomaly confidence score (0.0 to 1.0)
        and classifies severity level.
        """
        score_physics = physics_res.get("physics_anomaly_score", 0.0)
        score_ae = ae_res.get("ae_anomaly_prob", 0.0)
        score_if = if_res.get("isolation_anomaly_prob", 0.0)
        score_stat = stat_res.get("stat_anomaly_score", 0.0)

        # Base weighted sum
        weighted_score = (
            (self.w_physics * score_physics) +
            (self.w_ae * score_ae) +
            (self.w_if * score_if) +
            (self.w_stat * score_stat)
        )

        # Critical overrides: if direct physical law is broken or sensor is flatlined (ADC lockup)
        if physics_res.get("is_physics_violation", False) and score_physics >= 0.8:
            confidence_score = max(weighted_score, score_physics)
        elif stat_res.get("is_flatline", False):
            confidence_score = max(weighted_score, 0.92)
        elif score_stat >= 0.85:
            confidence_score = max(weighted_score, 0.88)
        elif score_stat >= 0.70 and (score_if > 0.40 or score_ae > 0.30 or score_physics > 0.30):
            # When statistical filter and at least one other model agree on anomaly
            confidence_score = max(weighted_score, 0.85)
        else:
            confidence_score = weighted_score

        confidence_score = round(min(1.0, max(0.0, confidence_score)), 4)

        # Determine Severity Level
        if confidence_score >= config.thresh_critical:
            severity = "CRITICAL"
            is_anomaly = True
        elif confidence_score >= config.thresh_high:
            severity = "HIGH"
            is_anomaly = True
        elif confidence_score >= config.thresh_medium:
            severity = "MEDIUM"
            is_anomaly = True
        elif confidence_score >= config.thresh_low:
            severity = "LOW"
            is_anomaly = True
        else:
            severity = "NORMAL"
            is_anomaly = False

        return {
            "is_anomaly": is_anomaly,
            "confidence_score": confidence_score,
            "severity": severity,
            "component_scores": {
                "physics": round(score_physics, 4),
                "autoencoder": round(score_ae, 4),
                "isolation_forest": round(score_if, 4),
                "statistical": round(score_stat, 4)
            }
        }


ensemble_meta_scorer = AnomalyEnsembleMetaScorer()
