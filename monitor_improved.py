#!/usr/bin/env python3
"""
Improved monitoring TUI for manga cache pre-seeding process
Provides real-time monitoring with continuous ANSI rewrites
"""

import os
import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import subprocess
import select
import signal


class ImprovedPreSeedMonitor:
    def __init__(self):
        self.stats = {
            'total_series': 0,
            'processed_series': 0,
            'successful_series': 0,
            'failed_series': 0,
            'total_volumes': 0,
            'start_time': None,
            'api_calls': 0,
            'cache_hits': 0,
            'current_series': None,
            'last_update': None,
            'elapsed_time': '00:00:00',
            'estimated_remaining': '--:--:--'
        }
        self.results_feed = []
        self.max_feed_lines = 15
        self.process = None
        self.monitoring_active = False
        self.last_screen_lines = 0

    def clear_screen(self):
        """Clear screen using ANSI escape sequences"""
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()

    def move_cursor(self, row, col):
        """Move cursor to specific position"""
        sys.stdout.write(f'\033[{row};{col}H')
        sys.stdout.flush()

    def start_monitoring(self, script_path: str):
        """Start monitoring the pre-seeding process"""
        print("🚀 Starting improved pre-seeding monitor...")
        print(f"📁 Script: {script_path}")
        print("=" * 60)
        time.sleep(2)

        # Start the pre-seeding process
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        self.monitoring_active = True
        self.stats['start_time'] = datetime.now()

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            self._run_continuous_monitor()
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring interrupted by user")
            self.stop_monitoring()
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")
            self.stop_monitoring()

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print("\n\n🛑 Received interrupt signal, stopping monitor...")
        self.stop_monitoring()

    def _run_continuous_monitor(self):
        """Run continuous monitor with ANSI rewrites"""
        last_update_time = time.time()

        while self.monitoring_active:
            # Check if process is still running
            if self.process.poll() is not None:
                self.monitoring_active = False
                break

            # Read output from process
            self._read_process_output()

            # Update elapsed time
            self._update_timing()

            # Redraw the screen every 0.5 seconds or when we have new data
            current_time = time.time()
            if current_time - last_update_time >= 0.5 or self.stats['last_update']:
                self._draw_screen()
                last_update_time = current_time
                self.stats['last_update'] = None  # Reset update flag

            time.sleep(0.1)

        # Final screen update
        self._draw_screen()
        print("\n\n📊 Final statistics displayed above")

    def _read_process_output(self):
        """Read output from the pre-seeding process"""
        try:
            # Use select to check if there's data available without blocking
            ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
            if ready:
                line = self.process.stdout.readline()
                if line:
                    self._parse_output_line(line.strip())
        except (IOError, ValueError):
            pass

    def _parse_output_line(self, line: str):
        """Parse output line and update statistics"""
        # Add to results feed
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.results_feed.append(f"[{timestamp}] {line}")
        if len(self.results_feed) > self.max_feed_lines:
            self.results_feed.pop(0)

        # Parse statistics from output
        if "Processing:" in line:
            series_name = line.split("Processing:")[1].strip()
            self.stats['current_series'] = series_name
            self.stats['last_update'] = datetime.now()

        elif "Cached" in line and "volumes for:" in line:
            # Extract volume count
            try:
                parts = line.split("Cached")
                if len(parts) > 1:
                    volume_part = parts[1].split("volumes")[0].strip()
                    volumes = int(volume_part)
                    self.stats['total_volumes'] += volumes
                    self.stats['successful_series'] += 1
                    self.stats['last_update'] = datetime.now()
            except (ValueError, IndexError):
                pass

        elif "Progress:" in line:
            # Extract progress information
            try:
                progress_part = line.split("Progress:")[1].strip()
                current, total = progress_part.split("/")
                self.stats['processed_series'] = int(current.strip())
                self.stats['total_series'] = int(total.split("(")[0].strip())
                self.stats['last_update'] = datetime.now()
            except (ValueError, IndexError):
                pass

        elif "API Calls:" in line:
            try:
                calls_part = line.split("API Calls:")[1].strip()
                self.stats['api_calls'] = int(calls_part)
                self.stats['last_update'] = datetime.now()
            except (ValueError, IndexError):
                pass

        elif "Success:" in line and "Failed:" in line:
            try:
                success_part = line.split("Success:")[1].split("|")[0].strip()
                failed_part = line.split("Failed:")[1].strip()
                self.stats['successful_series'] = int(success_part)
                self.stats['failed_series'] = int(failed_part)
                self.stats['last_update'] = datetime.now()
            except (ValueError, IndexError):
                pass

    def _update_timing(self):
        """Update elapsed time and estimated remaining time"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            self.stats['elapsed_time'] = str(elapsed).split('.')[0]

            # Calculate estimated remaining time
            if self.stats['processed_series'] > 0 and self.stats['total_series'] > 0:
                progress = self.stats['processed_series'] / self.stats['total_series']
                if progress > 0:
                    total_estimated = elapsed.total_seconds() / progress
                    remaining_seconds = total_estimated - elapsed.total_seconds()
                    if remaining_seconds > 0:
                        remaining = timedelta(seconds=int(remaining_seconds))
                        self.stats['estimated_remaining'] = str(remaining).split('.')[0]

    def _draw_screen(self):
        """Draw the complete monitoring screen"""
        # Clear screen and move to top
        self.clear_screen()

        # Header
        print("🎯 IMPROVED MANGA CACHE PRE-SEEDING MONITOR")
        print("=" * 60)
        print(f"Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S') if self.stats['start_time'] else 'N/A'}")
        print("-" * 60)

        # Progress section
        self._draw_progress_section()

        # Statistics section
        self._draw_statistics_section()

        # Current activity
        self._draw_current_activity()

        # Results feed
        self._draw_results_feed()

        # Footer
        print("-" * 60)
        print("Press Ctrl+C to stop monitoring")

        sys.stdout.flush()

    def _draw_progress_section(self):
        """Draw progress bar and timing information"""
        progress_pct = (self.stats['processed_series'] / max(self.stats['total_series'], 1)) * 100

        # Progress bar
        bar_width = 50
        filled = int((progress_pct / 100) * bar_width)
        bar = "[" + "█" * filled + "░" * (bar_width - filled) + "]"

        print(f"📊 Progress: {bar} {progress_pct:.1f}%")
        print(f"   {self.stats['processed_series']}/{self.stats['total_series']} series processed")

        # Timing information
        print(f"⏱️  Elapsed: {self.stats['elapsed_time']} | Estimated Remaining: {self.stats['estimated_remaining']}")
        print()

    def _draw_statistics_section(self):
        """Draw statistics in a formatted table"""
        print("📈 STATISTICS:")
        print(f"   ✅ Successful: {self.stats['successful_series']:3d} | ❌ Failed: {self.stats['failed_series']:3d}")
        print(f"   📚 Volumes: {self.stats['total_volumes']:4d} | 🔌 API Calls: {self.stats['api_calls']:4d}")
        print()

    def _draw_current_activity(self):
        """Draw current activity section"""
        if self.stats['current_series']:
            print(f"🔍 CURRENTLY PROCESSING: {self.stats['current_series']}")
        else:
            print("🔍 CURRENTLY PROCESSING: Waiting for first series...")
        print()

    def _draw_results_feed(self):
        """Draw results feed section"""
        print("📰 RECENT ACTIVITY:")
        print("-" * 60)

        if not self.results_feed:
            print("   Waiting for activity...")
        else:
            for line in self.results_feed[-self.max_feed_lines:]:
                print(f"   {line}")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring_active = False
        if self.process and self.process.poll() is None:
            print("\n🛑 Stopping pre-seeding process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️ Process did not terminate gracefully, forcing...")
                self.process.kill()

    def print_final_summary(self):
        """Print final summary after monitoring ends"""
        print("\n" + "=" * 60)
        print("🎉 MONITORING COMPLETE!")
        print("=" * 60)

        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total Series: {self.stats['total_series']}")
        print(f"   Processed: {self.stats['processed_series']}")
        print(f"   Successful: {self.stats['successful_series']}")
        print(f"   Failed: {self.stats['failed_series']}")
        print(f"   Total Volumes: {self.stats['total_volumes']}")
        print(f"   API Calls: {self.stats['api_calls']}")
        print(f"   Total Time: {self.stats['elapsed_time']}")


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 monitor_improved.py <pre_seed_script.py>")
        sys.exit(1)

    script_path = sys.argv[1]

    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found")
        sys.exit(1)

    monitor = ImprovedPreSeedMonitor()

    try:
        monitor.start_monitoring(script_path)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring interrupted by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"\n\n❌ Monitoring error: {e}")
        monitor.stop_monitoring()

    monitor.print_final_summary()


if __name__ == "__main__":
    main()