#!/usr/bin/env python3
"""
Manga Lookup Tool - Streamlit Web App

A web interface for the manga lookup tool with progress tracking,
real-time updates, and streamlined UI.

NOTE: This app is designed to run on Streamlit Cloud only.
Local execution requires Streamlit installation.
"""

# Check if Streamlit is available - if not, provide helpful error message
import sys

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import html
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import cover fetchers
from mal_cover_fetcher import MALCoverFetcher

# Import existing core logic
from manga_lookup import (
    BookInfo,
    DeepSeekAPI,
    GoogleBooksAPI,
    ProjectState,
    generate_sequential_barcodes,
    parse_volume_range,
    process_book_data,
)
from mangadex_cover_fetcher import MangaDexCoverFetcher

# Import MARC exporter
from marc_exporter import export_books_to_marc


def initialize_session_state():
    """Initialize session state variables"""
    if "series_entries" not in st.session_state:
        st.session_state.series_entries = []
    if "confirmed_series" not in st.session_state:
        st.session_state.confirmed_series = []
    if "all_books" not in st.session_state:
        st.session_state.all_books = []
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = {
            "is_processing": False,
            "current_series": None,
            "current_volume": None,
            "progress": 0,
            "total_volumes": 0,
            "start_time": None,
        }
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState()
    if "pending_series_name" not in st.session_state:
        st.session_state.pending_series_name = None
    if "selected_series" not in st.session_state:
        st.session_state.selected_series = None
    if "original_series_name" not in st.session_state:
        st.session_state.original_series_name = None
    if "start_barcode" not in st.session_state:
        st.session_state.start_barcode = "T000001"
    # Reset processing state if stuck
    if (
        st.session_state.processing_state.get("is_processing", False)
        and not st.session_state.all_books
    ):
        st.session_state.processing_state["is_processing"] = False


def fetch_cover_for_book(book: BookInfo) -> str | None:
    """Fetch cover image URL, prioritizing English editions"""

    # Try Google Books first for English covers
    try:
        google_api = GoogleBooksAPI()
        cover_url = google_api.get_cover_image_url(
            book.isbn_13,
            st.session_state.project_state,
        )
        if cover_url:
            return cover_url
    except Exception:
        pass

    # Fallback to MAL
    try:
        mal_fetcher = MALCoverFetcher()
        cover_url = mal_fetcher.fetch_cover(book.series_name, book.volume_number)
        if cover_url:
            return cover_url
    except Exception:
        pass

    # Fallback to MangaDex
    try:
        mangadex_fetcher = MangaDexCoverFetcher()
        cover_url = mangadex_fetcher.fetch_cover(book.series_name, book.volume_number)
        if cover_url:
            return cover_url
    except Exception:
        pass

    return None


def process_single_volume(series_name, volume, project_state):
    """Process a single volume and return book info"""
    try:
        deepseek_api = DeepSeekAPI()
        google_books_api = GoogleBooksAPI()
        book_data = deepseek_api.get_book_info(series_name, volume, project_state)
        if book_data:
            book = process_book_data(book_data, volume, google_books_api, project_state)
            return book, None
        return None, f"Volume {volume} not found"
    except Exception as e:
        return None, f"Error processing volume {volume}: {e!s}"


def display_duck_animation():

    st.image("https://media.giphy.com/media/WzA4Vj6V8UOEX10jMj/giphy.gif")


def calculate_elapsed_time(start_time):
    """Calculate elapsed time"""
    if not start_time:
        return "0 seconds"

    elapsed = time.time() - start_time
    if elapsed < 60:
        return f"{int(elapsed)} seconds"
    if elapsed < 3600:
        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds}s"
    hours = int(elapsed / 3600)
    minutes = int((elapsed % 3600) / 60)
    return f"{hours}h {minutes}m"


def display_progress_section():
    """Display progress tracking"""
    state = st.session_state.processing_state
    progress = state["progress"]
    total = state["total_volumes"]

    if progress == 0:
        st.write("Preparing to lookup manga volumes...")
    else:
        st.write(f"Processing {progress} of {total} volumes")
        if state["current_series"]:
            st.info(
                f"Current: {state['current_series']} - Volume {state['current_volume']}",
            )

    display_duck_animation()
    st.caption("Please wait...")


def process_series(series_name: str, volume_range: str, start_barcode: str):
    """Process a manga series with multiple volumes"""
    try:
        # Parse volume range
        volumes = parse_volume_range(volume_range)
        if not volumes:
            st.error(f"Invalid volume range: {volume_range}")
            return

        # Initialize processing state
        st.session_state.processing_state = {
            "is_processing": True,
            "current_series": series_name,
            "current_volume": None,
            "progress": 0,
            "total_volumes": len(volumes),
            "start_time": time.time(),
        }

        # Generate barcodes
        barcodes = generate_sequential_barcodes(start_barcode, len(volumes))

        # Process volumes concurrently
        books = []
        errors = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_volume = {
                executor.submit(
                    process_single_volume,
                    series_name,
                    volume,
                    st.session_state.project_state,
                ): volume
                for volume in volumes
            }

            # Process completed tasks
            for future in as_completed(future_to_volume):
                volume = future_to_volume[future]
                try:
                    book, error = future.result()
                    if book:
                        # Assign barcode
                        book.barcode = barcodes[len(books)]
                        books.append(book)
                    elif error:
                        errors.append(error)

                    # Update progress
                    st.session_state.processing_state["progress"] += 1
                    st.session_state.processing_state["current_volume"] = volume

                except Exception as e:
                    errors.append(f"Volume {volume}: {e!s}")

        # Update session state
        st.session_state.all_books.extend(books)
        st.session_state.processing_state["is_processing"] = False

        # Show results
        if books:
            st.success(f"Successfully processed {len(books)} volumes")
            if errors:
                st.warning(f"{len(errors)} volumes had errors: {', '.join(errors)}")
        else:
            st.error("No volumes were successfully processed")

    except Exception as e:
        st.error(f"Error processing series: {e!s}")
        st.session_state.processing_state["is_processing"] = False


def series_input_form():
    """Display series input form"""
    st.header("Add Manga Series")

    with st.form("series_form"):
        series_name = st.text_input(
            "Series Name",
            placeholder="e.g., Naruto, One Piece, Attack on Titan",
        )

        volume_range = st.text_input(
            "Volume Range",
            placeholder="e.g., 1-10, 1,3,5,7, 1-5,8,10",
        )

        start_barcode = st.text_input(
            "Starting Barcode",
            value=st.session_state.start_barcode,
            placeholder="e.g., T000001",
        )

        submitted = st.form_submit_button("Add Series")

        if submitted:
            if not series_name:
                st.error("Please enter a series name")
                return
            if not volume_range:
                st.error("Please enter a volume range")
                return

            # Add to pending series
            st.session_state.pending_series_name = series_name
            st.session_state.original_series_name = series_name
            st.session_state.start_barcode = start_barcode

            # Parse volumes to validate
            volumes = parse_volume_range(volume_range)
            if not volumes:
                st.error("Invalid volume range format")
                return

            # Add to series entries
            st.session_state.series_entries.append({
                "name": series_name,
                "volume_range": volume_range,
                "volumes": volumes,
                "start_barcode": start_barcode,
            })

            st.success(f"Added {series_name} with {len(volumes)} volumes")


def confirm_single_series():
    """Confirm series name before processing"""
    if st.session_state.pending_series_name:
        st.header("Confirm Series Name")

        st.write(f"**Original name:** {st.session_state.pending_series_name}")

        # Show potential matches from project state
        similar_series = st.session_state.project_state.find_similar_series(
            st.session_state.pending_series_name
        )

        if similar_series:
            st.write("**Similar series found:**")
            for series in similar_series[:5]:  # Show top 5
                if st.button(f"Use: {series}"):
                    st.session_state.selected_series = series
                    st.session_state.pending_series_name = None
                    st.rerun()

        # Manual entry option
        st.write("**Or enter custom name:**")
        custom_name = st.text_input(
            "Custom Series Name",
            value=st.session_state.pending_series_name,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use Original Name"):
                st.session_state.selected_series = st.session_state.pending_series_name
                st.session_state.pending_series_name = None
                st.rerun()
        with col2:
            if st.button("Use Custom Name") and custom_name:
                st.session_state.selected_series = custom_name
                st.session_state.pending_series_name = None
                st.rerun()

        if st.button("Cancel"):
            st.session_state.pending_series_name = None
            st.rerun()


def display_results():
    """Display processing results"""
    if not st.session_state.all_books:
        return

    st.header("Results")

    # Summary statistics
    total_books = len(st.session_state.all_books)
    unique_series = len(set(book.series_name for book in st.session_state.all_books))

    st.write(f"**Total volumes processed:** {total_books}")
    st.write(f"**Unique series:** {unique_series}")

    # Export options
    st.subheader("Export Options")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export to MARC"):
            try:
                export_books_to_marc(st.session_state.all_books, "manga_export.mrc")
                st.success("MARC file exported successfully!")
                st.download_button(
                    "Download MARC File",
                    data=open("manga_export.mrc", "rb").read(),
                    file_name="manga_export.mrc",
                    mime="application/marc",
                )
            except Exception as e:
                st.error(f"Error exporting MARC: {e!s}")

    with col2:
        if st.button("Generate Labels"):
            try:
                from label_generator import generate_pdf_sheet

                # Convert books to label data
                label_data = []
                for i, book in enumerate(st.session_state.all_books):
                    label_data.append({
                        "Title": book.book_title or f"{book.series_name} Vol. {book.volume_number}",
                        "Author's Name": book.authors[0] if book.authors else "Unknown",
                        "Publication Year": str(book.copyright_year) if book.copyright_year else "",
                        "Series Title": book.series_name,
                        "Series Volume": str(book.volume_number),
                        "Call Number": f"Manga {book.barcode}",
                        "Holdings Barcode": book.barcode,
                        "spine_label_id": chr(65 + i % 26),  # A, B, C, etc.
                        "clipart": "None",
                    })

                pdf_data = generate_pdf_sheet(label_data)
                st.success("Labels generated successfully!")
                st.download_button(
                    "Download Labels PDF",
                    data=pdf_data,
                    file_name="manga_labels.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Error generating labels: {e!s}")

    # Book details
    st.subheader("Book Details")

    for book in st.session_state.all_books:
        with st.expander(f"{book.series_name} - Volume {book.volume_number}"):
            col1, col2 = st.columns([1, 2])

            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=150)
                else:
                    st.write("No cover image")

            with col2:
                st.write(f"**Title:** {book.book_title}")
                st.write(f"**Authors:** {', '.join(book.authors) if book.authors else 'Unknown'}")
                st.write(f"**Publisher:** {book.publisher_name or 'Unknown'}")
                st.write(f"**Year:** {book.copyright_year or 'Unknown'}")
                st.write(f"**ISBN:** {book.isbn_13 or 'Unknown'}")
                st.write(f"**Barcode:** {book.barcode}")

                if book.description:
                    st.write(f"**Description:** {book.description[:200]}...")

                if book.genres:
                    st.write(f"**Genres:** {', '.join(book.genres)}")


def main():
    """Main application function"""
    st.set_page_config(
        page_title="Manga Lookup Tool",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Main title
    st.title("📚 Manga Lookup Tool")
    st.markdown("---")

    # Check if processing is in progress
    if st.session_state.processing_state.get("is_processing", False):
        display_progress_section()
        return

    # Show series confirmation if needed
    if st.session_state.pending_series_name:
        confirm_single_series()
        return

    # Process selected series
    if st.session_state.selected_series:
        # Find the matching series entry
        series_entry = None
        for entry in st.session_state.series_entries:
            if entry["name"] == st.session_state.original_series_name:
                series_entry = entry
                break

        if series_entry:
            st.info(f"Processing: {st.session_state.selected_series}")
            process_series(
                st.session_state.selected_series,
                series_entry["volume_range"],
                series_entry["start_barcode"],
            )
            st.session_state.selected_series = None
            st.session_state.original_series_name = None
            st.rerun()

    # Main application layout
    col1, col2 = st.columns([1, 2])

    with col1:
        # Input form
        series_input_form()

        # Series list
        if st.session_state.series_entries:
            st.subheader("Queued Series")
            for i, entry in enumerate(st.session_state.series_entries):
                st.write(f"**{entry['name']}** - {len(entry['volumes'])} volumes")

            if st.button("Process All Series"):
                if st.session_state.series_entries:
                    # Start with first series
                    first_entry = st.session_state.series_entries[0]
                    st.session_state.pending_series_name = first_entry["name"]
                    st.session_state.original_series_name = first_entry["name"]
                    st.session_state.start_barcode = first_entry["start_barcode"]
                    st.rerun()

    with col2:
        # Results display
        display_results()


if __name__ == "__main__":
    main()