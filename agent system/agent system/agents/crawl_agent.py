"""
Crawl Agent - Extracts content from web pages and documents.
"""

from io import BytesIO
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from loguru import logger
import urllib3

try:
    import trafilatura
except Exception:  # pragma: no cover - optional at runtime
    trafilatura = None

from config.settings import settings
from utils.helpers import extract_file_type, clean_text

if not settings.crawler_verify_ssl:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CrawlAgent:
    """Agent for crawling and extracting page/document content."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
    }

    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.crawler_timeout_seconds

    def crawl(self, url: str) -> Dict[str, Any]:
        """Crawl a URL and extract content."""
        result = {
            "url": url,
            "resolved_url": url,
            "success": False,
            "title": "",
            "content": "",
            "file_type": "",
            "content_type": "",
            "content_length": 0,
            "error": None,
        }

        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.timeout,
                allow_redirects=True,
                verify=settings.crawler_verify_ssl,
            )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            resolved_url = response.url or url
            result["resolved_url"] = resolved_url
            result["url"] = resolved_url
            result["content_type"] = content_type
            result["file_type"] = extract_file_type(resolved_url, content_type)
            result["content_length"] = len(response.content or b"")

            if result["file_type"] == "pdf":
                title = self._title_from_url(resolved_url)
                pdf_text = self._extract_pdf_text(response.content)
                result["success"] = True
                result["title"] = title
                result["content"] = clean_text(
                    pdf_text or f"PDF document {title}",
                    max_length=settings.crawler_max_content_chars,
                )
                return result

            if result["file_type"] in {"doc", "ppt"}:
                title = self._title_from_url(resolved_url)
                result["success"] = True
                result["title"] = title
                result["content"] = clean_text(
                    f"{result['file_type'].upper()} document {title}",
                    max_length=settings.crawler_max_content_chars,
                )
                return result

            title, content = self._extract_html(response, resolved_url)
            result["title"] = title
            result["content"] = clean_text(
                content,
                max_length=settings.crawler_max_content_chars,
            )
            result["success"] = True

            logger.debug(
                f"Crawled: {resolved_url[:60]}... ({len(result['content'])} chars)"
            )

        except requests.Timeout:
            result["error"] = "Timeout"
            logger.warning(f"Timeout crawling: {url}")
        except requests.RequestException as e:
            result["error"] = str(e)
            logger.warning(f"Error crawling {url}: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Unexpected error crawling {url}: {e}")

        return result

    def crawl_multiple(self, urls: list) -> list:
        """Crawl multiple URLs."""
        return [self.crawl(url) for url in urls]

    def _extract_html(self, response: requests.Response, url: str) -> tuple[str, str]:
        """Extract main text from HTML with a BeautifulSoup fallback."""
        html = response.text
        soup = BeautifulSoup(response.content, "lxml")
        title_tag = soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag else self._title_from_url(url)

        extracted = ""
        if trafilatura is not None:
            try:
                extracted = trafilatura.extract(
                    html,
                    url=url,
                    include_comments=False,
                    include_tables=True,
                    favor_precision=True,
                ) or ""
            except Exception as e:
                logger.debug(f"Trafilatura extraction failed for {url}: {e}")

        if extracted:
            return title, extracted

        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()
        return title, soup.get_text(separator=" ", strip=True)

    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from the first pages of a PDF when a parser is installed."""
        if not content:
            return ""

        for module_name in ("pypdf", "PyPDF2"):
            try:
                module = __import__(module_name)
                reader = module.PdfReader(BytesIO(content))
                texts = []
                for page in reader.pages[: settings.crawler_pdf_max_pages]:
                    try:
                        texts.append(page.extract_text() or "")
                    except Exception:
                        continue
                return "\n".join(text for text in texts if text).strip()
            except Exception:
                continue

        return ""

    def _title_from_url(self, url: str) -> str:
        filename = url.rstrip("/").split("/")[-1] or url
        filename = filename.split("?")[0]
        return filename.replace("%20", " ").replace("_", " ")[:200]
