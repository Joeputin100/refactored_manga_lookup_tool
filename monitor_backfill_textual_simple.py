#!/usr/bin/env python3
"""
Simple Textual TUI Monitor for BigQuery Metadata Backfill
- Uses Textual framework for robust terminal UI
- Real-time updates with proper screen management
- Shows Pacific Time, update age, and field information
"""
import time
from datetime import datetime
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ProgressBar, Label
from textual.reactive import reactive

from bigquery_cache import BigQueryCache

class BackfillStats:
    """Container for backfill statistics"""
    def __init__(self):
        self.cache = BigQueryCache()

    def get_stats(self) -> Dict[str, Any]:
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
        """Get recent volume updates with timestamps and field information"""
        try:
            query = """
            SELECT
                series_name,
                volume_number,
                description,
                isbn_13,
                copyright_year,
                publisher_name,
                last_updated
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE description IS NOT NULL AND description != ''
            ORDER BY last_updated DESC
            LIMIT 5
            """

            job = self.cache.client.query(query)
            results = list(job.result())

            # Calculate update age and determine which fields were updated
            recent_updates = []
            for vol in results:
                # Calculate age in seconds
                if vol['last_updated']:
                    age_seconds = int((datetime.now() - vol['last_updated']).total_seconds())
                else:
                    age_seconds = 999999  # Large number for unknown

                # Determine which fields were updated
                updated_fields = []
                if vol['description'] and vol['description'].strip():
                    updated_fields.append("desc")
                if vol['isbn_13'] and vol['isbn_13'].strip():
                    updated_fields.append("isbn")
                if vol['copyright_year']:
                    updated_fields.append("year")
                if vol['publisher_name'] and vol['publisher_name'].strip():
                    updated_fields.append("pub")

                recent_updates.append({
                    'series_name': vol['series_name'],
                    'volume_number': vol['volume_number'],
                    'age_seconds': age_seconds,
                    'updated_fields': updated_fields
                })

            return recent_updates

        except Exception as e:
            return []

class BackfillMonitorApp(App):
    """Textual app for monitoring BigQuery backfill"""

    CSS = """
    Screen {
        align: center middle;
    }

    Container {
        width: 80%;
        height: 90%;
        border: solid $accent;
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    .section {
        margin: 1 0;
    }

    ProgressBar {
        width: 100%;
        height: 1;
        margin: 1 0;
    }

    Label {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.stats_provider = BackfillStats()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with Container():
            yield Label("BIGQUERY METADATA BACKFILL MONITOR", classes="title")

            with Vertical(classes="section"):
                yield Label("Overall Progress:", id="overall-label")
                yield ProgressBar(total=100, id="overall-progress")

            with Vertical(classes="section"):
                yield Label("Individual Progress:")
                yield Label("📝 Descriptions:", id="desc-label")
                yield ProgressBar(total=100, id="desc-progress")
                yield Label("📚 ISBNs:", id="isbn-label")
                yield ProgressBar(total=100, id="isbn-progress")
                yield Label("📅 Copyright Years:", id="year-label")
                yield ProgressBar(total=100, id="year-progress")
                yield Label("🏢 Publishers:", id="pub-label")
                yield ProgressBar(total=100, id="pub-progress")
                yield Label("🖼️ Cover Images:", id="cover-label")
                yield ProgressBar(total=100, id="cover-progress")

            with Vertical(classes="section"):
                yield Label("Statistics:", id="stats-label")

            with Vertical(classes="section"):
                yield Label("Recent Updates:", id="updates-label")

    def on_mount(self) -> None:
        """Start the update timer when app mounts"""
        self.set_interval(5, self.update_data)
        self.update_data()

    def update_data(self) -> None:
        """Update all data from BigQuery"""
        try:
            # Get stats and updates
            stats = self.stats_provider.get_stats()
            updates = self.stats_provider.get_recent_updates()

            # Update progress bars
            if 'error' not in stats:
                self.query_one("#overall-progress", ProgressBar).update(progress=stats['overall_progress'])
                self.query_one("#overall-label").update(f"Overall Progress: {stats['overall_progress']:.1f}%")

                self.query_one("#desc-progress", ProgressBar).update(progress=stats['descriptions_progress'])
                self.query_one("#desc-label").update(f"📝 Descriptions: {stats['descriptions_progress']:.1f}%")

                self.query_one("#isbn-progress", ProgressBar).update(progress=stats['isbns_progress'])
                self.query_one("#isbn-label").update(f"📚 ISBNs: {stats['isbns_progress']:.1f}%")

                self.query_one("#year-progress", ProgressBar).update(progress=stats['copyright_progress'])
                self.query_one("#year-label").update(f"📅 Copyright Years: {stats['copyright_progress']:.1f}%")

                self.query_one("#pub-progress", ProgressBar).update(progress=stats['publishers_progress'])
                self.query_one("#pub-label").update(f"🏢 Publishers: {stats['publishers_progress']:.1f}%")

                self.query_one("#cover-progress", ProgressBar).update(progress=stats['covers_progress'])
                self.query_one("#cover-label").update(f"🖼️ Cover Images: {stats['covers_progress']:.1f}%")

                # Update stats
                stats_text = f"""
Total Volumes: {stats['total_volumes']}
Missing Descriptions: {stats['missing_descriptions']}
Missing ISBNs: {stats['missing_isbns']}
Missing Copyright Years: {stats['missing_copyright_years']}
Missing Publishers: {stats['missing_publishers']}
Missing Covers: {stats['missing_covers']}
                """.strip()
                self.query_one("#stats-label").update(f"Statistics:\n{stats_text}")

                # Update recent updates
                if updates:
                    updates_text = []
                    for vol in updates:
                        series = vol['series_name']
                        if len(series) > 20:
                            series = series[:17] + '...'

                        fields_str = " ".join(vol['updated_fields'])
                        age_str = self._format_age(vol['age_seconds'])
                        updates_text.append(f"• {series} Vol {vol['volume_number']} [{fields_str}] {age_str} ago")

                    self.query_one("#updates-label").update(f"Recent Updates:\n" + "\n".join(updates_text))
                else:
                    self.query_one("#updates-label").update("Recent Updates: No recent updates")

            else:
                # Handle error
                self.query_one("#stats-label").update(f"Error: {stats['error']}")

            # Footer doesn't have an update method, so we'll just update the stats label with time
            current_stats = self.query_one("#stats-label").renderable
            if isinstance(current_stats, str):
                self.query_one("#stats-label").update(f"{current_stats}\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")

        except Exception as e:
            self.query_one("#stats-label").update(f"Update Error: {str(e)}")

    def _format_age(self, seconds: int) -> str:
        """Format age in seconds to human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m"
        elif seconds < 86400:
            return f"{seconds//3600}h"
        else:
            return f"{seconds//86400}d"

def main():
    """Main function to run the Textual app"""
    app = BackfillMonitorApp()
    app.run()

if __name__ == "__main__":
    main()