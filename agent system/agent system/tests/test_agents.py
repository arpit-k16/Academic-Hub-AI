"""
Tests for agent components (no API keys needed).
"""

import pytest
from agents.extraction_agent import ExtractionAgent
from agents.classification_agent import ClassificationAgent
from agents.college_agent import CollegeMatchingAgent
from agents.dedup_agent import DeduplicationAgent
from agents.scoring_agent import ScoringAgent
from agents.relevance_agent import RelevanceAgent
from agents.search_agent import SearchAgent
from utils.helpers import hash_url, hash_content, extract_domain, normalize_url


class TestExtractionAgent:
    def test_extract_valid_content(self):
        agent = ExtractionAgent()
        crawl_result = {
            "success": True,
            "title": "CS101 Lecture Notes - Download PDF",
            "content": "These are lecture notes for Computer Science 101. Chapter 1 covers basics.",
            "url": "https://example.com/notes.pdf",
            "file_type": "pdf",
        }
        result = agent.extract(crawl_result)
        assert result["valid"] is True
        assert "CS101 Lecture Notes" in result["title"]
        assert "notes" in result["detected_keywords"]
    
    def test_extract_failed_crawl(self):
        agent = ExtractionAgent()
        crawl_result = {"success": False, "error": "Timeout"}
        result = agent.extract(crawl_result)
        assert result["valid"] is False


class TestRelevanceAgent:
    def test_relevant_content(self):
        agent = RelevanceAgent()
        result = agent.evaluate(
            course_code="CS101",
            course_name="Introduction to Programming",
            title="CS101 Lecture Notes PDF",
            content_snippet="Introduction to Programming lecture notes chapter 1",
            url="https://university.edu/cs101/notes.pdf"
        )
        assert result["is_relevant"] is True
        assert result["confidence_score"] >= 90
    
    def test_irrelevant_spam_content(self):
        agent = RelevanceAgent()
        result = agent.evaluate(
            course_code="CS101",
            course_name="Introduction to Programming",
            title="Buy Now - Great Discount Sale",
            content_snippet="Limited offer! Buy now with free shipping. Casino bonus.",
            url="https://spam-site.com/buy"
        )
        assert result["is_relevant"] is False

    def test_rejects_weak_partial_course_match(self):
        agent = RelevanceAgent()
        result = agent.evaluate(
            course_code="CS101",
            course_name="Data Structures",
            title="Business structures lecture notes",
            content_snippet="A generic management handout with no computer science course code.",
            url="https://example.com/structures-notes.pdf"
        )
        assert result["is_relevant"] is False


class TestClassificationAgent:
    def test_classify_notes(self):
        agent = ClassificationAgent()
        result = agent.classify(
            "Data Structures Lecture Notes",
            "Chapter 1: Introduction to Arrays and Linked Lists",
            ["notes", "lecture"]
        )
        assert result["resource_type"] == "notes"
        assert result["confidence"] > 50
    
    def test_classify_question_paper(self):
        agent = ClassificationAgent()
        result = agent.classify(
            "CS101 Previous Year Question Paper 2023",
            "Exam paper with solutions",
            ["question paper", "exam"]
        )
        assert result["resource_type"] == "question_paper"
    
    def test_classify_syllabus(self):
        agent = ClassificationAgent()
        result = agent.classify(
            "Course Syllabus CS101",
            "Course outline and curriculum for the semester",
            ["syllabus", "curriculum"]
        )
        assert result["resource_type"] == "syllabus"


class TestCollegeMatchingAgent:
    def test_match_by_domain(self):
        agent = CollegeMatchingAgent()
        result = agent.match("https://uktech.ac.in/notes/cs101.pdf")
        assert result["college_name"] == "Uttarakhand Technical University"
        assert result["confidence"] >= 90
    
    def test_no_match(self):
        agent = CollegeMatchingAgent()
        result = agent.match("https://randomsite.com/notes.pdf")
        assert result["college_name"] is None


class TestDeduplicationAgent:
    def test_detect_duplicate_url(self):
        agent = DeduplicationAgent()
        # First check
        result1 = agent.check_duplicate("https://example.com/notes.pdf", "content")
        assert result1["is_duplicate"] is False
        # Second check (same URL)
        result2 = agent.check_duplicate("https://example.com/notes.pdf", "different content")
        assert result2["is_duplicate"] is True
    
    def test_reset_cache(self):
        agent = DeduplicationAgent()
        agent.check_duplicate("https://example.com/test.pdf")
        agent.reset_cache()
        result = agent.check_duplicate("https://example.com/test.pdf")
        assert result["is_duplicate"] is False


class TestScoringAgent:
    def test_score_calculation(self):
        agent = ScoringAgent(threshold=90)
        result = agent.score(
            relevance_score=98,
            type_confidence=95,
            college_confidence=90,
            domain="uktech.ac.in"
        )
        assert result["final_score"] >= 90
        assert result["passes_threshold"] is True
    
    def test_low_score(self):
        agent = ScoringAgent(threshold=90)
        result = agent.score(
            relevance_score=30,
            type_confidence=40,
            college_confidence=20,
            domain="unknown.com"
        )
        assert result["final_score"] < 90

    def test_no_college_search_does_not_penalize_missing_college_match(self):
        agent = ScoringAgent(threshold=90)
        result = agent.score(
            relevance_score=95,
            type_confidence=85,
            college_confidence=0,
            domain="nptel.ac.in",
            college_required=False,
        )
        assert result["passes_threshold"] is True


class TestHelpers:
    def test_hash_url(self):
        hash1 = hash_url("https://example.com/test")
        hash2 = hash_url("https://example.com/test/")
        assert hash1 == hash2  # Normalized
    
    def test_extract_domain(self):
        domain = extract_domain("https://www.example.com/path/to/file")
        assert domain == "www.example.com"

    def test_normalize_url_removes_tracking_params(self):
        url = "https://example.com/course/notes.pdf?utm_source=x&id=10#section"
        assert normalize_url(url) == "https://example.com/course/notes.pdf?id=10"
        assert hash_url(url) == hash_url("https://example.com/course/notes.pdf?id=10")


class TestSearchAgent:
    def test_generate_queries_broad_and_college_targeted(self):
        agent = SearchAgent()
        queries = agent.generate_queries(
            "CS101",
            "Data Structures",
            "Kalinga Institute of Industrial Technology",
        )
        normalized = [" ".join(query.split()).lower() for query in queries]

        assert any("site:kiit.ac.in" in query for query in normalized)
        assert any("academic resources" in query for query in normalized)
        assert any("question paper" in query for query in normalized)
        assert len(normalized) == len(set(normalized))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
