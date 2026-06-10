"""
Classification Agent - Rule-based resource type detection (no API keys needed).
"""

import re
from typing import Dict, Any, List
from loguru import logger


class ClassificationAgent:
    """Agent for classifying resource types using keyword matching."""
    
    TYPE_KEYWORD_MAP = {
        "notes": [
            "notes", "lecture notes", "chapter", "unit", "summary", 
            "study material", "study notes", "class notes", "handout"
        ],
        "question_paper": [
            "question paper", "previous year", "exam paper", "test paper", 
            "pyq", "solved paper", "model paper", "sample paper", 
            "past paper", "examination", "midterm", "final exam"
        ],
        "syllabus": [
            "syllabus", "curriculum", "course outline", "course structure",
            "course content", "course plan", "learning objectives"
        ],
        "practical": [
            "practical", "lab", "experiment", "laboratory", "manual",
            "lab manual", "practical file", "viva", "hands-on"
        ],
        "tutorial": [
            "tutorial", "assignment", "exercise", "worksheet", 
            "problem set", "practice", "homework", "problem sheet"
        ],
        "reference": [
            "reference", "book", "textbook", "reading", "ebook",
            "publication", "journal", "article", "paper"
        ],
    }
    
    def __init__(self, use_llm: bool = False):
        # LLM disabled - using rule-based only
        self.use_llm = False
    
    def classify(
        self,
        title: str,
        content_snippet: str,
        keywords: list = None,
    ) -> Dict[str, Any]:
        """Classify resource type using keyword matching."""
        return self._classify_by_keywords(title, content_snippet, keywords or [])
    
    def _classify_by_keywords(
        self,
        title: str,
        content: str,
        keywords: list
    ) -> Dict[str, Any]:
        """Classify based on keywords."""
        title_text = title.lower()
        combined = f"{title} {content} {' '.join(keywords)}".lower()
        
        scores = {}
        matched_keywords = {}
        
        for resource_type, type_keywords in self.TYPE_KEYWORD_MAP.items():
            matches = [kw for kw in type_keywords if self._keyword_present(kw, combined)]
            if matches:
                title_matches = sum(1 for kw in matches if self._keyword_present(kw, title_text))
                scores[resource_type] = len(matches) + title_matches
                matched_keywords[resource_type] = matches
        
        if scores:
            best_type = max(scores, key=scores.get)
            # Higher confidence for more matches
            confidence = min(100, 45 + scores[best_type] * 15)
            return {
                "resource_type": best_type,
                "confidence": confidence,
                "reasoning": f"Matched: {matched_keywords.get(best_type, [])}",
            }
        
        return {
            "resource_type": "other",
            "confidence": 30,
            "reasoning": "No strong keyword matches",
        }

    def _keyword_present(self, keyword: str, text: str) -> bool:
        """Match keyword as a phrase instead of a loose substring."""
        pattern = rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])"
        return re.search(pattern, text) is not None
