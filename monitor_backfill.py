#!/usr/bin/env python3
"""
Real-time TUI Monitor for BigQuery Metadata Backfill
Displays current progress, statistics, and live updates
"""
import time
import sys
import threading
from datetime import datetime
from typing import Dict, Any
from bigquery_cache import BigQueryCache

class BackfillMonitor:
    def __init__(self):
        self.cache = BigQueryCache()
        self.running = True
        self.last_update = None
        self.stats = {}

    def get_backfill_stats(self) -> Dict[str, Any]:
        """Get current backfill statistics from BigQuery"""
        try:
            # Query for missing metadata counts
            query = """
            SELECT
                COUNT(*) as total_volumes,
                COUNTIF(description IS NULL OR description = '') as missing_descriptions,
                COUNTIF(isbn_13 IS NULL OR isbn_13 = '') as missing_isbns,
                COUNTIF(copyright_year IS NULL) as missing_copyright_years,
                COUNTIF(publisher_name IS NULL OR publisher_name = '') as missing_publishers,
                COUNTIF(cover_image_url IS NULL OR cover_image_url = '') as missing_covers
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            """

            job = self.cache.client.query(query)
            result = list(job.result())[0]

            stats = {
                'total_volumes': result['total_volumes'],
                'missing_descriptions': result['missing_descriptions'],
                'missing_isbns': result['missing_isbns'],
                'missing_copyright_years': result['missing_copyright_years'],
                'missing_publishers': result['missing_publishers'],
                'missing_covers': result['missing_covers'],
                'last_update': datetime.now()
            }

            # Calculate progress percentages
            stats['descriptions_progress'] = 100 - (stats['missing_descriptions'] / stats['total_volumes'] * 100)
            stats['isbns_progress'] = 100 - (stats['missing_isbns'] / stats['total_volumes'] * 100)
            stats['copyright_progress'] = 100 - (stats['missing_copyright_years'] / stats['total_volumes'] * 100)
            stats['publishers_progress'] = 100 - (stats['missing_publishers'] / stats['total_volumes'] * 100)
            stats['covers_progress'] = 100 - (stats['missing_covers'] / stats['total_volumes'] * 100)

            # Calculate overall progress
            stats['overall_progress'] = (stats['descriptions_progress'] + stats['isbns_progress'] +
                                       stats['copyright_progress'] + stats['publishers_progress']) / 4

            return stats

        except Exception as e:
            return {'error': str(e)}

    def get_recent_updates(self) -> list:
        """Get recent volume updates (last 10)"""
        try:
            query = """
            SELECT
                series_name,
                volume_number,
                description,
                isbn_13,
                copyright_year,
                publisher_name
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE description IS NOT NULL AND description != ''
            ORDER BY RAND()
            LIMIT 10
            """

            job = self.cache.client.query(query)
            return list(job.result())

        except Exception as e:
            return []

    def clear_screen(self):
        """Clear the terminal screen"""
        print('\033[2J\033[H', end='')

    def display_progress_bar(self, percentage: float, width: int = 40) -> str:
        """Create a progress bar string"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    def display_stats(self, stats: Dict[str, Any]):
        """Display the statistics in a formatted TUI"""
        self.clear_screen()

        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║                BIGQUERY METADATA BACKFILL MONITOR                   ║")
        print("╠═══════════════════════════════════════════���══════════════════════════╣")

        if 'error' in stats:
            print(f"║ Error: {stats['error']:<65} ║")
            print("╚══════════════════════════════════════════════════════════════════════╝")
            return

        # Overall progress
        print(f"║ Overall Progress: {self.display_progress_bar(stats['overall_progress']):<45} ║")
        print("╠══════════════════════════════════════════════════════════════════════╣")

        # Individual progress bars
        print(f"║ 📝 Descriptions:  {self.display_progress_bar(stats['descriptions_progress']):<45} ║")
        print(f"║ 📚 ISBNs:          {self.display_progress_bar(stats['isbns_progress']):<45} ║")
        print(f"║ 📅 Copyright Years: {self.display_progress_bar(stats['copyright_progress']):<45} ║")
        print(f"║ 🏢 Publishers:     {self.display_progress_bar(stats['publishers_progress']):<45} ║")
        print(f"║ 🖼️  Cover Images:   {self.display_progress_bar(stats['covers_progress']):<45} ║")

        print("╠══════════════════════════════════════════════════════════════════════╣")

        # Detailed counts
        print(f"║ Total Volumes: {stats['total_volumes']:<6} | Missing Descriptions: {stats['missing_descriptions']:<4} ║")
        print(f"║                | Missing ISBNs: {stats['missing_isbns']:<10} | Missing Years: {stats['missing_copyright_years']:<4} ║")
        print(f"║                | Missing Publishers: {stats['missing_publishers']:<4} | Missing Covers: {stats['missing_covers']:<4} ║")

        print("╠══════════════════════════════════════════════════════════════════════╣")

        # Recent updates
        recent = self.get_recent_updates()
        if recent:
            print("║ Recent Updates (Sample):                                           ║")
            for i, vol in enumerate(recent[:5]):
                series = vol['series_name'][:20] + '...' if len(vol['series_name']) > 20 else vol['series_name']
                print(f"║ {i+1:2d}. {series:<25} Vol {vol['volume_number']:<3} ║")

        print("╠══════════════════════════════════════════════════════════════════════╣")
        print(f"║ Last Updated: {stats['last_update'].strftime('%Y-%m-%d %H:%M:%S'):<49} ║")
        print("║ Press Ctrl+C to exit                                                  ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")

    def run_monitor(self, refresh_interval: int = 5):
        """Run the real-time monitor"""
        print("Starting BigQuery Backfill Monitor...")
        print("Press Ctrl+C to exit\n")

        try:
            while self.running:
                stats = self.get_backfill_stats()
                self.display_stats(stats)
                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n\nMonitor stopped by user")
            self.running = False
        except Exception as e:
            print(f"\nError in monitor: {e}")
            self.running = False

def main():
    """Main function to run the monitor"""
    monitor = BackfillMonitor()
    monitor.run_monitor(refresh_interval=5)

if __name__ == "__main__":
    main()