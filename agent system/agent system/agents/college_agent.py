"""
College Matching Agent - Matches resources to colleges.
"""

import re
from typing import Dict, Any, Optional, List
from loguru import logger


class CollegeMatchingAgent:
    """Agent for matching resources to colleges based on domain and content."""
    
    # Known college domain patterns
    KNOWN_COLLEGES = {
        "bennett.edu.in": {"name": "Bennett University", "short": "BU"},
        "uktech.ac.in": {"name": "Uttarakhand Technical University", "short": "UTU"},
        "uou.ac.in": {"name": "Uttarakhand Open University", "short": "UOU"},
        "hnbgu.ac.in": {"name": "Hemwati Nandan Bahuguna Garhwal University", "short": "HNBGU"},
        "kiit.ac.in": {"name": "Kalinga Institute of Industrial Technology", "short": "KIIT"},
        "du.ac.in": {"name": "Delhi University", "short": "DU"},
        "iitd.ac.in": {"name": "IIT Delhi", "short": "IITD"},
        "iitb.ac.in": {"name": "IIT Bombay", "short": "IITB"},
        "iitk.ac.in": {"name": "IIT Kanpur", "short": "IITK"},
        "iitkgp.ac.in": {"name": "IIT Kharagpur", "short": "IITKGP"},
        "iitm.ac.in": {"name": "IIT Madras", "short": "IITM"},
        "iitr.ac.in": {"name": "IIT Roorkee", "short": "IITR"},
        "iisc.ac.in": {"name": "Indian Institute of Science", "short": "IISC"},
        "vit.ac.in": {"name": "Vellore Institute of Technology", "short": "VIT"},
        "annauniv.edu": {"name": "Anna University", "short": "AU"},
        "bits-pilani.ac.in": {"name": "BITS Pilani", "short": "BITS"},
        "nptel.ac.in": {"name": "NPTEL", "short": "NPTEL"},
        "swayam.gov.in": {"name": "SWAYAM", "short": "SWAYAM"},
    }
    
    def __init__(self, additional_colleges: Dict[str, Dict] = None):
        self.colleges = self.KNOWN_COLLEGES.copy()
        if additional_colleges:
            self.colleges.update(additional_colleges)
    
    def match(
        self,
        url: str,
        content: str = "",
        title: str = "",
    ) -> Dict[str, Any]:
        """Match resource to a college."""
        # Extract domain from URL
        domain = self._extract_domain(url)
        
        # Try domain matching first
        domain_match = self._match_by_domain(domain)
        if domain_match["confidence"] >= 90:
            return domain_match
        
        # Try content matching
        content_match = self._match_by_content(f"{title} {content}")
        if content_match["confidence"] > domain_match["confidence"]:
            return content_match
        
        return domain_match if domain_match["college_name"] else {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }

    def get_expected_domain(self, college_name: str) -> Optional[str]:
        """Resolve expected domain for the requested college."""
        if not college_name:
            return None
        query = college_name.lower()
        for domain, info in self.colleges.items():
            if info["name"].lower() in query or info["short"].lower() in query:
                return domain
        return None

    def matches_target_college(self, match: Dict[str, Any], target_college: str) -> bool:
        """Return True only when match corresponds to the requested college."""
        if not target_college:
            return True
        if not match.get("college_name"):
            return False
        target = target_college.lower()
        matched_name = match.get("college_name", "").lower()
        matched_short = match.get("college_short", "").lower()
        return (
            target in matched_name
            or matched_name in target
            or (matched_short and matched_short in target)
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _match_by_domain(self, domain: str) -> Dict[str, Any]:
        """Match college by domain."""
        for college_domain, info in self.colleges.items():
            if college_domain in domain:
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 95,
                    "match_source": "domain",
                }
        
        # Check for generic .ac.in or .edu
        if ".ac.in" in domain or ".edu" in domain:
            return {
                "college_name": None,
                "college_short": None,
                "confidence": 30,
                "match_source": "generic_academic",
            }
        
        return {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }
    
    def _match_by_content(self, content: str) -> Dict[str, Any]:
        """Match college by content mentions."""
        content_lower = content.lower()
        
        for domain, info in self.colleges.items():
            # Check for full name
            if info["name"].lower() in content_lower:
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 85,
                    "match_source": "content_fullname",
                }
            # Check for short name
            short = info["short"].lower()
            if short and re.search(rf"(?<![a-z0-9]){re.escape(short)}(?![a-z0-9])", content_lower):
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 70,
                    "match_source": "content_shortname",
                }
        
        return {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }
