#!/usr/bin/env python3
"""
Enhanced Cover Image Fetcher

Strategy:
1. Google Books API (primary) - high quality English covers
2. Gemini 2.5 Flash Lite web search (secondary) - intelligent image search
3. DeepSeek web search (tertiary) - fallback image search

Rate Limits (conservative estimates at 90% of known limits):
- Google Books: 1000 requests/day (900/day)
- Gemini: 1500 requests/minute (1350/minute)
- DeepSeek: 1000 requests/minute (900/minute)
"""

import time
import requests
import json
from typing import Optional, Dict

from wikipedia_cover_fetcher import WikipediaCoverFetcher


class GoogleBooksCoverFetcher:
    """Fetch cover images from Google Books API"""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests (90% of 1000/day)
        self.requests_today = 0
        self.daily_limit = 900  # 90% of 1000/day

    def _rate_limit(self):
        """Rate limiting for Google Books API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def _check_daily_limit(self):
        """Check if we've exceeded daily limit"""
        # Simple daily counter (resets on script restart)
        if self.requests_today >= self.daily_limit:
            print(f"⚠️ Google Books daily limit reached: {self.requests_today}/{self.daily_limit}")
            return False
        return True

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Fetch cover image URL from Google Books"""
        if not self._check_daily_limit():
            return None

        self._rate_limit()

        try:
            # Search for manga volume
            search_query = f'"{series_name}" "volume {volume}" manga'
            params = {
                'q': search_query,
                'maxResults': 5,
                'printType': 'books'
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            self.requests_today += 1

            data = response.json()

            if data.get('totalItems', 0) > 0:
                for item in data['items']:
                    volume_info = item.get('volumeInfo', {})

                    # Check if this looks like the right volume
                    title = volume_info.get('title', '').lower()
                    if f'volume {volume}' in title or f'vol. {volume}' in title:
                        image_links = volume_info.get('imageLinks', {})

                        # Try different image sizes in order of preference
                        for size in ['extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail']:
                            if size in image_links:
                                cover_url = image_links[size]
                                print(f"✅ Google Books found cover for: {series_name} Vol {volume}")
                                return cover_url

            print(f"❌ Google Books no cover found for: {series_name} Vol {volume}")
            return None

        except Exception as e:
            print(f"❌ Google Books API error for {series_name}: {e}")
            return None


class GeminiWebSearchFetcher:
    """Use Gemini 2.5 Flash Lite for intelligent web image search"""

    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 0.044  # ~22 requests/second (90% of 1350/minute)

    def _rate_limit(self):
        """Rate limiting for Gemini API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Use Gemini to search for cover images"""
        self._rate_limit()

        try:
            # This would use the VertexAI API to perform web search
            # For now, we'll implement a placeholder that uses the existing VertexAIAPI
            # In practice, this would call Gemini with a prompt to search for cover images

            prompt = f"""Find a high-quality cover image for the manga "{series_name}" volume {volume}.
            Search for official English edition covers. Return only the direct image URL if found."""

            # This is a placeholder - actual implementation would use VertexAI web search
            print(f"🔍 Gemini web search for: {series_name} Vol {volume}")

            # For now, return None to indicate we need to implement this properly
            return None

        except Exception as e:
            print(f"❌ Gemini web search error for {series_name}: {e}")
            return None


class DeepSeekWebSearchFetcher:
    """Use DeepSeek for web image search fallback"""

    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 0.067  # ~15 requests/second (90% of 900/minute)

    def _rate_limit(self):
        """Rate limiting for DeepSeek API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Use DeepSeek to search for cover images"""
        self._rate_limit()

        try:
            # This would use the DeepSeek API to perform web search
            # For now, we'll implement a placeholder

            prompt = f"""Search for the cover image of manga "{series_name}" volume {volume}.
            Look for high-quality official covers. Return only the direct image URL."""

            print(f"🔍 DeepSeek web search for: {series_name} Vol {volume}")

            # For now, return None to indicate we need to implement this properly
            return None

        except Exception as e:
            print(f"❌ DeepSeek web search error for {series_name}: {e}")
            return None


class EnhancedCoverFetcher:
    """Enhanced cover fetcher with multi-source fallback strategy"""

    def __init__(self):
        self.fetchers = [
            GoogleBooksCoverFetcher(),      # Primary: High quality English covers
            WikipediaCoverFetcher(),        # Secondary: Wikipedia cover images
            GeminiWebSearchFetcher(),       # Tertiary: Intelligent image search
            DeepSeekWebSearchFetcher()      # Quaternary: Fallback image search
        ]

        self.stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'by_source': {}
        }

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Fetch cover using multi-source fallback strategy"""
        self.stats['total_attempts'] += 1

        for i, fetcher in enumerate(self.fetchers):
            source_name = fetcher.__class__.__name__
            print(f"🔍 Trying {source_name} for: {series_name} Vol {volume}")

            try:
                cover_url = fetcher.fetch_cover(series_name, volume)

                if cover_url and self._validate_cover_url(cover_url):
                    # Track success
                    if source_name not in self.stats['by_source']:
                        self.stats['by_source'][source_name] = 0
                    self.stats['by_source'][source_name] += 1
                    self.stats['successful'] += 1

                    print(f"✅ {source_name} SUCCESS for: {series_name} Vol {volume}")
                    return cover_url

            except Exception as e:
                print(f"❌ {source_name} failed for {series_name}: {e}")
                continue

        self.stats['failed'] += 1
        print(f"❌ ALL SOURCES FAILED for: {series_name} Vol {volume}")
        return None

    def _validate_cover_url(self, url: str) -> bool:
        """Validate that cover URL is accessible and reasonable"""
        try:
            # For Wikipedia URLs, we know they're valid from the API
            if 'wikipedia.org' in url or 'wikimedia.org' in url:
                return True

            # Quick HEAD request to check accessibility
            response = requests.head(url, timeout=5, allow_redirects=True)

            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'image' in content_type:
                    return True

            return False

        except Exception:
            return False

    def get_stats(self) -> Dict:
        """Get current fetching statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print current statistics"""
        print("\n📊 Cover Fetching Statistics:")
        print(f"   Total Attempts: {self.stats['total_attempts']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")

        if self.stats['by_source']:
            print("   Success by Source:")
            for source, count in self.stats['by_source'].items():
                print(f"     {source}: {count}")


def test_enhanced_fetcher():
    """Test the enhanced cover fetcher"""
    print("🧪 Testing Enhanced Cover Fetcher...")

    fetcher = EnhancedCoverFetcher()

    # Test with popular series
    test_series = [
        ("One Piece", 1),
        ("Naruto", 1),
        ("Attack on Titan", 1)
    ]

    for series_name, volume in test_series:
        print(f"\n🔍 Testing: {series_name} Vol {volume}")
        cover_url = fetcher.fetch_cover(series_name, volume)

        if cover_url:
            print(f"✅ Found cover: {cover_url}")
        else:
            print(f"❌ No cover found")

    fetcher.print_stats()


if __name__ == "__main__":
    test_enhanced_fetcher()