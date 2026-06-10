"""
Deduplication Agent - Prevents duplicate entries.
"""

import hashlib
from typing import Dict, Any, Optional, Set
from loguru import logger

from utils.helpers import hash_url, hash_content


class DeduplicationAgent:
    """Agent for detecting and preventing duplicate resources."""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_content_hashes: Set[str] = set()
    
    def check_duplicate(
        self,
        url: str,
        content: str = "",
        check_db: bool = True,
        db_session = None,
    ) -> Dict[str, Any]:
        """Check if resource is a duplicate."""
        url_hash = hash_url(url)
        content_hash = hash_content(content) if content else ""
        
        result = {
            "is_duplicate": False,
            "url_hash": url_hash,
            "content_hash": content_hash,
            "duplicate_type": None,
            "duplicate_of_id": None,
        }
        
        # Check in-memory cache first
        if url_hash in self.seen_urls:
            result["is_duplicate"] = True
            result["duplicate_type"] = "url_memory"
            logger.debug(f"Duplicate URL found in memory: {url[:50]}")
            return result
        
        if content_hash and content_hash in self.seen_content_hashes:
            result["is_duplicate"] = True
            result["duplicate_type"] = "content_memory"
            logger.debug(f"Duplicate content found in memory")
            return result
        
        # Check database if session provided
        if check_db and db_session:
            from db.crud import check_duplicate_sync
            existing = check_duplicate_sync(db_session, url_hash, content_hash)
            if existing:
                result["is_duplicate"] = True
                result["duplicate_type"] = "database"
                result["duplicate_of_id"] = existing.id
                logger.debug(f"Duplicate found in database: {existing.id}")
                return result
        
        # Add to cache
        self.seen_urls.add(url_hash)
        if content_hash:
            self.seen_content_hashes.add(content_hash)
        
        return result
    
    def reset_cache(self):
        """Clear in-memory cache."""
        self.seen_urls.clear()
        self.seen_content_hashes.clear()
