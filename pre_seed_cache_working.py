#!/usr/bin/env python3
"""
Working pre-seeding script for manga series cache
Uses actual API methods available on EC2
"""

import time
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the APIs directly
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, VertexAIAPI, BookInfo
from bigquery_cache import BigQueryCache


class CachePreSeeder:
    def __init__(self):
        # Initialize APIs
        self.deepseek_api = DeepSeekAPI()
        self.google_books_api = GoogleBooksAPI()
        self.vertex_api = VertexAIAPI()
        self.cache = BigQueryCache()

        self.stats = {
            'total_series': 0,
            'processed_series': 0,
            'successful_series': 0,
            'failed_series': 0,
            'total_volumes': 0,
            'start_time': None,
            'api_calls': 0,
            'cache_hits': 0
        }

    def get_series_list(self) -> List[str]:
        """Return the comprehensive list of series to pre-seed"""
        return [
            # Attack on Titan series
            "Attack on Titan",
            "Attack on Titan: Colossal Edition",
            "Attack on Titan: No Regrets",
            "Attack on Titan: Before the Fall",

            # Popular long-running series
            "One Piece",
            "Naruto",
            "Boruto: Naruto Next Generation",
            "Boruto: Two Blue Vortex",
            "Dragon Ball Z",
            "Bleach",
            "Fairy Tail",
            "Hunter x Hunter",
            "My Hero Academia",

            # Tokyo Ghoul series
            "Tokyo Ghoul",
            "Tokyo Ghoul: re",

            # Classic series
            "Bakuman",
            "Hikaru no Go",
            "Tegami Bachi",
            "Death Note",
            "Berserk",
            "Akira",
            "Inuyasha",
            "Ranma 1/2",

            # Modern hits
            "Tokyo Revengers",
            "To Your Eternity",
            "Haikyuu!",
            "Assassination Classroom",
            "Cells at Work",
            "Spy x Family",
            "Samurai 8",

            # Psychological/dark series
            "Flowers of Evil",
            "Goodnight Punpun",
            "Happiness",
            "All You Need is Kill",
            "Inuyashiki",
            "Gantz",
            "Gantz G",
            "Platinum End",

            # Other notable series
            "Alive",
            "Orange",
            "Welcome Back Alice",
            "Barefoot Gen",
            "Magus of the Library",
            "Thunder3",
            "Tokyo Alien Bros",
            "Centaur",
            "Blue Note",
            "Children of Whales",
            "Crayon Shinchan",
            "A Polar Bear in Love",
            "Sho-ha Shoten",
            "O Parts Hunter",
            "Otherworldly Izakaya Nobu",
            "Nausicaa of the Valley of the Wind",
            "Gigant"
        ]

    def search_series(self, series_name: str) -> Dict[str, Any]:
        """Search for series information using available APIs"""
        try:
            # Try DeepSeek API first for pre-seeding (as requested)
            book_info = self.deepseek_api.get_book_info(series_name, "1")
            if book_info and isinstance(book_info, BookInfo):
                self.stats['api_calls'] += 1
                return self._book_info_to_dict(book_info)

            # Fallback to Vertex AI
            series_info = self.vertex_api.get_comprehensive_series_info(series_name)
            if series_info:
                self.stats['api_calls'] += 1
                return series_info

            # Final fallback to Google Books
            total_volumes = self.google_books_api.get_total_volumes(series_name)
            if total_volumes:
                self.stats['api_calls'] += 1
                return {
                    'series_name': series_name,
                    'total_volumes': total_volumes,
                    'source': 'google_books'
                }

            return None

        except Exception as e:
            print(f"❌ Error searching for {series_name}: {e}")
            return None

    def _book_info_to_dict(self, book_info: BookInfo) -> Dict[str, Any]:
        """Convert BookInfo object to dictionary for caching"""
        return {
            'series_name': book_info.series_name,
            'book_title': book_info.book_title,
            'authors': book_info.authors,
            'publisher_name': book_info.publisher_name,
            'copyright_year': book_info.copyright_year,
            'isbn_13': book_info.isbn_13,
            'physical_description': book_info.physical_description,
            'description': book_info.description,
            'genres': book_info.genres,
            'msrp_cost': book_info.msrp_cost,
            'cover_image_url': book_info.cover_image_url,
            'source': 'deepseek'
        }

    def get_volumes(self, series_name: str) -> List[Dict[str, Any]]:
        """Get volumes information for a series"""
        try:
            volumes = []

            # Try to get volume 1 information as a sample
            book_info = self.deepseek_api.get_book_info(series_name, "1")
            if book_info and isinstance(book_info, BookInfo):
                self.stats['api_calls'] += 1
                volume_info = self._book_info_to_dict(book_info)
                volume_info['volume_number'] = 1
                volumes.append(volume_info)

            # Try to get comprehensive series info from Vertex AI
            series_info = self.vertex_api.get_comprehensive_series_info(series_name)
            if series_info and 'volumes' in series_info:
                self.stats['api_calls'] += 1
                volumes.extend(series_info['volumes'])

            # Get total volumes from Google Books
            total_volumes = self.google_books_api.get_total_volumes(series_name)
            if total_volumes:
                self.stats['api_calls'] += 1
                # Create placeholder volumes based on total count
                for i in range(1, min(total_volumes + 1, 6)):  # Limit to first 5 volumes
                    volumes.append({
                        'series_name': series_name,
                        'volume_number': i,
                        'source': 'google_books_estimated'
                    })

            return volumes

        except Exception as e:
            print(f"❌ Error getting volumes for {series_name}: {e}")
            return []

    def update_stats(self, series_name: str, success: bool, volumes_count: int = 0):
        """Update statistics for monitoring"""
        self.stats['processed_series'] += 1
        if success:
            self.stats['successful_series'] += 1
            self.stats['total_volumes'] += volumes_count
        else:
            self.stats['failed_series'] += 1

    def process_series(self, series_name: str) -> Dict[str, Any]:
        """Process a single series and cache its data"""
        try:
            print(f"🔍 Processing: {series_name}")

            # Get series information
            series_info = self.search_series(series_name)

            if not series_info:
                print(f"❌ No data found for: {series_name}")
                return {'success': False, 'error': 'No series data found'}

            # Cache series information
            if self.cache.enabled:
                self.cache.cache_series_info(series_name, series_info)

            # Get volumes information
            volumes_info = self.get_volumes(series_name)

            if volumes_info:
                # Cache volumes information
                if self.cache.enabled:
                    for volume in volumes_info:
                        self.cache.cache_volume_info(series_name, volume)

                print(f"✅ Cached {len(volumes_info)} volumes for: {series_name}")
                return {
                    'success': True,
                    'series_name': series_name,
                    'volumes_count': len(volumes_info),
                    'series_info': series_info
                }
            else:
                print(f"⚠️ No volumes found for: {series_name}")
                return {'success': True, 'series_name': series_name, 'volumes_count': 0}

        except Exception as e:
            print(f"❌ Error processing {series_name}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def pre_seed_all_series(self):
        """Pre-seed all series in the list"""
        series_list = self.get_series_list()
        self.stats['total_series'] = len(series_list)
        self.stats['start_time'] = datetime.now()

        print(f"🚀 Starting pre-seeding for {len(series_list)} series")
        print("=" * 50)

        results = []

        for i, series_name in enumerate(series_list, 1):
            print(f"\n[{i}/{len(series_list)}] " + "=" * 40)

            result = self.process_series(series_name)
            results.append(result)

            # Update stats
            self.update_stats(
                series_name,
                result.get('success', False),
                result.get('volumes_count', 0)
            )

            # Print current stats
            self.print_current_stats()

            # Rate limiting - be respectful to APIs
            time.sleep(2)

        return results

    def print_current_stats(self):
        """Print current statistics"""
        elapsed = datetime.now() - self.stats['start_time']
        progress = (self.stats['processed_series'] / max(self.stats['total_series'], 1)) * 100

        print(f"📊 Progress: {self.stats['processed_series']}/{self.stats['total_series']} ({progress:.1f}%)")
        print(f"✅ Success: {self.stats['successful_series']} | ❌ Failed: {self.stats['failed_series']}")
        print(f"📚 Volumes: {self.stats['total_volumes']} | 🔌 API Calls: {self.stats['api_calls']}")
        print(f"⏱️  Elapsed: {str(elapsed).split('.')[0]}")

    def print_final_report(self, results: List[Dict]):
        """Print final report"""
        print("\n" + "=" * 50)
        print("🎉 PRE-SEEDING COMPLETE!")
        print("=" * 50)

        total_time = datetime.now() - self.stats['start_time']

        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total Series: {self.stats['total_series']}")
        print(f"   Processed: {self.stats['processed_series']}")
        print(f"   Successful: {self.stats['successful_series']}")
        print(f"   Failed: {self.stats['failed_series']}")
        print(f"   Total Volumes: {self.stats['total_volumes']}")
        print(f"   API Calls: {self.stats['api_calls']}")
        print(f"   Total Time: {str(total_time).split('.')[0]}")

        # Show failed series
        failed_series = [
            r.get('series_name', 'Unknown')
            for r in results
            if not r.get('success', False)
        ]

        if failed_series:
            print(f"\n❌ FAILED SERIES ({len(failed_series)}):")
            for series in failed_series:
                print(f"   - {series}")

        # Show top series by volume count
        successful_series = [
            r for r in results
            if r.get('success', False) and r.get('volumes_count', 0) > 0
        ]

        if successful_series:
            top_series = sorted(
                successful_series,
                key=lambda x: x.get('volumes_count', 0),
                reverse=True
            )[:5]

            print(f"\n🏆 TOP SERIES BY VOLUME COUNT:")
            for i, series in enumerate(top_series, 1):
                print(f"   {i}. {series.get('series_name')}: {series.get('volumes_count')} volumes")


def main():
    """Main function"""
    print("🎯 Manga Cache Pre-Seeding Tool")
    print("=" * 40)

    # Check if BigQuery cache is available
    try:
        cache = BigQueryCache()
        if not cache.enabled:
            print("❌ BigQuery cache is not enabled. Please check your configuration.")
            return
        print("✅ BigQuery cache is enabled and ready")
    except Exception as e:
        print(f"❌ Error initializing BigQuery cache: {e}")
        return

    # Initialize pre-seeder
    pre_seeder = CachePreSeeder()

    # Start pre-seeding
    results = pre_seeder.pre_seed_all_series()

    # Print final report
    pre_seeder.print_final_report(results)


if __name__ == "__main__":
    main()