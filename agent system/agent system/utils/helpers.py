"""
Utility helper functions.
"""

import re
import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from typing import Optional


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content."""
    if not content:
        return ""
    normalized = re.sub(r"\s+", " ", content.lower().strip())
    return hashlib.sha256(normalized.encode()).hexdigest()


def hash_url(url: str) -> str:
    """Generate SHA-256 hash of URL."""
    if not url:
        return ""
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication while preserving meaningful query params."""
    parsed = urlparse(url.lower().strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return url.lower().strip().rstrip("/")

    tracking_prefixes = ("utm_",)
    tracking_names = {"fbclid", "gclid", "mc_cid", "mc_eid", "session", "sid", "spm"}
    filtered_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key in tracking_names or key.startswith(tracking_prefixes):
            continue
        filtered_query.append((key, value))

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            "",
            urlencode(filtered_query, doseq=True),
            "",
        )
    )


def clean_text(text: str, max_length: int = 1000) -> str:
    """Clean and truncate text content."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\w\s.,!?;:\-()\[\]]", "", text)
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.strip()


def extract_file_type(url: str, content_type: Optional[str] = None) -> str:
    """Extract file type from URL or content type."""
    # Check content type first
    if content_type:
        if "pdf" in content_type.lower():
            return "pdf"
        elif "html" in content_type.lower():
            return "html"
        elif (
            "word" in content_type.lower()
            or "msword" in content_type.lower()
            or "officedocument.wordprocessingml" in content_type.lower()
        ):
            return "doc"
        elif (
            "powerpoint" in content_type.lower()
            or "officedocument.presentationml" in content_type.lower()
        ):
            return "ppt"
    
    # Check URL extension
    url_lower = url.lower()
    if url_lower.endswith(".pdf"):
        return "pdf"
    elif url_lower.endswith(".doc") or url_lower.endswith(".docx"):
        return "doc"
    elif url_lower.endswith(".ppt") or url_lower.endswith(".pptx"):
        return "ppt"
    elif url_lower.endswith(".html") or url_lower.endswith(".htm"):
        return "html"
    else:
        return "html"  # Default to HTML


def is_trusted_domain(domain: str, trusted_list: list) -> bool:
    """Check if domain is in trusted list."""
    domain = domain.lower()
    for trusted in trusted_list:
        if trusted.startswith("."):
            if domain.endswith(trusted):
                return True
        else:
            if domain == trusted or domain.endswith("." + trusted):
                return True
    return False


def calculate_domain_trust(domain: str, trusted_list: list) -> float:
    """Calculate trust score for domain."""
    if is_trusted_domain(domain, trusted_list):
        return 1.5  # Boost for trusted domains
    elif ".edu" in domain or ".ac." in domain:
        return 1.3
    elif ".gov" in domain:
        return 1.2
    elif ".org" in domain:
        return 1.0
    else:
        return 0.8  # Slight penalty for unknown domains
