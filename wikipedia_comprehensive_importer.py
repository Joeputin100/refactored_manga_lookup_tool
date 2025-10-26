#!/usr/bin/env python3
"""
Comprehensive Wikipedia Manga Series Importer

This script imports all missing best-selling manga series from Wikipedia,
using the Wikipedia API to get detailed information for each series.
"""

import sys
import os
import time
import json
import re
from typing import Dict, List, Any, Optional
from urllib.parse import unquote

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Please install required packages: pip install requests beautifulsoup4")
    sys.exit(1)

try:
    from bigquery_cache import BigQueryCache
    from mangadex_cover_fetcher import MangaDexCoverFetcher
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Some features may be limited")

from wikipedia_complete_series_list import get_all_series, WIKIPEDIA_BEST_SELLING_MANGA_SERIES


class WikipediaComprehensiveImporter:
    def __init__(self):
        self.bq_cache = None
        self.cover_fetcher = None
        self.setup_apis()
        self.wikipedia_base_url = "https://en.wikipedia.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MangaLookupTool/1.0 (https://github.com/your-repo; your-email@example.com)'
        })

    def setup_apis(self):
        """Initialize required APIs"""
        try:
            self.bq_cache = BigQueryCache()
            print("✅ BigQuery cache initialized")
        except Exception as e:
            print(f"❌ BigQuery cache error: {e}")

        try:
            self.cover_fetcher = MangaDexCoverFetcher()
            print("✅ MangaDex cover fetcher initialized")
        except Exception as e:
            print(f"❌ MangaDex cover fetcher error: {e}")

    def get_missing_series(self) -> List[str]:
        """Get list of Wikipedia series not in cache"""
        if not self.bq_cache or not self.bq_cache.enabled:
            print("❌ BigQuery cache not available - cannot check missing series")
            return []

        all_wikipedia_series = get_all_series()
        missing_series = []

        # Get all cached series
        try:
            query = 'SELECT DISTINCT series_name FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`'
            result = self.bq_cache.client.query(query)
            cached_series = [row['series_name'] for row in result]

            for series in all_wikipedia_series:
                # Check for exact match or case-insensitive match
                series_lower = series.lower()
                cached_lower = [s.lower() for s in cached_series]
                if series not in cached_series and series_lower not in cached_lower:
                    missing_series.append(series)

        except Exception as e:
            print(f"❌ Error checking cached series: {e}")
            # Fallback: return all Wikipedia series
            return all_wikipedia_series

        return missing_series

    def get_wikipedia_page_info(self, series_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information from Wikipedia page for a manga series
        """
        try:
            # Clean series name for URL
            clean_name = series_name.replace(' ', '_').replace('/', '_')
            url = f"{self.wikipedia_base_url}/wiki/{clean_name}"

            print(f"🔍 Fetching Wikipedia page: {series_name}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic information
            info = {
                'title': series_name,
                'wikipedia_url': url,
                'description': '',
                'author': '',
                'publisher': '',
                'genres': [],
                'status': '',
                'volumes': 0,
                'published': '',
                'cover_image_url': None
            }

            # Try to get description from first paragraph
            first_paragraph = soup.find('p')
            if first_paragraph:
                info['description'] = first_paragraph.get_text().strip()

            # Look for infobox table
            infobox = soup.find('table', class_='infobox')
            if infobox:
                rows = infobox.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    data = row.find('td')
                    if header and data:
                        header_text = header.get_text().strip().lower()
                        data_text = data.get_text().strip()

                        if 'author' in header_text:
                            info['author'] = data_text
                        elif 'publisher' in header_text:
                            info['publisher'] = data_text
                        elif 'genre' in header_text:
                            genres = [g.strip() for g in data_text.split(',')]
                            info['genres'] = genres
                        elif 'status' in header_text:
                            info['status'] = data_text
                        elif 'volumes' in header_text:
                            # Extract number from volumes field
                            volumes_match = re.search(r'(\d+)', data_text)
                            if volumes_match:
                                info['volumes'] = int(volumes_match.group(1))
                        elif 'published' in header_text:
                            info['published'] = data_text

            # Try to get cover image
            cover_img = soup.find('img')
            if cover_img and 'cover' in cover_img.get('alt', '').lower():
                src = cover_img.get('src')
                if src:
                    if src.startswith('//'):
                        info['cover_image_url'] = 'https:' + src
                    elif src.startswith('/'):
                        info['cover_image_url'] = self.wikipedia_base_url + src
                    else:
                        info['cover_image_url'] = src

            # If we couldn't find volumes in infobox, try to extract from text
            if info['volumes'] == 0:
                # Look for volume count in the page text
                volume_patterns = [
                    r'(\d+)\s+volumes',
                    r'(\d+)\s+tankōbon',
                    r'volumes\s+(\d+)'
                ]
                page_text = soup.get_text()
                for pattern in volume_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        info['volumes'] = int(match.group(1))
                        break

            return info

        except Exception as e:
            print(f"❌ Error fetching Wikipedia page for {series_name}: {e}")
            return None

    def get_cover_image_from_mangadex(self, series_name: str) -> Optional[str]:
        """Try to get cover image from MangaDex"""
        if not self.cover_fetcher:
            return None

        try:
            manga_data = self.cover_fetcher.search_manga(series_name)
            if manga_data:
                cover_url = self.cover_fetcher.get_cover_url(manga_data)
                return cover_url
        except Exception as e:
            print(f"❌ Error getting cover from MangaDex for {series_name}: {e}")

        return None

    def series_exists_in_cache(self, title: str) -> bool:
        """Check if series already exists in BigQuery cache"""
        if not self.bq_cache or not self.bq_cache.enabled:
            return False

        try:
            # Use case-insensitive query
            query = f'''SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) = LOWER("{title}")'''
            result = self.bq_cache.client.query(query).result()
            return any(result)
        except Exception as e:
            print(f"❌ Error checking series existence: {e}")

        return False

    def add_series_to_cache(self, series_info: Dict[str, Any]) -> bool:
        """Add series to BigQuery cache"""
        if not self.bq_cache or not self.bq_cache.enabled:
            print(f"❌ Cannot add {series_info['title']} - BigQuery cache unavailable")
            return False

        try:
            # Get cover image (try Wikipedia first, then MangaDex)
            cover_url = series_info.get('cover_image_url')
            if not cover_url:
                cover_url = self.get_cover_image_from_mangadex(series_info['title'])

            # Prepare series data for BigQuery cache
            series_data = {
                'corrected_series_name': series_info['title'],
                'authors': [series_info['author']] if series_info['author'] else [],
                'total_volumes': series_info['volumes'],
                'summary': series_info['description'],
                'spinoff_series': [],
                'alternate_editions': [],
                'cover_image_url': cover_url,
                'genres': series_info['genres'],
                'publisher': series_info['publisher'],
                'status': series_info['status'],
                'alternative_titles': [],
                'adaptations': []
            }

            # Add to cache
            self.bq_cache.cache_series_info(series_info['title'], series_data, api_source="wikipedia_comprehensive")
            print(f"✅ Added {series_info['title']} to cache")

            # Add volume 1 if we have volume count
            if series_info['volumes'] > 0:
                self.add_volume_1(series_info['title'])

            return True

        except Exception as e:
            print(f"❌ Error adding {series_info['title']}: {e}")
            return False

    def add_volume_1(self, series_title: str):
        """Add volume 1 for the series"""
        if not self.bq_cache or not self.bq_cache.enabled:
            return

        try:
            # Create basic volume data
            volume_data = {
                'book_title': f"{series_title} Volume 1",
                'authors': [],  # Will be filled from series data
                'isbn_13': None,
                'publisher_name': None,
                'copyright_year': None,
                'description': f"First volume of the best-selling manga series {series_title}",
                'physical_description': "192 pages, 5 x 7.5 inches",
                'genres': [],  # Will be filled from series data
                'msrp_cost': 9.99,
                'cover_image_url': None
            }

            # Add to cache
            self.bq_cache.cache_volume_info(series_title, 1, volume_data, api_source="wikipedia_comprehensive")
            print(f"✅ Added volume 1 for {series_title}")

        except Exception as e:
            print(f"❌ Error adding volume 1 for {series_title}: {e}")

    def import_missing_series(self, batch_size: int = 10, delay: int = 2):
        """Import all missing Wikipedia series"""
        print("🎯 Wikipedia Comprehensive Manga Importer")
        print("=" * 60)

        if not self.bq_cache:
            print("❌ BigQuery cache not available - cannot import")
            return

        # Get missing series
        missing_series = self.get_missing_series()
        print(f"📚 Found {len(missing_series)} missing Wikipedia series")

        if not missing_series:
            print("✅ All Wikipedia series are already in cache!")
            return

        # Process in batches
        total_batches = (len(missing_series) + batch_size - 1) // batch_size
        imported_count = 0
        failed_count = 0

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(missing_series))
            batch = missing_series[start_idx:end_idx]

            print(f"\n🔄 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} series)")

            for series_name in batch:
                print(f"\n📖 Processing: {series_name}")

                # Get Wikipedia page info
                series_info = self.get_wikipedia_page_info(series_name)
                if not series_info:
                    print(f"❌ Failed to get info for {series_name}")
                    failed_count += 1
                    continue

                # Add to cache
                if self.add_series_to_cache(series_info):
                    imported_count += 1
                    print(f"✅ Successfully imported {series_name}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to import {series_name}")

                # Rate limiting
                time.sleep(delay)

            # Brief pause between batches
            if batch_num < total_batches - 1:
                print(f"⏰ Waiting 5 seconds before next batch...")
                time.sleep(5)

        print(f"\n📊 Import Complete:")
        print(f"   ✅ Imported: {imported_count} new series")
        print(f"   ❌ Failed: {failed_count} series")
        print(f"   📚 Total processed: {imported_count + failed_count} series")


def main():
    importer = WikipediaComprehensiveImporter()
    importer.import_missing_series(batch_size=5, delay=3)


if __name__ == "__main__":
    main()