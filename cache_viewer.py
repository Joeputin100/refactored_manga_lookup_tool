#!/usr/bin/env python3
"""
Cache Viewer TUI for Manga Lookup Tool

A Textual-based terminal UI to browse cached series and volume information.
"""

import sys
import os
from typing import List, Dict, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, DataTable, Static, Label,
    ListView, ListItem, Button, Markdown
)
from textual.reactive import reactive
from textual.binding import Binding

from bigquery_cache import BigQueryCache


class SeriesListItem(ListItem):
    """List item for series selection"""
    def __init__(self, series_name: str) -> None:
        super().__init__()
        self.series_name = series_name

    def render(self) -> str:
        """Render the series name"""
        return self.series_name


class VolumeListItem(ListItem):
    """List item for volume selection"""
    def __init__(self, volume_info: Dict) -> None:
        super().__init__()
        self.volume_info = volume_info

    def render(self) -> str:
        """Render the volume title"""
        volume_number = self.volume_info.get('volume_number', 'Unknown')
        book_title = self.volume_info.get('book_title', 'Unknown Title')
        return f"Volume {volume_number}: {book_title}"


class CacheViewerApp(App):
    """Main TUI application for cache viewing"""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr;
    }

    /* Series List Panel
    #series-list-panel {
        border: solid $accent;
        padding: 1;
    }

    Series Detail Panel
    #series-detail-panel {
        border: solid $accent;
        padding: 1;
    }

    Volume List Panel
    #volume-list-panel {
        border: solid $accent;
        padding: 1;
    }

    Volume Detail Panel
    #volume-detail-panel {
        border: solid $accent;
        padding: 1;
    } */

    .panel-title {
        text-style: bold;
        background: $accent;
        color: $surface;
        padding: 1;
        margin-bottom: 1;
    }

    .detail-content {
        padding: 1;
        height: 100%;
    }

    .series-list {
        height: 100%;
    }

    .volume-list {
        height: 100%;
    }

    .loading {
        text-align: center;
        padding: 2;
    }

    .error {
        background: $error;
        color: $surface;
        padding: 1;
    }

    .success {
        background: $success;
        color: $surface;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh Cache", show=True),
        Binding("ctrl+s", "focus_panel('series_list')", "Focus Series List", show=False),
        Binding("ctrl+d", "focus_panel('series_detail')", "Focus Series Detail", show=False),
        Binding("ctrl+v", "focus_panel('volume_list')", "Focus Volume List", show=False),
        Binding("ctrl+b", "focus_panel('volume_detail')", "Focus Volume Detail", show=False),
    ]

    selected_series = reactive(None)
    selected_volume = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.cache = None
        self.series_list = []
        self.volumes_cache = {}

    def compose(self) -> ComposeResult:
        """Create the app layout"""
        yield Header()

        # Series List Panel (Top Left)
        with Vertical(id="series-list-panel"):
            yield Label("📚 Series List", classes="panel-title")
            yield ListView(id="series-list-view", classes="series-list")

        # Series Detail Panel (Top Right)
        with Vertical(id="series-detail-panel"):
            yield Label("📖 Series Details", classes="panel-title")
            yield Static("Select a series to view details", id="series-detail-content", classes="detail-content")

        # Volume List Panel (Bottom Left)
        with Vertical(id="volume-list-panel"):
            yield Label("📚 Volumes", classes="panel-title")
            yield ListView(id="volume-list-view", classes="volume-list")

        # Volume Detail Panel (Bottom Right)
        with Vertical(id="volume-detail-panel"):
            yield Label("📖 Volume Details", classes="panel-title")
            yield Static("Select a volume to view details", id="volume-detail-content", classes="detail-content")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app"""
        self.title = "Manga Cache Viewer"
        self.sub_title = "Browse cached series and volume information"

        # Initialize cache
        try:
            self.cache = BigQueryCache()
            if not self.cache.enabled:
                self.show_error("BigQuery cache is not enabled")
                return

            self.load_series_list()

        except Exception as e:
            self.show_error(f"Failed to initialize cache: {e}")

    def load_series_list(self) -> None:
        """Load the list of series from cache"""
        try:
            series_list_view = self.query_one("#series-list-view", ListView)
            series_list_view.clear()

            # Show loading message
            self.query_one("#series-detail-content", Static).update("Loading series list...")

            # Get all series from cache
            query = """
            SELECT DISTINCT series_name
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            ORDER BY series_name
            """
            query_job = self.cache.client.query(query)
            self.series_list = [row['series_name'] for row in query_job]

            # Populate series list
            for series_name in self.series_list:
                series_list_view.append(SeriesListItem(series_name))

            if self.series_list:
                self.query_one("#series-detail-content", Static).update(
                    f"Found {len(self.series_list)} series in cache. Select one to view details."
                )
            else:
                self.query_one("#series-detail-content", Static).update(
                    "No series found in cache."
                )

        except Exception as e:
            self.show_error(f"Failed to load series list: {e}")

    def load_series_detail(self, series_name: str) -> None:
        """Load detailed information for a series"""
        try:
            # Get series info from cache
            series_info = self.cache.get_series_info(series_name)

            if not series_info:
                self.query_one("#series-detail-content", Static).update(
                    f"No detailed information found for '{series_name}'"
                )
                return

            # Count actual volumes for this series
            volume_query = f"""
            SELECT COUNT(*) as volume_count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """
            volume_job = self.cache.client.query(volume_query)
            actual_volume_count = list(volume_job)[0]['volume_count']

            # Format series details
            detail_text = f"""
## {series_info.get('corrected_series_name', series_name)}

**Authors:** {', '.join(series_info.get('authors', []))}
**Total Volumes:** {actual_volume_count}
**Publisher:** {series_info.get('publisher', 'Unknown')}
**Status:** {series_info.get('status', 'Unknown')}
**Genres:** {', '.join(series_info.get('genres', []))}

**Summary:**
{series_info.get('summary', 'No summary available.')}

**Alternative Titles:**
{', '.join(series_info.get('alternative_titles', [])) or 'None'}

**Spinoffs/Alternate Editions:**
{', '.join(series_info.get('spinoff_series', [])) or 'None'}

**Adaptations:**
{', '.join(series_info.get('adaptations', [])) or 'None'}
            """

            self.query_one("#series-detail-content", Static).update(detail_text)

            # Load volumes for this series
            self.load_volumes_for_series(series_name)

        except Exception as e:
            self.show_error(f"Failed to load series details: {e}")

    def load_volumes_for_series(self, series_name: str) -> None:
        """Load volumes for the selected series"""
        try:
            volume_list_view = self.query_one("#volume-list-view", ListView)
            volume_list_view.clear()

            # Clear volume detail
            self.query_one("#volume-detail-content", Static).update(
                "Select a volume to view details"
            )

            # Get volumes from cache
            query = f"""
            SELECT *
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            ORDER BY volume_number
            """
            query_job = self.cache.client.query(query)
            volumes = [dict(row) for row in query_job]

            # Store volumes in cache
            self.volumes_cache[series_name] = volumes

            # Populate volume list
            for volume in volumes:
                volume_list_view.append(VolumeListItem(volume))

            if volumes:
                self.query_one("#volume-detail-content", Static).update(
                    f"Found {len(volumes)} volumes. Select one to view details."
                )
            else:
                self.query_one("#volume-detail-content", Static).update(
                    "No volumes found for this series."
                )

        except Exception as e:
            self.show_error(f"Failed to load volumes: {e}")

    def load_volume_detail(self, volume_info: Dict) -> None:
        """Load detailed information for a volume"""
        try:
            detail_text = f"""
## {volume_info.get('book_title', 'Unknown Title')}

**Volume Number:** {volume_info.get('volume_number', 'Unknown')}
**Series:** {volume_info.get('series_name', 'Unknown')}
**Authors:** {', '.join(volume_info.get('authors', []))}
**Publisher:** {volume_info.get('publisher_name', 'Unknown')}
**Copyright Year:** {volume_info.get('copyright_year', 'Unknown')}
**ISBN-13:** {volume_info.get('isbn_13', 'Unknown')}
**MSRP:** ${volume_info.get('msrp_cost', 'Unknown')}

**Genres:**
{', '.join(volume_info.get('genres', [])) or 'None'}

**Physical Description:**
{volume_info.get('physical_description', 'Not available')}

**Description:**
{volume_info.get('description', 'No description available.')}
            """

            self.query_one("#volume-detail-content", Static).update(detail_text)

        except Exception as e:
            self.show_error(f"Failed to load volume details: {e}")

    @on(ListView.Selected, "#series-list-view")
    def on_series_selected(self, event: ListView.Selected) -> None:
        """Handle series selection"""
        if isinstance(event.item, SeriesListItem):
            self.selected_series = event.item.series_name
            self.load_series_detail(self.selected_series)

    @on(ListView.Selected, "#volume-list-view")
    def on_volume_selected(self, event: ListView.Selected) -> None:
        """Handle volume selection"""
        if isinstance(event.item, VolumeListItem):
            self.selected_volume = event.item.volume_info
            self.load_volume_detail(self.selected_volume)

    def action_refresh(self) -> None:
        """Refresh the cache data"""
        self.load_series_list()
        if self.selected_series:
            self.load_series_detail(self.selected_series)

    def show_error(self, message: str) -> None:
        """Display an error message"""
        self.query_one("#series-detail-content", Static).update(
            f"❌ {message}"
        )

    def show_success(self, message: str) -> None:
        """Display a success message"""
        self.query_one("#series-detail-content", Static).update(
            f"✅ {message}"
        )


def main():
    """Main entry point"""
    try:
        app = CacheViewerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting cache viewer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()