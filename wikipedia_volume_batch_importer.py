#!/usr/bin/env python3
"""
Wikipedia Volume Batch Importer

This script imports volume 1 for all Wikipedia series that don't have volume data yet.
It can run simultaneously with the series importer on EC2.
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wikipedia_volume_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from bigquery_cache import BigQueryCache
    from manga_lookup import DeepSeekAPI
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)


class WikipediaVolumeBatchImporter:
    def __init__(self):
        self.bq_cache = None
        self.deepseek_api = None
        self.setup_apis()
        self.status_file = "wikipedia_volume_import_status.json"
        self.load_status()

    def setup_apis(self):
        """Initialize required APIs"""
        try:
            self.bq_cache = BigQueryCache()
            logger.info("✅ BigQuery cache initialized")
        except Exception as e:
            logger.error(f"❌ BigQuery cache error: {e}")

        try:
            self.deepseek_api = DeepSeekAPI()
            logger.info("✅ DeepSeek API initialized")
        except Exception as e:
            logger.error(f"❌ DeepSeek API error: {e}")

    def load_status(self):
        """Load import status from file"""
        self.status = {
            'started_at': None,
            'last_run': None,
            'total_volumes_imported': 0,
            'total_series_processed': 0,
            'completed': False,
            'errors': []
        }

        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.status = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load status file: {e}")

    def save_status(self):
        """Save import status to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save status file: {e}")

    def get_series_needing_volume_1(self) -> List[str]:
        """Get list of Wikipedia series that need volume 1 imported"""
        if not self.bq_cache or not self.bq_cache.enabled:
            logger.error("BigQuery cache not available")
            return []

        try:
            # Get all Wikipedia series
            query = '''
            SELECT DISTINCT series_name
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE api_source LIKE "%wikipedia%"
            '''
            result = self.bq_cache.client.query(query)
            wikipedia_series = [row['series_name'] for row in result]

            # Check which ones don't have volume 1
            series_needing_volume = []
            for series in wikipedia_series:
                volume_query = f'''
                SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                WHERE LOWER(series_name) = LOWER("{series}") AND volume_number = 1
                '''
                volume_result = list(self.bq_cache.client.query(volume_query))
                if not volume_result:
                    series_needing_volume.append(series)

            logger.info(f"Found {len(series_needing_volume)} series needing volume 1")
            return series_needing_volume

        except Exception as e:
            logger.error(f"Error getting series needing volume 1: {e}")
            return []

    def import_volume_1_for_series(self, series_name: str) -> bool:
        """Import volume 1 for a specific series"""
        if not self.bq_cache or not self.bq_cache.enabled:
            return False

        try:
            logger.info(f"📚 Importing volume 1 for: {series_name}")

            # Get series info for reference
            series_query = f'''
            SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE LOWER(series_name) = LOWER("{series_name}")
            '''
            series_result = list(self.bq_cache.client.query(series_query))
            if not series_result:
                logger.warning(f"No series info found for {series_name}")
                return False

            series_info = series_result[0]

            # Create volume data
            volume_data = {
                'book_title': f"{series_name} Volume 1",
                'authors': [],
                'isbn_13': None,
                'publisher_name': series_info.get('publisher', ''),
                'copyright_year': None,
                'description': f"First volume of {series_name}. {series_info.get('summary', '')}",
                'physical_description': "192 pages, 5 x 7.5 inches",
                'genres': [],
                'msrp_cost': 9.99,
                'cover_image_url': series_info.get('cover_image_url')
            }

            # Try to get author from series info
            if series_info.get('authors'):
                authors = series_info['authors']
                if isinstance(authors, str):
                    volume_data['authors'] = [authors]
                elif isinstance(authors, list):
                    volume_data['authors'] = authors

            # Try to get genres from series info
            if series_info.get('genres'):
                genres = series_info['genres']
                if isinstance(genres, str):
                    volume_data['genres'] = [genres]
                elif isinstance(genres, list):
                    volume_data['genres'] = genres

            # Add to cache
            self.bq_cache.cache_volume_info(series_name, 1, volume_data, api_source="wikipedia_volume_batch")
            logger.info(f"✅ Added volume 1 for {series_name}")

            return True

        except Exception as e:
            logger.error(f"❌ Error importing volume 1 for {series_name}: {e}")
            return False

    def run_volume_batch(self, batch_size: int = 19) -> Dict[str, Any]:
        """Run a single volume import batch"""
        logger.info(f"Starting volume import batch (size: {batch_size})")

        try:
            series_needing_volume = self.get_series_needing_volume_1()
            if not series_needing_volume:
                logger.info("✅ No series need volume 1 import")
                return {'imported': 0, 'failed': 0, 'completed': True}

            logger.info(f"Found {len(series_needing_volume)} series needing volume 1")

            imported_count = 0
            failed_count = 0

            # Process batch
            for i, series_name in enumerate(series_needing_volume[:batch_size]):
                logger.info(f"Processing {i+1}/{min(batch_size, len(series_needing_volume))}: {series_name}")

                if self.import_volume_1_for_series(series_name):
                    imported_count += 1
                else:
                    failed_count += 1

                # Rate limiting
                time.sleep(1)

            result = {
                'imported': imported_count,
                'failed': failed_count,
                'completed': len(series_needing_volume) <= batch_size
            }

            logger.info(f"Volume batch complete: {imported_count} imported, {failed_count} failed")
            return result

        except Exception as e:
            logger.error(f"Error in volume import batch: {e}")
            return {'imported': 0, 'failed': 0, 'completed': False}

    def run_continuous_volume_import(self, batch_size: int = 19, interval_minutes: int = 15):
        """Run continuous volume import with specified interval"""
        logger.info("🚀 Starting continuous Wikipedia volume import")
        logger.info(f"Batch size: {batch_size}, Interval: {interval_minutes} minutes")

        self.status['started_at'] = datetime.now().isoformat()
        self.status['completed'] = False
        self.save_status()

        while True:
            try:
                # Check if we should run
                series_needing_volume = self.get_series_needing_volume_1()
                if not series_needing_volume:
                    logger.info("🎉 All Wikipedia series have volume 1!")
                    self.status['completed'] = True
                    self.save_status()
                    break

                logger.info(f"📚 {len(series_needing_volume)} series need volume 1")

                # Run volume batch
                self.status['last_run'] = datetime.now().isoformat()

                result = self.run_volume_batch(batch_size)

                # Update status
                self.status['total_volumes_imported'] += result['imported']
                self.status['total_series_processed'] += (result['imported'] + result['failed'])

                if result['completed']:
                    logger.info("🎉 Volume import completed!")
                    self.status['completed'] = True
                    self.save_status()
                    break

                self.save_status()

                # Wait for next interval
                logger.info(f"⏰ Waiting {interval_minutes} minutes until next volume batch...")
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("🛑 Volume import interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in continuous volume import: {e}")
                self.status['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
                self.save_status()

                # Wait before retrying
                time.sleep(60)

        logger.info("📊 Final volume import statistics:")
        logger.info(f"   Total volumes imported: {self.status['total_volumes_imported']}")
        logger.info(f"   Total series processed: {self.status['total_series_processed']}")

    def get_status(self) -> Dict[str, Any]:
        """Get current volume import status"""
        series_needing_volume = self.get_series_needing_volume_1()

        status = self.status.copy()
        status['series_needing_volume'] = len(series_needing_volume)

        return status


def main():
    """Main function for volume batch import"""
    import argparse

    parser = argparse.ArgumentParser(description='Wikipedia Volume Batch Importer')
    parser.add_argument('--batch-size', type=int, default=19, help='Number of volumes to process per batch')
    parser.add_argument('--interval', type=int, default=15, help='Minutes between batches')
    parser.add_argument('--single-run', action='store_true', help='Run a single batch and exit')
    parser.add_argument('--status', action='store_true', help='Show current status and exit')

    args = parser.parse_args()

    importer = WikipediaVolumeBatchImporter()

    if args.status:
        status = importer.get_status()
        print("📊 Wikipedia Volume Import Status")
        print("=" * 40)
        print(f"Started: {status.get('started_at', 'Never')}")
        print(f"Last Run: {status.get('last_run', 'Never')}")
        print(f"Volumes Imported: {status['total_volumes_imported']}")
        print(f"Series Processed: {status['total_series_processed']}")
        print(f"Series Needing Volume 1: {status['series_needing_volume']}")
        print(f"Completed: {'✅' if status['completed'] else '❌'}")
        return

    if args.single_run:
        logger.info("Running single volume import batch")
        result = importer.run_volume_batch(args.batch_size)
        print(f"Volume batch result: {result}")
    else:
        importer.run_continuous_volume_import(args.batch_size, args.interval)


if __name__ == "__main__":
    main()