"""
Configuration settings for the Academic Resource Discovery System.
NO API KEYS REQUIRED - uses free services only.
"""

from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Academic Resource Discovery System")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/academic_resources"
    )
    
    # Crawler Settings
    crawler_max_results_per_query: int = Field(default=25)
    crawler_max_urls_per_run: int = Field(default=300)
    crawler_timeout_seconds: int = Field(default=30)
    crawler_verify_ssl: bool = Field(default=False)
    crawler_delay_between_requests: float = Field(default=2.0)
    crawler_max_content_chars: int = Field(default=12000)
    crawler_pdf_max_pages: int = Field(default=8)
    crawler_accept_non_pdf_resources: bool = Field(default=True)
    crawler_enforce_requested_college: bool = Field(default=False)
    crawler_enable_seed_discovery: bool = Field(default=True)
    crawler_seed_max_pages: int = Field(default=150)
    crawler_seed_max_depth: int = Field(default=5)
    crawler_seed_allow_external_domains: bool = Field(default=True)
    crawler_enable_result_site_discovery: bool = Field(default=True)
    crawler_result_site_max_domains: int = Field(default=8)
    crawler_result_site_max_pages_per_domain: int = Field(default=35)
    crawler_result_site_max_depth: int = Field(default=2)
    crawler_sitemap_max_urls: int = Field(default=120)
    
    # Scoring Thresholds
    relevance_threshold: float = Field(default=0.9)
    final_score_threshold: int = Field(default=90)
    high_confidence_threshold: int = Field(default=90)
    
    # Trusted Domains
    trusted_domains: str = Field(
        default=".edu,.ac.in,.gov,uktech.ac.in,uou.ac.in,nptel.ac.in"
    )
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # Streamlit
    streamlit_port: int = Field(default=8501)
    
    @property
    def trusted_domains_list(self) -> List[str]:
        """Get trusted domains as a list."""
        return [d.strip() for d in self.trusted_domains.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
