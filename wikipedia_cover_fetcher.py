#!/usr/bin/env python3
"""
Wikipedia Cover Image Fetcher

Fetches cover images from Wikipedia for manga series.
Uses Wikipedia API to search for cover images and extract direct URLs.
"""

import time
import requests
import re
from typing import Optional


class WikipediaCoverFetcher:
    """Fetch cover images from Wikipedia"""

    def __init__(self):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        self.requests_today = 0
        self.daily_limit = 500  # Conservative limit

    def _rate_limit(self):
        """Rate limiting for Wikipedia API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def _check_daily_limit(self):
        """Check if we've exceeded daily limit"""
        if self.requests_today >= self.daily_limit:
            print(f"⚠️ Wikipedia daily limit reached: {self.requests_today}/{self.daily_limit}")
            return False
        return True

    def _search_wikipedia(self, query: str) -> Optional[dict]:
        """Search Wikipedia for pages related to the query"""
        if not self._check_daily_limit():
            return None

        self._rate_limit()

        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 5
            }

            headers = {
                'User-Agent': 'MangaLookupTool/1.0 (https://github.com/yourusername/manga-lookup-tool; your@email.com)'
            }

            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            self.requests_today += 1
            return response.json()

        except Exception as e:
            print(f"❌ Wikipedia search error for {query}: {e}")
            return None

    def _get_page_images(self, page_title: str) -> Optional[dict]:
        """Get images from a Wikipedia page"""
        if not self._check_daily_limit():
            return None

        self._rate_limit()

        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'images',
                'imlimit': 50
            }

            headers = {
                'User-Agent': 'MangaLookupTool/1.0 (https://github.com/yourusername/manga-lookup-tool; your@email.com)'
            }

            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            self.requests_today += 1
            return response.json()

        except Exception as e:
            print(f"❌ Wikipedia images error for {page_title}: {e}")
            return None

    def _get_image_info(self, image_title: str) -> Optional[str]:
        """Get direct URL for a Wikipedia image"""
        if not self._check_daily_limit():
            return None

        self._rate_limit()

        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': image_title,
                'prop': 'imageinfo',
                'iiprop': 'url'
            }

            headers = {
                'User-Agent': 'MangaLookupTool/1.0 (https://github.com/yourusername/manga-lookup-tool; your@email.com)'
            }

            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            self.requests_today += 1
            data = response.json()

            # Extract image URL
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                imageinfo = page_data.get('imageinfo', [])
                if imageinfo:
                    return imageinfo[0].get('url')

            return None

        except Exception as e:
            print(f"❌ Wikipedia image info error for {image_title}: {e}")
            return None

    def _is_cover_image(self, image_title: str, series_name: str, volume: int) -> bool:
        """Check if an image is likely a cover image"""
        image_lower = image_title.lower()
        series_lower = series_name.lower()

        # Common cover image patterns
        cover_patterns = [
            f'{series_lower}',
            f'volume {volume}',
            f'vol. {volume}',
            f'vol {volume}',
            'cover',
            'front cover',
            'jacket',
            'dust jacket'
        ]

        # Check for volume-specific patterns first
        volume_patterns = [
            f'{series_lower}.*{volume}',
            f'volume.*{volume}.*{series_lower}',
            f'{volume}.*{series_lower}'
        ]

        # Check volume-specific patterns
        for pattern in volume_patterns:
            if re.search(pattern, image_lower):
                return True

        # Check general cover patterns
        for pattern in cover_patterns:
            if pattern in image_lower:
                return True

        return False

    def fetch_cover(self, series_name: str, volume: int = 1) -> Optional[str]:
        """Fetch cover image URL from Wikipedia"""
        print(f"🔍 Wikipedia search for: {series_name} Vol {volume}")

        # Search for the manga series
        search_query = f'"{series_name}" manga volume {volume}'
        search_results = self._search_wikipedia(search_query)

        if not search_results:
            print(f"❌ Wikipedia no search results for: {series_name} Vol {volume}")
            return None

        # Get search results
        pages = search_results.get('query', {}).get('search', [])
        if not pages:
            print(f"❌ Wikipedia no pages found for: {series_name} Vol {volume}")
            return None

        # Try each search result page
        for page in pages:
            page_title = page.get('title', '')
            print(f"  📖 Checking Wikipedia page: {page_title}")

            # Get images from this page
            images_data = self._get_page_images(page_title)
            if not images_data:
                continue

            # Extract images
            pages_data = images_data.get('query', {}).get('pages', {})
            for page_id, page_data in pages_data.items():
                images = page_data.get('images', [])
                for image in images:
                    image_title = image.get('title', '')

                    # Check if this is a cover image
                    if self._is_cover_image(image_title, series_name, volume):
                        print(f"  🖼️ Potential cover found: {image_title}")

                        # Get direct image URL
                        image_url = self._get_image_info(image_title)
                        if image_url:
                            print(f"✅ Wikipedia found cover for: {series_name} Vol {volume}")
                            return image_url

        print(f"❌ Wikipedia no cover found for: {series_name} Vol {volume}")
        return None


def test_wikipedia_fetcher():
    """Test the Wikipedia cover fetcher"""
    print("🧪 Testing Wikipedia Cover Fetcher...")

    fetcher = WikipediaCoverFetcher()

    # Test with known series that have Wikipedia covers
    test_cases = [
        ("Fisherman Sanpei", 1),  # Known to have Wikipedia cover
        ("Fairy Tail", 1),
        ("One Piece", 1)
    ]

    for series_name, volume in test_cases:
        print(f"\n🔍 Testing: {series_name} Vol {volume}")
        cover_url = fetcher.fetch_cover(series_name, volume)

        if cover_url:
            print(f"✅ Found cover: {cover_url}")
        else:
            print(f"❌ No cover found")


if __name__ == "__main__":
    test_wikipedia_fetcher()