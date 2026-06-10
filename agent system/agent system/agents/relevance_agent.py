"""
Relevance Agent - Rule-based relevance scoring (no API keys needed).
"""

import re
from typing import Dict, Any, List

from config.settings import settings


class RelevanceAgent:
    """Agent for evaluating resource relevance using transparent rules."""

    POSITIVE_KEYWORDS = [
        "notes",
        "lecture",
        "lecture notes",
        "slides",
        "syllabus",
        "course outline",
        "course content",
        "question paper",
        "previous year",
        "pyq",
        "exam",
        "tutorial",
        "assignment",
        "practical",
        "lab",
        "chapter",
        "unit",
        "module",
        "study material",
        "pdf",
        "download",
        "university",
        "college",
        "course",
        "semester",
        "academic",
        "learning",
        "reference",
        "textbook",
        "solution",
    ]

    NEGATIVE_KEYWORDS = [
        "buy now",
        "discount",
        "sale",
        "shopping",
        "cart",
        "price",
        "casino",
        "betting",
        "loan",
        "credit",
        "insurance",
        "forex",
        "click here",
        "subscribe",
        "free trial",
        "limited offer",
        "advertisement",
        "sponsored",
        "affiliate",
        "dating",
        "login required",
        "admission open",
        "apply now",
    ]

    ACADEMIC_DOMAINS = [
        ".edu",
        ".ac.in",
        ".ac.uk",
        ".edu.in",
        ".gov",
        "nptel",
        "swayam",
        "coursera",
        "edx",
        "khan",
        "university",
        "college",
        "institute",
    ]

    STOPWORDS = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "i",
        "ii",
        "iii",
        "iv",
        "v",
    }

    def evaluate(
        self,
        course_code: str,
        course_name: str,
        title: str,
        content_snippet: str,
        url: str,
    ) -> Dict[str, Any]:
        """Evaluate relevance of a resource using exact course/resource evidence."""
        combined_text = f"{title} {content_snippet} {url}".lower()
        url_lower = url.lower()

        positive_score = self._count_phrase_matches(combined_text, self.POSITIVE_KEYWORDS)
        negative_score = self._count_phrase_matches(combined_text, self.NEGATIVE_KEYWORDS)
        course_signal = self._course_signal_score(course_code, course_name, combined_text)
        domain_score = self._check_academic_domain(url_lower)
        resource_signal = self._resource_signal_score(combined_text, url_lower)

        confidence_score = (
            10
            + course_signal
            + min(positive_score * 7, 28)
            + resource_signal
            + domain_score
            - negative_score * 22
        )
        confidence_score = max(0, min(100, confidence_score))

        threshold_score = int(max(settings.relevance_threshold, 0.9) * 100)
        has_real_course_match = course_signal >= 30
        has_resource_evidence = positive_score > 0 or resource_signal >= 15
        is_relevant = (
            confidence_score >= threshold_score
            and negative_score == 0
            and has_real_course_match
            and has_resource_evidence
        )

        reasons = []
        if course_signal > 0:
            reasons.append(f"course evidence score {course_signal}")
        if positive_score > 0:
            reasons.append(f"academic keywords found ({positive_score})")
        if resource_signal > 0:
            reasons.append(f"resource evidence score {resource_signal}")
        if domain_score > 0:
            reasons.append("academic domain")
        if negative_score > 0:
            reasons.append(f"spam indicators ({negative_score})")

        return {
            "is_relevant": is_relevant,
            "confidence_score": confidence_score,
            "reason": "; ".join(reasons) if reasons else "No strong indicators",
            "quality_indicators": self._get_quality_indicators(combined_text),
            "course_signal_score": course_signal,
            "resource_signal_score": resource_signal,
        }

    def _course_signal_score(self, course_code: str, course_name: str, text: str) -> int:
        """Score exact course code, exact course title, and meaningful title terms."""
        score = 0
        compact_text = re.sub(r"[^a-z0-9]", "", text)
        compact_code = re.sub(r"[^a-z0-9]", "", (course_code or "").lower())
        if compact_code and compact_code in compact_text:
            score += 40

        normalized_course_name = " ".join(
            re.findall(r"[a-z0-9]+", (course_name or "").lower())
        )
        if normalized_course_name and normalized_course_name in text:
            score += 30

        term_hits = 0
        for term in self._meaningful_course_terms(course_code, course_name):
            if re.search(rf"\b{re.escape(term)}\b", text):
                term_hits += 1
        score += min(term_hits * 8, 24)

        return min(score, 70)

    def _meaningful_course_terms(self, course_code: str, course_name: str) -> List[str]:
        terms = []
        for term in re.findall(r"[a-z0-9]+", f"{course_code} {course_name}".lower()):
            if term in self.STOPWORDS:
                continue
            if len(term) < 3 and not any(char.isdigit() for char in term):
                continue
            terms.append(term)
        return list(dict.fromkeys(terms))

    def _count_phrase_matches(self, text: str, keywords: List[str]) -> int:
        """Count phrase/word matches without short substring false positives."""
        count = 0
        for keyword in keywords:
            pattern = rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])"
            if re.search(pattern, text):
                count += 1
        return count

    def _resource_signal_score(self, text: str, url: str) -> int:
        score = 0
        if any(ext in url for ext in [".pdf", ".doc", ".docx", ".ppt", ".pptx"]):
            score += 18
        if any(word in text for word in ["download", "material", "notes", "paper"]):
            score += 10
        return min(score, 25)

    def _check_academic_domain(self, url: str) -> int:
        """Check if URL is from academic domain."""
        for domain in self.ACADEMIC_DOMAINS:
            if domain in url:
                return 15
        return 0

    def _get_quality_indicators(self, text: str) -> List[str]:
        """Extract quality indicators from text."""
        indicators = []
        if "pdf" in text or ".pdf" in text:
            indicators.append("PDF available")
        if "download" in text:
            indicators.append("Downloadable")
        if any(kw in text for kw in ["notes", "lecture", "slides"]):
            indicators.append("Lecture content")
        if any(kw in text for kw in ["question", "exam", "paper", "pyq"]):
            indicators.append("Exam material")
        if any(kw in text for kw in ["syllabus", "curriculum", "course outline"]):
            indicators.append("Course structure")
        return indicators
