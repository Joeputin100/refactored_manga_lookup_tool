#!/usr/bin/env python3
"""
Enhanced Cover Image Fetcher - Fixed Version

Uses working Google Books API and implements simpler web search fallback
"""

import time
import requests
import json
import re
from typing import Optional, Dict


class GoogleBooksCoverFetcher:
    """Fetch cover images from Google Books API"""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        self.requests_today = 0
        self.daily_limit = 900

    def _rate_limit(self):
        """Rate limiting for Google Books API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def _check_daily_limit(self):
        """Check if we've exceeded daily limit"""
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


class SimpleWebSearchFetcher:
    """Simple web search fallback using existing APIs"""

    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests

    def _rate_limit(self):
        """Rate limiting for web search"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Simple web search fallback - uses existing APIs for metadata"""
        self._rate_limit()

        try:
            from manga_lookup import VertexAIAPI, DeepSeekAPI

            print(f"🔍 Web search fallback for: {series_name} Vol {volume}")

            # Try to get comprehensive series info which might include cover URLs
            vertex_api = VertexAIAPI()
            series_info = vertex_api.get_comprehensive_series_info(series_name)

            if series_info and 'cover_image_url' in series_info and series_info['cover_image_url']:
                cover_url = series_info['cover_image_url']
                if self._validate_cover_url(cover_url):
                    print(f"✅ Web search found cover for: {series_name} Vol {volume}")
                    return cover_url

            # If VertexAI doesn't work, try DeepSeek
            deepseek_api = DeepSeekAPI()
            book_info = deepseek_api.get_book_info(series_name, volume)

            if book_info and 'cover_image_url' in book_info and book_info['cover_image_url']:
                cover_url = book_info['cover_image_url']
                if self._validate_cover_url(cover_url):
                    print(f"✅ Web search found cover for: {series_name} Vol {volume}")
                    return cover_url

            print(f"❌ Web search no cover found for: {series_name} Vol {volume}")
            return None

        except Exception as e:
            print(f"❌ Web search error for {series_name}: {e}")
            return None

    def _validate_cover_url(self, url: str) -> bool:
        """Validate that cover URL is accessible"""
        try:
            # Quick HEAD request to check accessibility
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False


class EnhancedCoverFetcherFixed:
    """Enhanced cover fetcher with working implementation"""

    def __init__(self):
        self.fetchers = [
            GoogleBooksCoverFetcher(),      # Primary: High quality English covers
            SimpleWebSearchFetcher()        # Fallback: Web search using existing APIs
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


def test_enhanced_fetcher_fixed():
    """Test the fixed enhanced cover fetcher"""
    print("🧪 Testing Fixed Enhanced Cover Fetcher...")

    fetcher = EnhancedCoverFetcherFixed()

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
    test_enhanced_fetcher_fixed()