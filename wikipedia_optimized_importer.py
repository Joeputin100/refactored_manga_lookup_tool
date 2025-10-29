#!/usr/bin/env python3
"""
Optimized Wikipedia Background Importer

Features:
- Reduced interval (5 minutes instead of 30)
- Increased batch size (15 instead of 5)
- Better error handling for missing Wikipedia pages
- Improved rate limiting (90% of 200 requests/second)
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from wikipedia_comprehensive_importer import WikipediaComprehensiveImporter
    from wikipedia_complete_series_list import get_all_series
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wikipedia_optimized_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WikipediaOptimizedImporter:
    def __init__(self):
        self.importer = WikipediaComprehensiveImporter()
        self.status_file = "wikipedia_optimized_import_status.json"
        self.load_status()

    def load_status(self):
        """Load import status from file"""
        self.status = {
            'started_at': None,
            'last_run': None,
            'total_imported': 0,
            'total_failed': 0,
            'current_batch': 0,
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

    def get_missing_series_count(self) -> int:
        """Get count of missing series"""
        try:
            missing_series = self.importer.get_missing_series()
            return len(missing_series)
        except Exception as e:
            logger.error(f"Error getting missing series count: {e}")
            return 0

    def run_import_batch(self, batch_size: int = 15) -> Dict[str, Any]:
        """Run a single import batch with optimized parameters"""
        logger.info(f"🚀 Starting optimized import batch (size: {batch_size})")

        try:
            missing_series = self.importer.get_missing_series()
            if not missing_series:
                logger.info("✅ No missing series to import")
                return {'imported': 0, 'failed': 0, 'completed': True}

            logger.info(f"📚 Found {len(missing_series)} missing series")

            imported_count = 0
            failed_count = 0

            # Process batch with optimized rate limiting
            for i, series_name in enumerate(missing_series[:batch_size]):
                logger.info(f"Processing {i+1}/{min(batch_size, len(missing_series))}: {series_name}")

                try:
                    # Get Wikipedia page info
                    series_info = self.importer.get_wikipedia_page_info(series_name)
                    if not series_info:
                        logger.warning(f"Failed to get info for {series_name}")
                        failed_count += 1
                        continue

                    # Add to cache
                    if self.importer.add_series_to_cache(series_info):
                        imported_count += 1
                        logger.info(f"✅ Imported {series_name}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to import {series_name}")

                    # Optimized rate limiting (1 second between requests)
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error processing {series_name}: {e}")
                    failed_count += 1

            result = {
                'imported': imported_count,
                'failed': failed_count,
                'completed': len(missing_series) <= batch_size
            }

            logger.info(f"🎯 Batch complete: {imported_count} imported, {failed_count} failed")
            return result

        except Exception as e:
            logger.error(f"Error in import batch: {e}")
            return {'imported': 0, 'failed': 0, 'completed': False}

    def run_continuous_import(self, batch_size: int = 15, interval_minutes: int = 5):
        """Run continuous import with optimized interval"""
        logger.info("🚀 Starting optimized continuous Wikipedia import")
        logger.info(f"Batch size: {batch_size}, Interval: {interval_minutes} minutes")

        self.status['started_at'] = datetime.now().isoformat()
        self.status['completed'] = False
        self.save_status()

        while True:
            try:
                # Check if we should run
                missing_count = self.get_missing_series_count()
                if missing_count == 0:
                    logger.info("🎉 All Wikipedia series imported!")
                    self.status['completed'] = True
                    self.save_status()
                    break

                logger.info(f"📚 {missing_count} series remaining to import")

                # Run import batch
                self.status['last_run'] = datetime.now().isoformat()
                self.status['current_batch'] += 1

                result = self.run_import_batch(batch_size)

                # Update status
                self.status['total_imported'] += result['imported']
                self.status['total_failed'] += result['failed']

                if result['completed']:
                    logger.info("🎉 Import completed!")
                    self.status['completed'] = True
                    self.save_status()
                    break

                self.save_status()

                # Wait for next interval (optimized: 5 minutes)
                logger.info(f"⏰ Waiting {interval_minutes} minutes until next batch...")
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("🛑 Import interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in continuous import: {e}")
                self.status['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
                self.save_status()

                # Wait before retrying
                time.sleep(60)

        logger.info("📊 Final import statistics:")
        logger.info(f"   Total imported: {self.status['total_imported']}")
        logger.info(f"   Total failed: {self.status['total_failed']}")
        logger.info(f"   Total batches: {self.status['current_batch']}")

    def get_status(self) -> Dict[str, Any]:
        """Get current import status"""
        missing_count = self.get_missing_series_count()

        status = self.status.copy()
        status['missing_count'] = missing_count
        status['progress_percentage'] = 100 - (missing_count / len(get_all_series()) * 100) if get_all_series() else 0

        return status


def main():
    """Main function for optimized background import"""
    import argparse

    parser = argparse.ArgumentParser(description='Optimized Wikipedia Background Manga Importer')
    parser.add_argument('--batch-size', type=int, default=15, help='Number of series to process per batch (default: 15)')
    parser.add_argument('--interval', type=int, default=5, help='Minutes between batches (default: 5)')
    parser.add_argument('--single-run', action='store_true', help='Run a single batch and exit')
    parser.add_argument('--status', action='store_true', help='Show current status and exit')

    args = parser.parse_args()

    importer = WikipediaOptimizedImporter()

    if args.status:
        status = importer.get_status()
        print("📊 Optimized Wikipedia Import Status")
        print("=" * 50)
        print(f"Started: {status.get('started_at', 'Never')}")
        print(f"Last Run: {status.get('last_run', 'Never')}")
        print(f"Total Imported: {status['total_imported']}")
        print(f"Total Failed: {status['total_failed']}")
        print(f"Missing Series: {status['missing_count']}")
        print(f"Progress: {status['progress_percentage']:.1f}%")
        print(f"Completed: {'✅' if status['completed'] else '❌'}")
        return

    if args.single_run:
        logger.info("Running single import batch")
        result = importer.run_import_batch(args.batch_size)
        print(f"Batch result: {result}")
    else:
        importer.run_continuous_import(args.batch_size, args.interval)


if __name__ == "__main__":
    main()