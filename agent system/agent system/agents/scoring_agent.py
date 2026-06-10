"""
Scoring Agent - Calculates final scores for resources.
"""

from typing import Dict, Any
from loguru import logger

from config.settings import settings
from utils.helpers import calculate_domain_trust


class ScoringAgent:
    """Agent for calculating final resource scores."""
    
    # Weight configuration
    WEIGHTS_WITH_COLLEGE = {
        "relevance": 0.50,
        "type_confidence": 0.25,
        "college_confidence": 0.10,
        "domain_trust": 0.15,
    }
    WEIGHTS_NO_COLLEGE = {
        "relevance": 0.55,
        "type_confidence": 0.30,
        "college_confidence": 0.00,
        "domain_trust": 0.15,
    }
    
    def __init__(self, threshold: int = None):
        self.threshold = threshold or max(settings.final_score_threshold, 90)
    
    def score(
        self,
        relevance_score: float,
        type_confidence: float,
        college_confidence: float,
        domain: str,
        college_required: bool = True,
    ) -> Dict[str, Any]:
        """Calculate final score for a resource."""
        weights = self.WEIGHTS_WITH_COLLEGE if college_required else self.WEIGHTS_NO_COLLEGE

        # Normalize scores to 0-100
        relevance_norm = min(100, max(0, relevance_score))
        type_norm = min(100, max(0, type_confidence))
        college_norm = min(100, max(0, college_confidence))
        
        # Calculate domain trust
        domain_trust = calculate_domain_trust(domain, settings.trusted_domains_list)
        domain_score = domain_trust * 66.67  # Scale to ~100
        
        # Calculate weighted score
        final_score = (
            relevance_norm * weights["relevance"] +
            type_norm * weights["type_confidence"] +
            college_norm * weights["college_confidence"] +
            domain_score * weights["domain_trust"]
        )
        
        # Determine if it passes threshold
        passes_threshold = final_score >= self.threshold
        
        return {
            "final_score": round(final_score, 2),
            "domain_trust_score": round(domain_trust, 2),
            "passes_threshold": passes_threshold,
            "threshold": self.threshold,
            "college_required": college_required,
            "score_breakdown": {
                "relevance": round(relevance_norm * weights["relevance"], 2),
                "type_confidence": round(type_norm * weights["type_confidence"], 2),
                "college_confidence": round(college_norm * weights["college_confidence"], 2),
                "domain_trust": round(domain_score * weights["domain_trust"], 2),
            },
        }
