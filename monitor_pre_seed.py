#!/usr/bin/env python3
"""
Monitoring TUI for manga cache pre-seeding process
Provides real-time monitoring with counts, API response times, and results feed
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

# Try to import curses for TUI, fallback to simple text if not available
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False


class PreSeedMonitor:
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
            'last_update': None
        }
        self.results_feed = []
        self.max_feed_lines = 20
        self.process = None
        self.monitoring_active = False

    def start_monitoring(self, script_path: str):
        """Start monitoring the pre-seeding process"""
        print("🚀 Starting pre-seeding monitoring...")
        print(f"📁 Script: {script_path}")
        print("=" * 60)

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

        if CURSES_AVAILABLE:
            curses.wrapper(self._run_curses_monitor)
        else:
            self._run_text_monitor()

    def _run_curses_monitor(self, stdscr):
        """Run curses-based TUI monitor"""
        curses.curs_set(0)
        stdscr.nodelay(1)

        while self.monitoring_active:
            # Check if process is still running
            if self.process.poll() is not None:
                self.monitoring_active = False
                break

            # Read output from process
            self._read_process_output()

            # Clear screen
            stdscr.clear()

            # Draw header
            self._draw_header(stdscr)

            # Draw statistics
            self._draw_stats(stdscr)

            # Draw results feed
            self._draw_feed(stdscr)

            # Refresh screen
            stdscr.refresh()

            # Check for quit key
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.monitoring_active = False
                break

            time.sleep(0.1)

        # Cleanup
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def _run_text_monitor(self):
        """Run simple text-based monitor"""
        print("\033[2J\033[H")  # Clear screen

        while self.monitoring_active:
            # Check if process is still running
            if self.process.poll() is not None:
                self.monitoring_active = False
                break

            # Read output from process
            self._read_process_output()

            # Clear screen and redraw
            print("\033[2J\033[H")  # Clear screen and move to top
            self._print_header()
            self._print_stats()
            self._print_feed()

            time.sleep(1)

        # Cleanup
        if self.process and self.process.poll() is None:
            self.process.terminate()

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
        self.results_feed.append(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")
        if len(self.results_feed) > self.max_feed_lines:
            self.results_feed.pop(0)

        # Parse statistics from output
        if "Processing:" in line:
            series_name = line.split("Processing:")[1].strip()
            self.stats['current_series'] = series_name

        elif "Cached" in line and "volumes for:" in line:
            # Extract volume count
            try:
                parts = line.split("Cached")
                if len(parts) > 1:
                    volume_part = parts[1].split("volumes")[0].strip()
                    volumes = int(volume_part)
                    self.stats['total_volumes'] += volumes
                    self.stats['successful_series'] += 1
            except (ValueError, IndexError):
                pass

        elif "Progress:" in line:
            # Extract progress information
            try:
                progress_part = line.split("Progress:")[1].strip()
                current, total = progress_part.split("/")
                self.stats['processed_series'] = int(current.strip())
                self.stats['total_series'] = int(total.split("(")[0].strip())
            except (ValueError, IndexError):
                pass

        elif "API Calls:" in line:
            try:
                calls_part = line.split("API Calls:")[1].strip()
                self.stats['api_calls'] = int(calls_part)
            except (ValueError, IndexError):
                pass

        self.stats['last_update'] = datetime.now()

    def _draw_header(self, stdscr):
        """Draw header in curses mode"""
        stdscr.addstr(0, 0, "🎯 MANGA CACHE PRE-SEEDING MONITOR", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * 60, curses.A_BOLD)
        stdscr.addstr(2, 0, f"Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        stdscr.addstr(3, 0, f"Last Update: {self.stats.get('last_update', 'N/A')}")
        stdscr.addstr(4, 0, "-" * 60)

    def _print_header(self):
        """Print header in text mode"""
        print("🎯 MANGA CACHE PRE-SEEDING MONITOR")
        print("=" * 60)
        print(f"Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Last Update: {self.stats.get('last_update', 'N/A')}")
        print("-" * 60)

    def _draw_stats(self, stdscr):
        """Draw statistics in curses mode"""
        row = 6
        elapsed = datetime.now() - self.stats['start_time']
        progress_pct = (self.stats['processed_series'] / max(self.stats['total_series'], 1)) * 100

        # Progress bar
        bar_width = 40
        filled = int((progress_pct / 100) * bar_width)
        bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
        stdscr.addstr(row, 0, f"📊 Progress: {bar} {progress_pct:.1f}%")
        row += 1

        # Main statistics
        stdscr.addstr(row, 0, f"📚 Series: {self.stats['processed_series']}/{self.stats['total_series']}")
        stdscr.addstr(row, 30, f"✅ Success: {self.stats['successful_series']}")
        row += 1

        stdscr.addstr(row, 0, f"📖 Volumes: {self.stats['total_volumes']}")
        stdscr.addstr(row, 30, f"❌ Failed: {self.stats['failed_series']}")
        row += 1

        stdscr.addstr(row, 0, f"🔌 API Calls: {self.stats['api_calls']}")
        stdscr.addstr(row, 30, f"⏱️  Elapsed: {str(elapsed).split('.')[0]}")
        row += 2

        # Current series
        if self.stats['current_series']:
            stdscr.addstr(row, 0, f"🔍 Current: {self.stats['current_series']}", curses.A_BOLD)
            row += 1

    def _print_stats(self):
        """Print statistics in text mode"""
        elapsed = datetime.now() - self.stats['start_time']
        progress_pct = (self.stats['processed_series'] / max(self.stats['total_series'], 1)) * 100

        # Progress bar
        bar_width = 40
        filled = int((progress_pct / 100) * bar_width)
        bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
        print(f"📊 Progress: {bar} {progress_pct:.1f}%")

        # Main statistics
        print(f"📚 Series: {self.stats['processed_series']}/{self.stats['total_series']} | "
              f"✅ Success: {self.stats['successful_series']} | "
              f"❌ Failed: {self.stats['failed_series']}")
        print(f"📖 Volumes: {self.stats['total_volumes']} | "
              f"🔌 API Calls: {self.stats['api_calls']} | "
              f"⏱️  Elapsed: {str(elapsed).split('.')[0]}")

        # Current series
        if self.stats['current_series']:
            print(f"\n🔍 Current: {self.stats['current_series']}")

    def _draw_feed(self, stdscr):
        """Draw results feed in curses mode"""
        row = 12
        stdscr.addstr(row, 0, "📰 RESULTS FEED:", curses.A_BOLD)
        row += 1
        stdscr.addstr(row, 0, "-" * 60)
        row += 1

        for i, line in enumerate(self.results_feed[-self.max_feed_lines:]):
            if row < curses.LINES - 2:
                stdscr.addstr(row, 0, line)
                row += 1

        # Instructions
        if row < curses.LINES - 1:
            stdscr.addstr(curses.LINES - 1, 0, "Press 'q' to quit", curses.A_BOLD)

    def _print_feed(self):
        """Print results feed in text mode"""
        print("\n📰 RESULTS FEED:")
        print("-" * 60)
        for line in self.results_feed[-self.max_feed_lines:]:
            print(line)

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring_active = False
        if self.process and self.process.poll() is None:
            self.process.terminate()


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 monitor_pre_seed.py <pre_seed_script.py>")
        sys.exit(1)

    script_path = sys.argv[1]

    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found")
        sys.exit(1)

    monitor = PreSeedMonitor()

    try:
        monitor.start_monitoring(script_path)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring interrupted by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"\n\n❌ Monitoring error: {e}")
        monitor.stop_monitoring()

    print("\n📊 Final Statistics:")
    print(f"   Total Series: {monitor.stats['total_series']}")
    print(f"   Processed: {monitor.stats['processed_series']}")
    print(f"   Successful: {monitor.stats['successful_series']}")
    print(f"   Failed: {monitor.stats['failed_series']}")
    print(f"   Total Volumes: {monitor.stats['total_volumes']}")
    print(f"   API Calls: {monitor.stats['api_calls']}")


if __name__ == "__main__":
    main()