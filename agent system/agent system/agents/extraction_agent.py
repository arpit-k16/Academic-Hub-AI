"""
Extraction Agent - Cleans and structures extracted content.
"""

import re
import json
from typing import Dict, Any, List
from loguru import logger


class ExtractionAgent:
    """Agent for cleaning and structuring extracted content."""
    
    # Keywords to detect resource types
    TYPE_KEYWORDS = {
        "notes": ["notes", "lecture", "chapter", "unit", "summary"],
        "question_paper": ["question paper", "previous year", "exam", "test", "pyq", "sample paper"],
        "syllabus": ["syllabus", "curriculum", "course outline", "course content"],
        "practical": ["practical", "lab", "experiment", "laboratory", "manual"],
        "tutorial": ["tutorial", "assignment", "exercise", "worksheet", "practice"],
    }
    
    def extract(self, crawl_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure content from crawl result."""
        if not crawl_result.get("success"):
            return {
                "valid": False,
                "error": crawl_result.get("error", "Crawl failed"),
            }
        
        title = self._clean_title(crawl_result.get("title", ""))
        content = crawl_result.get("content", "")
        
        # Detect keywords
        keywords = self._detect_keywords(title, content)
        
        return {
            "valid": True,
            "title": title,
            "url": crawl_result.get("url", ""),
            "content_snippet": content[:500] if content else "",
            "full_content": content,
            "file_type": crawl_result.get("file_type", "html"),
            "detected_keywords": keywords,
            "keyword_json": json.dumps(keywords),
        }
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title."""
        if not title:
            return ""
        # Remove common suffixes
        title = re.sub(r"\s*[-|]\s*PDF.*$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*[-|]\s*Download.*$", "", title, flags=re.IGNORECASE)
        # Clean whitespace
        title = " ".join(title.split())
        return title[:200]
    
    def _detect_keywords(self, title: str, content: str) -> List[str]:
        """Detect relevant keywords from title and content."""
        combined = f"{title} {content}".lower()
        found_keywords = []
        
        for category, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
