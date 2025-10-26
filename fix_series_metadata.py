#!/usr/bin/env python3
"""
Comprehensive metadata fixer for all 55 manga series
Checks BigQuery cache for missing fields and fills gaps using multiple APIs
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import DeepSeekAPI, GoogleBooksAPI, VertexAIAPI, ProjectState
from bigquery_cache import BigQueryCache


class SeriesMetadataFixer:
    def __init__(self):
        # Initialize APIs
        self.deepseek_api = DeepSeekAPI()
        self.google_books_api = GoogleBooksAPI()
        self.vertex_api = VertexAIAPI()
        self.cache = BigQueryCache()
        self.project_state = ProjectState()

        self.stats = {
            'total_series': 0,
            'processed': 0,
            'fixed_metadata': 0,
            'fixed_covers': 0,
            'errors': 0
        }

    def get_all_series_list(self) -> List[str]:
        """Get the complete list of 55 series"""
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

    def check_series_metadata(self, series_name: str) -> Dict[str, Any]:
        """Check what metadata is missing for a series"""
        cached_info = self.cache.get_series_info(series_name)

        if not cached_info:
            return {
                'exists': False,
                'missing_fields': ['all'],
                'cover_missing': True,
                'needs_complete_rebuild': True
            }

        missing_fields = []
        required_fields = [
            'corrected_series_name',
            'authors',
            'extant_volumes',
            'summary',
            'genres',
            'publisher',
            'status',
            'alternative_titles',
            'adaptations'
        ]

        for field in required_fields:
            if not cached_info.get(field):
                missing_fields.append(field)

        cover_missing = not cached_info.get('cover_image_url')

        return {
            'exists': True,
            'missing_fields': missing_fields,
            'cover_missing': cover_missing,
            'needs_complete_rebuild': len(missing_fields) > 5,
            'current_data': cached_info
        }

    def get_comprehensive_series_info(self, series_name: str) -> Dict[str, Any]:
        """Get comprehensive series information using multiple APIs"""
        print(f"  🔍 Fetching comprehensive info for: {series_name}")

        # Try Vertex AI first for comprehensive data
        try:
            vertex_info = self.vertex_api.get_comprehensive_series_info(series_name)
            if vertex_info and vertex_info.get('authors'):
                print(f"  ✅ Got comprehensive data from Vertex AI")
                return vertex_info
        except Exception as e:
            print(f"  ❌ Vertex AI failed: {e}")

        # Fallback to DeepSeek for volume 1 info
        try:
            book_info = self.deepseek_api.get_book_info(series_name, 1, self.project_state)
            if book_info:
                print(f"  ✅ Got basic data from DeepSeek")
                return {
                    'corrected_series_name': book_info.get('series_name', series_name),
                    'authors': book_info.get('authors', []),
                    'extant_volumes': book_info.get('number_of_extant_volumes', 0),
                    'summary': book_info.get('description', ''),
                    'genres': book_info.get('genres', []),
                    'publisher': book_info.get('publisher_name', ''),
                    'status': 'Unknown',
                    'alternative_titles': [],
                    'adaptations': []
                }
        except Exception as e:
            print(f"  ❌ DeepSeek failed: {e}")

        # Final fallback - basic info from Google Books
        try:
            total_volumes = self.google_books_api.get_total_volumes(series_name)
            print(f"  ✅ Got volume count from Google Books: {total_volumes}")
            return {
                'corrected_series_name': series_name,
                'authors': [],
                'extant_volumes': total_volumes,
                'summary': '',
                'genres': [],
                'publisher': '',
                'status': 'Unknown',
                'alternative_titles': [],
                'adaptations': []
            }
        except Exception as e:
            print(f"  ❌ Google Books failed: {e}")

        return None

    def get_cover_image_url(self, series_name: str) -> str:
        """Get cover image URL using multiple sources"""
        print(f"  🖼️  Fetching cover for: {series_name}")

        # Try Google Books first
        try:
            cover_url = self.google_books_api.get_series_cover_url(series_name, self.project_state)
            if cover_url:
                print(f"  ✅ Got cover from Google Books")
                return cover_url
        except Exception as e:
            print(f"  ❌ Google Books cover failed: {e}")

        # Try DeepSeek for volume 1 cover
        try:
            book_info = self.deepseek_api.get_book_info(series_name, 1, self.project_state)
            if book_info and book_info.get('cover_image_url'):
                print(f"  ✅ Got cover from DeepSeek")
                return book_info.get('cover_image_url')
        except Exception as e:
            print(f"  ❌ DeepSeek cover failed: {e}")

        return None

    def fix_series_metadata(self, series_name: str) -> Dict[str, Any]:
        """Fix metadata for a single series"""
        print(f"\n📚 Processing: {series_name}")

        # Check current state
        current_state = self.check_series_metadata(series_name)

        if not current_state['exists'] or current_state['needs_complete_rebuild']:
            print(f"  🔄 Series needs complete rebuild")

            # Get comprehensive info
            new_info = self.get_comprehensive_series_info(series_name)
            if not new_info:
                print(f"  ❌ Failed to get series info")
                return {'success': False, 'error': 'Failed to get series info'}

            # Get cover image
            cover_url = self.get_cover_image_url(series_name)
            if cover_url:
                new_info['cover_image_url'] = cover_url
                self.stats['fixed_covers'] += 1

            # Cache the complete info
            if self.cache.enabled:
                self.cache.cache_series_info(series_name, new_info)

            self.stats['fixed_metadata'] += 1
            return {'success': True, 'action': 'complete_rebuild', 'cover_added': bool(cover_url)}

        else:
            # Fix missing fields
            current_data = current_state['current_data']
            fixed_anything = False

            # Fix missing fields
            if current_state['missing_fields']:
                print(f"  🔧 Fixing missing fields: {current_state['missing_fields']}")

                # Get additional info for missing fields
                additional_info = self.get_comprehensive_series_info(series_name)
                if additional_info:
                    for field in current_state['missing_fields']:
                        if additional_info.get(field):
                            current_data[field] = additional_info[field]
                            fixed_anything = True

                    # Update cache if we fixed anything
                    if fixed_anything and self.cache.enabled:
                        self.cache.cache_series_info(series_name, current_data)
                        self.stats['fixed_metadata'] += 1

            # Fix missing cover
            if current_state['cover_missing']:
                print(f"  🖼️  Adding missing cover")
                cover_url = self.get_cover_image_url(series_name)
                if cover_url:
                    current_data['cover_image_url'] = cover_url
                    if self.cache.enabled:
                        self.cache.cache_series_info(series_name, current_data)
                    self.stats['fixed_covers'] += 1
                    fixed_anything = True

            return {'success': True, 'action': 'partial_fix', 'fixed_anything': fixed_anything}

    def run_comprehensive_fix(self):
        """Run comprehensive fix for all series"""
        series_list = self.get_all_series_list()
        self.stats['total_series'] = len(series_list)

        print(f"🚀 Starting comprehensive metadata fix for {len(series_list)} series")
        print("=" * 60)

        results = []

        for i, series_name in enumerate(series_list, 1):
            print(f"\n[{i}/{len(series_list)}] {'='*40}")

            try:
                result = self.fix_series_metadata(series_name)
                results.append({
                    'series_name': series_name,
                    **result
                })

                self.stats['processed'] += 1

                # Rate limiting
                time.sleep(2)

            except Exception as e:
                print(f"❌ Error processing {series_name}: {e}")
                results.append({
                    'series_name': series_name,
                    'success': False,
                    'error': str(e)
                })
                self.stats['errors'] += 1

            # Print progress
            self.print_progress()

        # Final report
        self.print_final_report(results)
        return results

    def print_progress(self):
        """Print current progress"""
        progress = (self.stats['processed'] / self.stats['total_series']) * 100
        print(f"📊 Progress: {self.stats['processed']}/{self.stats['total_series']} ({progress:.1f}%)")
        print(f"✅ Fixed metadata: {self.stats['fixed_metadata']} | 🖼️ Fixed covers: {self.stats['fixed_covers']} | ❌ Errors: {self.stats['errors']}")

    def print_final_report(self, results: List[Dict]):
        """Print final report"""
        print("\n" + "=" * 60)
        print("🎉 COMPREHENSIVE METADATA FIX COMPLETE!")
        print("=" * 60)

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total Series: {self.stats['total_series']}")
        print(f"   Processed: {self.stats['processed']}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Metadata Fixed: {self.stats['fixed_metadata']}")
        print(f"   Covers Fixed: {self.stats['fixed_covers']}")

        if failed:
            print(f"\n❌ FAILED SERIES ({len(failed)}):")
            for series in failed:
                print(f"   - {series['series_name']}: {series.get('error', 'Unknown error')}")

        # Show series that still need work
        incomplete_series = []
        for result in successful:
            series_name = result['series_name']
            current_state = self.check_series_metadata(series_name)
            if current_state['missing_fields'] or current_state['cover_missing']:
                incomplete_series.append({
                    'series_name': series_name,
                    'missing_fields': current_state['missing_fields'],
                    'cover_missing': current_state['cover_missing']
                })

        if incomplete_series:
            print(f"\n⚠️  SERIES STILL NEEDING WORK ({len(incomplete_series)}):")
            for series in incomplete_series[:10]:  # Show first 10
                issues = []
                if series['missing_fields']:
                    issues.append(f"missing {len(series['missing_fields'])} fields")
                if series['cover_missing']:
                    issues.append("missing cover")
                print(f"   - {series['series_name']}: {', '.join(issues)}")
            if len(incomplete_series) > 10:
                print(f"   ... and {len(incomplete_series) - 10} more")


def main():
    """Main function"""
    print("🎯 Comprehensive Manga Series Metadata Fixer")
    print("=" * 50)

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

    # Initialize fixer
    fixer = SeriesMetadataFixer()

    # Run comprehensive fix
    results = fixer.run_comprehensive_fix()

    print("\n✅ Metadata fixing process completed!")


if __name__ == "__main__":
    main()