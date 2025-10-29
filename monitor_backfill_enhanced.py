#!/usr/bin/env python3
"""
Enhanced Real-time TUI Monitor for BigQuery Metadata Backfill
- Uses ANSI rewrites instead of full screen clears
- Compatible with narrow Termux terminal windows
- Displays Pacific Time
"""
import time
import sys
import threading
from datetime import datetime
import pytz
from typing import Dict, Any
from bigquery_cache import BigQueryCache

class EnhancedBackfillMonitor:
    def __init__(self):
        self.cache = BigQueryCache()
        self.running = True
        self.last_update = None
        self.stats = {}
        self.display_lines = 0
        self.terminal_width = self.get_terminal_width()

    def get_terminal_width(self):
        """Get terminal width, default to 80 if cannot determine"""
        try:
            import shutil
            width = shutil.get_terminal_size().columns
            return max(width, 60)  # Minimum width for readability
        except:
            return 80  # Default width

    def get_pacific_time(self):
        """Get current time in Pacific Time"""
        try:
            pacific = pytz.timezone('America/Los_Angeles')
            return datetime.now(pacific).strftime('%Y-%m-%d %H:%M:%S %Z')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def clear_display(self):
        """Clear only the lines we've written using ANSI rewrites"""
        if self.display_lines > 0:
            # Move cursor up and clear lines
            print(f'\033[{self.display_lines}A\033[0J', end='')
        self.display_lines = 0

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
        """Get recent volume updates (last 5 for narrow terminals)"""
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
            LIMIT 5
            """

            job = self.cache.client.query(query)
            return list(job.result())

        except Exception as e:
            return []

    def display_progress_bar(self, percentage: float, width: int = None) -> str:
        """Create a progress bar string with dynamic width"""
        if width is None:
            width = min(30, self.terminal_width - 30)  # Dynamic width based on terminal
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    def display_stats(self, stats: Dict[str, Any]):
        """Display the statistics in a formatted TUI optimized for narrow terminals"""
        self.clear_display()

        lines = []

        # Header
        lines.append("╔" + "═" * (self.terminal_width - 2) + "╗")
        title = "BIGQUERY METADATA BACKFILL MONITOR"
        padding = (self.terminal_width - 2 - len(title)) // 2
        lines.append(f"║{' ' * padding}{title}{' ' * (self.terminal_width - 2 - len(title) - padding)}║")
        lines.append("╠" + "═" * (self.terminal_width - 2) + "╣")

        if 'error' in stats:
            error_msg = f"Error: {stats['error']}"
            lines.append(f"║ {error_msg:<{self.terminal_width-3}}║")
            lines.append("╚" + "═" * (self.terminal_width - 2) + "╝")
            self._print_lines(lines)
            return

        # Overall progress
        overall_bar = self.display_progress_bar(stats['overall_progress'])
        lines.append(f"║ Overall Progress: {overall_bar:<{self.terminal_width-20}} ║")
        lines.append("╠" + "═" * (self.terminal_width - 2) + "╣")

        # Individual progress bars
        progress_width = min(25, self.terminal_width - 25)
        lines.append(f"║ 📝 Descriptions:  {self.display_progress_bar(stats['descriptions_progress'], progress_width):<{self.terminal_width-20}} ║")
        lines.append(f"║ 📚 ISBNs:          {self.display_progress_bar(stats['isbns_progress'], progress_width):<{self.terminal_width-20}} ║")
        lines.append(f"║ 📅 Copyright Years: {self.display_progress_bar(stats['copyright_progress'], progress_width):<{self.terminal_width-20}} ║")
        lines.append(f"║ 🏢 Publishers:     {self.display_progress_bar(stats['publishers_progress'], progress_width):<{self.terminal_width-20}} ║")
        lines.append(f"║ 🖼️  Cover Images:   {self.display_progress_bar(stats['covers_progress'], progress_width):<{self.terminal_width-20}} ║")

        lines.append("╠" + "═" * (self.terminal_width - 2) + "╣")

        # Detailed counts - optimized for narrow terminals
        if self.terminal_width >= 70:
            lines.append(f"║ Total Volumes: {stats['total_volumes']:<4} | Missing Descriptions: {stats['missing_descriptions']:<3} ║")
            lines.append(f"║                | Missing ISBNs: {stats['missing_isbns']:<8} | Missing Years: {stats['missing_copyright_years']:<3} ║")
            lines.append(f"║                | Missing Publishers: {stats['missing_publishers']:<3} | Missing Covers: {stats['missing_covers']:<3} ║")
        else:
            # Compact format for very narrow terminals
            lines.append(f"║ Volumes: {stats['total_volumes']} | Missing: ║")
            lines.append(f"║ Desc:{stats['missing_descriptions']} ISBN:{stats['missing_isbns']} Year:{stats['missing_copyright_years']} ║")
            lines.append(f"║ Pub:{stats['missing_publishers']} Covers:{stats['missing_covers']} ║")

        lines.append("╠" + "═" * (self.terminal_width - 2) + "╣")

        # Recent updates
        recent = self.get_recent_updates()
        if recent:
            lines.append("║ Recent Updates: ║")
            for vol in recent:
                series = vol['series_name']
                if len(series) > self.terminal_width - 15:
                    series = series[:self.terminal_width - 18] + '...'
                lines.append(f"║ • {series} Vol {vol['volume_number']:<3} ║")

        lines.append("╠" + "═" * (self.terminal_width - 2) + "╣")

        # Footer with Pacific Time
        pacific_time = self.get_pacific_time()
        time_line = f"Last Updated: {pacific_time}"
        lines.append(f"║ {time_line:<{self.terminal_width-3}}║")
        lines.append(f"║ {'Press Ctrl+C to exit':<{self.terminal_width-3}}║")
        lines.append("╚" + "═" * (self.terminal_width - 2) + "╝")

        self._print_lines(lines)

    def _print_lines(self, lines):
        """Print lines and track how many we've displayed"""
        for line in lines:
            print(line)
        self.display_lines = len(lines)

    def run_monitor(self, refresh_interval: int = 5):
        """Run the enhanced real-time monitor"""
        print("Starting Enhanced BigQuery Backfill Monitor...")
        print("Press Ctrl+C to exit\n")

        try:
            while self.running:
                # Update terminal width in case it changed
                self.terminal_width = self.get_terminal_width()

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
    """Main function to run the enhanced monitor"""
    monitor = EnhancedBackfillMonitor()
    monitor.run_monitor(refresh_interval=5)

if __name__ == "__main__":
    main()