#!/usr/bin/env python3
"""
Monitor and run backfill for high-priority series with real-time status updates
"""

import sys
import os
import time
import threading
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

class HighPriorityMonitor:
    """Monitor high-priority series backfill progress"""

    def __init__(self):
        self.cache = BigQueryCache()
        self.high_priority_series = [
            "One Piece",
            "Dragon Ball Z",
            "Tokyo Ghoul",
            "Tokyo Ghoul:re",
            "Bleach",
            "Naruto",
            "Bakuman",
            "Assassination Classroom",
            "Hunter x Hunter"
        ]
        self.series_volumes = {
            "One Piece": 107,
            "Dragon Ball Z": 42,
            "Tokyo Ghoul": 14,
            "Tokyo Ghoul:re": 16,
            "Bleach": 74,
            "Naruto": 72,
            "Bakuman": 20,
            "Assassination Classroom": 21,
            "Hunter x Hunter": 37
        }

    def get_series_status(self, series_name):
        """Get current status for a series"""

        # Get volumes for this series
        volumes = []
        expected = self.series_volumes.get(series_name, 0)

        for volume_num in range(1, expected + 1):
            volume_info = self.cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])

        if not volumes:
            return {
                "status": "NOT_FOUND",
                "volumes_found": 0,
                "volumes_expected": expected,
                "completion_rate": 0
            }

        # Check metadata completeness
        missing_fields = 0
        total_fields = len(volumes) * 6  # 6 metadata fields per volume

        for volume in volumes:
            if not volume.get('description'):
                missing_fields += 1
            if not volume.get('isbn_13'):
                missing_fields += 1
            if not volume.get('copyright_year'):
                missing_fields += 1
            if not volume.get('publisher_name'):
                missing_fields += 1
            if not volume.get('cover_image_url') and not volume.get('cover_image_data'):
                missing_fields += 1
            if not volume.get('msrp_cost'):
                missing_fields += 1

        completion_rate = ((total_fields - missing_fields) / total_fields) * 100

        return {
            "status": "FOUND",
            "volumes_found": len(volumes),
            "volumes_expected": expected,
            "completion_rate": completion_rate,
            "missing_fields": missing_fields
        }

    def display_status(self):
        """Display current status of all high-priority series"""

        print(f"\n📊 HIGH-PRIORITY SERIES STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)

        total_completion = 0
        total_series = 0

        for series_name in self.high_priority_series:
            status = self.get_series_status(series_name)

            if status["status"] == "NOT_FOUND":
                print(f"📚 {series_name:25} ❌ NOT FOUND")
            else:
                completion = status["completion_rate"]
                total_completion += completion
                total_series += 1

                # Color coding based on completion
                if completion >= 95:
                    icon = "✅"
                elif completion >= 80:
                    icon = "🟡"
                elif completion >= 50:
                    icon = "🟠"
                else:
                    icon = "🔴"

                print(f"📚 {series_name:25} {icon} {completion:5.1f}% ({status['volumes_found']}/{status['volumes_expected']} vols)")

        if total_series > 0:
            avg_completion = total_completion / total_series
            print(f"\n📈 AVERAGE COMPLETION: {avg_completion:.1f}%")

    def run_with_monitoring(self):
        """Run backfill with real-time monitoring"""

        print("🚀 STARTING HIGH-PRIORITY SERIES BACKFILL WITH MONITORING")
        print("=" * 70)
        print("📊 Status updates every 30 seconds")
        print("⏹️  Press Ctrl+C to stop")
        print()

        # Initial status
        self.display_status()

        # Start monitoring thread
        stop_monitoring = threading.Event()

        def monitor_loop():
            while not stop_monitoring.is_set():
                time.sleep(30)
                if not stop_monitoring.is_set():
                    self.display_status()

        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            # Run backfill operations
            print("\n🔄 Starting backfill operations...")

            # First, import Tokyo Ghoul:re using regular lookup
            print("\n📚 Importing Tokyo Ghoul:re using regular lookup...")
            self.import_tokyo_ghoul_re()

            # Run enhanced backfill on all series
            print("\n🔄 Running enhanced backfill on all series...")
            self.run_enhanced_backfill()

            # Keep monitoring until manually stopped
            print("\n📊 Monitoring active. Press Ctrl+C to stop.")
            while True:
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n\n🛑 Backfill monitoring stopped by user")
            stop_monitoring.set()

        # Final status
        print("\n📊 FINAL STATUS:")
        self.display_status()

    def import_tokyo_ghoul_re(self):
        """Import Tokyo Ghoul:re using regular lookup process"""

        try:
            # Import using the regular manga lookup process
            from manga_lookup import MangaLookup

            lookup = MangaLookup()
            print("   🔍 Looking up Tokyo Ghoul:re volumes...")

            # Look up first 5 volumes to start
            for volume_num in range(1, 6):
                result = lookup.lookup_manga_volume("Tokyo Ghoul:re", volume_num)
                if result:
                    print(f"   ✅ Volume {volume_num} imported")
                else:
                    print(f"   ❌ Volume {volume_num} failed")
                time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"   ❌ Tokyo Ghoul:re import failed: {e}")

    def run_enhanced_backfill(self):
        """Run enhanced backfill on all series"""

        try:
            # Import the enhanced backfill script
            from final_enhanced_backfill import FinalEnhancedBackfill

            backfill = FinalEnhancedBackfill()

            for series_name in self.high_priority_series:
                print(f"\n   🔄 Processing {series_name}...")

                # Process the series
                backfill.process_all_difficult_series()

                print(f"   ✅ {series_name} backfill completed")

        except Exception as e:
            print(f"   ❌ Enhanced backfill failed: {e}")

if __name__ == "__main__":
    monitor = HighPriorityMonitor()
    monitor.run_with_monitoring()