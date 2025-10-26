#!/usr/bin/env python3
"""
Simple state-tracking monitor for manga cache pre-seeding process
Tracks existing progress and cache hits from BigQuery
"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta

class SimpleStateMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            'total_series': 55,  # Your list size
            'processed_series': 0,
            'cached_series': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'failures': 0,
            'current_series': '',
            'last_update': datetime.now()
        }
        self.running = True

    def get_bigquery_stats(self):
        """Get current stats from BigQuery cache"""
        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            # Get series count
            client = cache.client
            query = f"""
                SELECT COUNT(*) as series_count
                FROM `{cache.series_table_id}`
            """
            query_job = client.query(query)
            series_result = list(query_job.result())
            self.stats['cached_series'] = series_result[0]['series_count'] if series_result else 0

            return True
        except Exception as e:
            print(f"❌ BigQuery stats error: {e}")
            return False

    def parse_log_file(self, log_file_path):
        """Parse log file to extract current progress"""
        if not os.path.exists(log_file_path):
            return

        try:
            with open(log_file_path, 'r') as f:
                lines = f.readlines()[-200:]  # Read last 200 lines

            for line in lines:
                line = line.strip()

                # Track series processing
                if "Processing series:" in line:
                    series_name = line.split("Processing series:")[1].strip()
                    self.stats['current_series'] = series_name

                # Track cache hits
                elif "✅ Cached series info for:" in line:
                    self.stats['cache_hits'] += 1

                # Track API calls
                elif "🔍 No cached data found for:" in line:
                    self.stats['api_calls'] += 1

                # Track failures
                elif "❌ Failed to process:" in line:
                    self.stats['failures'] += 1

                # Track successful processing
                elif "✅ Successfully processed:" in line:
                    self.stats['processed_series'] += 1

        except Exception as e:
            pass

    def find_latest_log(self):
        """Find the latest log file"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return None

        log_files = [f for f in os.listdir(log_dir) if f.startswith("pre_seed_") and f.endswith(".log")]
        if not log_files:
            return None

        latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
        return os.path.join(log_dir, latest_log)

    def update_stats(self):
        """Update statistics from multiple sources"""
        # Get BigQuery stats
        self.get_bigquery_stats()

        # Parse log file
        log_file = self.find_latest_log()
        if log_file:
            self.parse_log_file(log_file)

    def display_stats(self):
        """Display stats with ANSI rewrites"""
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        self.update_stats()

        # Clear screen and move cursor to top
        print("\033[2J\033[H", end="")

        print("🎯 Manga Cache Pre-Seeding Monitor (State Tracking)")
        print("=" * 60)
        print(f"Elapsed Time: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        print(f"Last Update: {self.stats['last_update'].strftime('%H:%M:%S')}")
        print()

        # Progress
        progress_pct = (self.stats['processed_series'] / self.stats['total_series']) * 100 if self.stats['total_series'] > 0 else 0

        print(f"📊 Progress: {self.stats['processed_series']}/{self.stats['total_series']} series ({progress_pct:.1f}%)")
        bar_length = 40
        filled = int(bar_length * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}] {progress_pct:.1f}%")
        print()

        # Statistics
        print("📈 Statistics:")
        print(f"  Cached Series: {self.stats['cached_series']}")
        print(f"  Cache Hits: {self.stats['cache_hits']}")
        print(f"  API Calls: {self.stats['api_calls']}")
        print(f"  Failures: {self.stats['failures']}")

        # Efficiency
        total_operations = self.stats['cache_hits'] + self.stats['api_calls']
        cache_efficiency = (self.stats['cache_hits'] / total_operations * 100) if total_operations > 0 else 0
        print(f"  Cache Efficiency: {cache_efficiency:.1f}%")
        print()

        # Current activity
        if self.stats['current_series']:
            print(f"🔍 Currently Processing: {self.stats['current_series']}")
        else:
            print("🔍 Currently Processing: None")

        print()
        print("Press Ctrl+C to exit")

        self.stats['last_update'] = datetime.now()

    def run(self):
        """Run the monitor"""
        try:
            while self.running:
                try:
                    self.display_stats()
                    time.sleep(2)
                except KeyboardInterrupt:
                    self.running = False
                    break
        except KeyboardInterrupt:
            self.running = False
        finally:
            print("\033[?25h", end="")  # Show cursor

if __name__ == "__main__":
    monitor = SimpleStateMonitor()
    monitor.run()