"""
Base Scraper Class - Abstract base for all news scrapers
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NewsArticle(BaseModel):
    """Model for a news article"""
    title: str
    content: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    scraped_at: datetime = None
    currency_pairs: List[str] = []
    sentiment: Optional[str] = None  # bullish, bearish, neutral
    importance: str = "medium"  # low, medium, high
    
    def __init__(self, **data):
        if 'scraped_at' not in data or data['scraped_at'] is None:
            data['scraped_at'] = datetime.now()
        super().__init__(**data)


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.timeout = 30.0
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, "lxml")
    
    @abstractmethod
    async def scrape_news(self, currency_pairs: List[str] = None) -> List[NewsArticle]:
        """
        Scrape news articles from the source
        Must be implemented by each scraper
        """
        pass
    
    @abstractmethod
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from article page
        Must be implemented by each scraper
        """
        pass
    
    def detect_currency_pairs(self, text: str, available_pairs: List[str]) -> List[str]:
        """Detect mentioned currency pairs in text"""
        from config.settings import PAIR_CONFIGS
        
        detected = []
        text_upper = text.upper()
        text_lower = text.lower()
        
        for pair in available_pairs:
            # Direct pair mention
            if pair in text_upper:
                detected.append(pair)
                continue
            
            # Check keywords
            if pair in PAIR_CONFIGS:
                keywords = PAIR_CONFIGS[pair].get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        detected.append(pair)
                        break
        
        return list(set(detected))
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\'\"()%$€£¥]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def truncate_text(self, text: str, max_length: int = 5000) -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
