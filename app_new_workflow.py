#!/usr/bin/env python3
"""
Manga Lookup Tool - Streamlit Web App

Redesigned workflow with step-by-step process:
1. Starting barcode input
2. Series selection with API lookup
3. Volume range input
4. Processing with progress tracking
5. Results display with export options
"""

import sys
import requests

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import time

# Import existing core logic
from manga_lookup import (
    DeepSeekAPI,
    GoogleBooksAPI,
    VertexAIAPI,
    ProjectState,
    generate_sequential_barcodes,
    parse_volume_range,
)
from marc_exporter import export_books_to_marc
from mal_cover_fetcher import MALCoverFetcher
from mangadex_cover_fetcher import MangaDexCoverFetcher


def initialize_session_state():
    """Initialize session state variables for new workflow"""
    if "workflow_step" not in st.session_state:
        st.session_state.workflow_step = "barcode_input"
    if "start_barcode" not in st.session_state:
        st.session_state.start_barcode = ""
    if "series_entries" not in st.session_state:
        st.session_state.series_entries = []
    if "current_series_index" not in st.session_state:
        st.session_state.current_series_index = 0
    if "all_books" not in st.session_state:
        st.session_state.all_books = []
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = {
            "is_processing": False,
            "progress": 0,
            "total_volumes": 0,
            "start_time": None,
        }
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState()


def display_barcode_input():
    """Step 1: Starting barcode input"""
    st.header("Step 1: Enter Starting Barcode")

    st.write("Enter the starting barcode number for your manga collection.")
    st.write("Examples: T000001, 00001234, MANGA005")
    st.write("**Requirements:** Any combination of letters and numbers, ending in a number")

    barcode_input = st.text_input(
        "Starting Barcode",
        value="",
        placeholder="e.g., T000001",
        key="barcode_input"
    )

    if st.button("Confirm Starting Barcode"):
        if not barcode_input:
            st.error("Please enter a barcode number")
            return

        # Validate barcode format (ASCII only, ending in number)
        if not barcode_input[-1].isdigit():
            st.error("Barcode must end with a number")
            return

        st.session_state.start_barcode = barcode_input
        st.session_state.workflow_step = "barcode_confirmation"
        st.rerun()


def display_barcode_confirmation():
    """Step 2: Show barcode sequence"""
    st.header("Step 2: Barcode Sequence Confirmed")

    st.success(f"Starting barcode: {st.session_state.start_barcode}")

    # Show first 3 barcodes in sequence
    try:
        barcodes = generate_sequential_barcodes(
            st.session_state.start_barcode, 3
        )
        st.write("**First 3 barcodes in sequence:**")
        for i, barcode in enumerate(barcodes, 1):
            st.write(f"{i}. {barcode}")
    except Exception as e:
        st.error(f"Error generating barcodes: {e}")
        if st.button("Go Back"):
            st.session_state.workflow_step = "barcode_input"
            st.rerun()
        return

    st.write("---")
    st.header("Add 1st Series")

    series_name = st.text_input(
        "Series Name",
        placeholder="e.g., Naruto, One Piece, Attack on Titan",
        key="first_series_input"
    )

    if st.button("Confirm Series Name"):
        if not series_name:
            st.error("Please enter a series name")
            return

        # Add first series entry
        st.session_state.series_entries.append({
            "name": series_name,
            "volume_range": "",
            "volumes": [],
            "start_barcode": st.session_state.start_barcode,
            "confirmed": False,
            "search_results": [],
            "selected_series": None
        })

        st.session_state.workflow_step = "series_search"
        st.rerun()


def search_series_info(series_name: str):
    """Search for series information using APIs"""
    results = []

    # Try Vertex AI first (most authoritative)
    try:
        vertex_api = VertexAIAPI()
        suggestions = vertex_api.correct_series_name(series_name)
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            # Get comprehensive series information
            try:
                series_info = vertex_api.get_comprehensive_series_info(suggestion)
                results.append({
                    "name": suggestion,
                    "source": "Vertex AI",
                    "authors": series_info.get("authors", []),
                    "volume_count": series_info.get("number_of_extant_volumes", 0),
                    "summary": series_info.get("description", ""),
                    "cover_url": None,  # Vertex AI doesn't provide covers
                    "additional_info": {
                        "genres": series_info.get("genres", []),
                        "publisher": series_info.get("publisher", ""),
                        "status": series_info.get("status", ""),
                        "alternative_titles": series_info.get("alternative_titles", []),
                        "spin_offs": series_info.get("spin_offs", []),
                        "adaptations": series_info.get("adaptations", [])
                    }
                })
            except Exception as detail_error:
                # If detailed lookup fails, still add the suggestion
                results.append({
                    "name": suggestion,
                    "source": "Vertex AI",
                    "authors": [],
                    "volume_count": 0,
                    "summary": "",
                    "cover_url": None,
                    "additional_info": {}
                })
    except Exception as e:
        # Silently fail for Vertex AI - it's an enhancement
        pass

    # Try DeepSeek API second
    try:
        deepseek_api = DeepSeekAPI()
        suggestions = deepseek_api.correct_series_name(series_name)
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            # Get detailed series information
            try:
                book_data = deepseek_api.get_book_info(
                    suggestion, 1, st.session_state.project_state
                )
                if book_data:
                    results.append({
                        "name": suggestion,
                        "source": "DeepSeek",
                        "authors": book_data.get("authors", []),
                        "volume_count": book_data.get("number_of_extant_volumes", 0),
                        "summary": book_data.get("description", ""),
                        "cover_url": None,  # Will be fetched separately
                        "additional_info": {
                            "genres": book_data.get("genres", []),
                            "publisher": book_data.get("publisher_name", ""),
                            "status": "",
                            "alternative_titles": [],
                            "spin_offs": [],
                            "adaptations": []
                        }
                    })
                else:
                    results.append({
                        "name": suggestion,
                        "source": "DeepSeek",
                        "authors": [],
                        "volume_count": 0,
                        "summary": "",
                        "cover_url": None,
                        "additional_info": {}
                    })
            except Exception as detail_error:
                # If detailed lookup fails, still add the suggestion
                results.append({
                    "name": suggestion,
                    "source": "DeepSeek",
                    "authors": [],
                    "volume_count": 0,
                    "summary": "",
                    "cover_url": None,
                    "additional_info": {}
                })
    except Exception as e:
        st.error(f"DeepSeek API error: {e}")

    # Try Google Books for additional series information
    try:
        google_api = GoogleBooksAPI()
        # Search for volume 1 of the series to get better metadata
        search_query = f"{series_name} 1"
        url = f"{google_api.base_url}?q={search_query}&maxResults=5"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("totalItems", 0) > 0:
            for item in data["items"][:3]:  # Limit to 3 results
                volume_info = item["volumeInfo"]
                title = volume_info.get("title", "")

                # Only add if it looks like a volume 1
                if "1" in title or "one" in title.lower() or "first" in title.lower():
                    authors = volume_info.get("authors", [])
                    description = volume_info.get("description", "")
                    image_links = volume_info.get("imageLinks", {})
                    cover_url = google_api._select_cover_image(image_links)

                    results.append({
                        "name": f"{series_name} (Google Books)",
                        "source": "Google Books",
                        "authors": authors,
                        "volume_count": 0,  # Google Books doesn't provide series volume count
                        "summary": description,
                        "cover_url": cover_url,
                        "additional_info": {
                            "genres": [],
                            "publisher": "",
                            "status": "",
                            "alternative_titles": [],
                            "spin_offs": [],
                            "adaptations": []
                        }
                    })
    except Exception as e:
        # Silently fail for Google Books - it's just an enhancement
        pass

    # Fetch cover images for all results
    for result in results:
        if not result["cover_url"]:
            result["cover_url"] = fetch_cover_for_series(result["name"])

    return results


def fetch_cover_for_series(series_name: str) -> str | None:
    """Fetch cover image URL for a series"""
    # Try MAL first
    try:
        mal_fetcher = MALCoverFetcher()
        cover_url = mal_fetcher.fetch_cover(series_name, 1)
        if cover_url:
            return cover_url
    except Exception:
        pass

    # Try MangaDex
    try:
        mangadex_fetcher = MangaDexCoverFetcher()
        cover_url = mangadex_fetcher.fetch_cover(series_name, 1)
        if cover_url:
            return cover_url
    except Exception:
        pass

    return None


def display_series_search():
    """Step 3: Series search and selection"""
    current_series = st.session_state.series_entries[
        st.session_state.current_series_index
    ]

    st.header(f"Step 3: Confirm Series - {current_series['name']}")

    # Show search results if not already searched
    if not current_series["search_results"]:
        with st.spinner("Searching for series information..."):
            current_series["search_results"] = search_series_info(
                current_series["name"]
            )

    # Display search results as cards
    if current_series["search_results"]:
        st.write("**Found series:**")

        for i, result in enumerate(current_series["search_results"]):
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    if result["cover_url"]:
                        st.image(result["cover_url"], width=100)
                    else:
                        st.write("No cover")

                with col2:
                    st.write(f"**{result['name']}**")
                    st.caption(f"Source: {result['source']}")

                    if result["authors"]:
                        st.write(f"**Authors:** {', '.join(result['authors'])}")

                    if result["volume_count"] > 0:
                        st.write(f"**Volumes:** {result['volume_count']}")

                    # Show additional info if available
                    additional_info = result.get("additional_info", {})
                    if additional_info.get("genres"):
                        st.write(f"**Genres:** {', '.join(additional_info['genres'])}")

                    if additional_info.get("publisher"):
                        st.write(f"**Publisher:** {additional_info['publisher']}")

                    if additional_info.get("status"):
                        st.write(f"**Status:** {additional_info['status']}")

                    if additional_info.get("alternative_titles"):
                        st.write(f"**Also known as:** {', '.join(additional_info['alternative_titles'])}")

                    if result["summary"]:
                        st.write(f"**Summary:** {result['summary']}")

                    st.caption("Note: Covers may appear differently in different editions, printings, and languages.")

                    if st.button("Select This Series", key=f"select_{i}"):
                        current_series["selected_series"] = result["name"]
                        st.session_state.workflow_step = "volume_input"
                        st.rerun()

                st.write("---")
    else:
        st.warning("No series found. You can proceed with the original name.")

    # Option to use original name
    if st.button("Use Original Name"):
        current_series["selected_series"] = current_series["name"]
        st.session_state.workflow_step = "volume_input"
        st.rerun()


def display_volume_input():
    """Step 4: Volume range input"""
    current_series = st.session_state.series_entries[st.session_state.current_series_index]

    st.header(f"Step 4: Volume Range - {current_series['selected_series']}")

    volume_range = st.text_input(
        "Volume Range",
        placeholder="e.g., 1-10, 1,3,5,7, 1-5,8,10",
        key=f"volume_range_{st.session_state.current_series_index}"
    )

    if st.button("Confirm Volumes"):
        if not volume_range:
            st.error("Please enter a volume range")
            return

        try:
            volumes = parse_volume_range(volume_range)
            if not volumes:
                st.error("Invalid volume range format")
                return

            current_series["volume_range"] = volume_range
            current_series["volumes"] = volumes
            current_series["confirmed"] = True

            # Calculate barcodes for this series
            total_volumes_so_far = sum(len(entry["volumes"]) for entry in st.session_state.series_entries[:-1])
            start_barcode_num = int(st.session_state.start_barcode.rstrip('0123456789')) + total_volumes_so_far
            current_series["barcodes"] = generate_sequential_barcodes(
                st.session_state.start_barcode.replace(st.session_state.start_barcode.rstrip('0123456789'), str(start_barcode_num)),
                len(volumes)
            )

            st.session_state.workflow_step = "series_confirmation"
            st.rerun()

        except Exception as e:
            st.error(f"Error parsing volume range: {e}")


def display_series_confirmation():
    """Step 5: Series confirmation and option to add more"""
    st.header("Step 5: Series Confirmation")

    # Show all confirmed series
    for i, series in enumerate(st.session_state.series_entries):
        if series["confirmed"]:
            st.write(f"**{series['selected_series']}** - {len(series['volumes'])} volumes")
            st.write(f"Barcodes: {series['barcodes'][0]} to {series['barcodes'][-1]}")
            st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add Another Series"):
            st.session_state.current_series_index += 1
            st.session_state.series_entries.append({
                "name": "",
                "volume_range": "",
                "volumes": [],
                "start_barcode": "",
                "confirmed": False,
                "search_results": [],
                "selected_series": None
            })
            st.session_state.workflow_step = "series_search"
            st.rerun()

    with col2:
        if st.button("Start Processing"):
            st.session_state.workflow_step = "processing"
            st.rerun()


def display_processing():
    """Step 6: Processing display"""
    st.header("Processing Manga Volumes")

    # Initialize processing state
    if not st.session_state.processing_state["is_processing"]:
        total_volumes = sum(len(series["volumes"]) for series in st.session_state.series_entries)
        st.session_state.processing_state = {
            "is_processing": True,
            "progress": 0,
            "total_volumes": total_volumes,
            "start_time": time.time(),
            "results": []
        }

    # Show progress
    state = st.session_state.processing_state
    progress = state["progress"]
    total = state["total_volumes"]

    st.write(f"Processing {progress} of {total} volumes")

    # Show elapsed time
    if state["start_time"]:
        elapsed = time.time() - state["start_time"]
        if elapsed < 60:
            st.write(f"Elapsed time: {int(elapsed)} seconds")
        elif elapsed < 3600:
            minutes = int(elapsed / 60)
            seconds = int(elapsed % 60)
            st.write(f"Elapsed time: {minutes}m {seconds}s")
        else:
            hours = int(elapsed / 3600)
            minutes = int((elapsed % 3600) / 60)
            st.write(f"Elapsed time: {hours}h {minutes}m")

    # Show progress table with check/X marks
    st.subheader("Processing Progress")

    # Create progress table
    progress_data = []
    for series_entry in st.session_state.series_entries:
        for volume in series_entry["volumes"]:
            progress_data.append({
                "Series": series_entry["selected_series"],
                "Volume": volume,
                "Status": "❌" if progress < total else "✅"
            })

    if progress_data:
        # Display as a table
        for i, item in enumerate(progress_data):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"{item['Series']} - Vol {item['Volume']}")
            col2.write(item["Status"])
            if i < len(progress_data) - 1:
                st.divider()

    # Process volumes (simplified for now)
    if progress < total:
        # Simulate processing
        time.sleep(0.5)
        st.session_state.processing_state["progress"] += 1
        st.rerun()
    else:
        st.session_state.processing_state["is_processing"] = False
        st.session_state.workflow_step = "results"
        st.rerun()


def display_results():
    """Step 7: Results display"""
    st.header("Processing Complete!")

    # Results table with series headers and detailed information
    if not st.session_state.all_books:
        st.info("No books were processed")
        return

    # Group books by series
    from collections import defaultdict
    series_groups = defaultdict(list)
    for book in st.session_state.all_books:
        series_groups[book.series_name].append(book)

    # Display each series with header and volume details
    for series_name in sorted(series_groups.keys()):
        books = sorted(series_groups[series_name], key=lambda x: x.volume_number)

        # Series header
        st.markdown(f"### 📚 {series_name}")

        # Series metadata
        if books:
            first_book = books[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**Author:** {', '.join(first_book.authors) if first_book.authors else 'Unknown'}")
            with col2:
                st.write(f"**Barcode Range:** {books[0].barcode} - {books[-1].barcode}")
            with col3:
                st.write(f"**Volume Range:** {books[0].volume_number} - {books[-1].volume_number}")
            with col4:
                st.write(f"**Total Volumes:** {len(books)}")

        # Volume details table
        st.subheader("Volume Details")

        # Table header
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 2])
        col1.write("**Cover**")
        col2.write("**Title**")
        col3.write("**Vol**")
        col4.write("**Barcode**")
        col5.write("**MSRP**")
        col6.write("**Physical Desc**")
        col7.write("**Summary**")

        # Volume rows
        for book in books:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 2])

            # Cover image
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    st.image(book.cover_image_url, width=50)
                else:
                    st.write("📚")

            # Title
            with col2:
                st.write(book.book_title or f"{series_name} Vol. {book.volume_number}")

            # Volume number
            with col3:
                st.write(str(book.volume_number))

            # Barcode
            with col4:
                st.write(book.barcode)

            # MSRP
            with col5:
                st.write(f"${book.msrp_cost:.2f}" if book.msrp_cost else "N/A")

            # Physical description
            with col6:
                st.write(book.physical_description or "N/A")

            # Summary description (truncated)
            with col7:
                desc = book.description or "No description"
                if len(desc) > 100:
                    st.write(f"{desc[:100]}...")
                    st.caption("Hover for full description")
                else:
                    st.write(desc)

        st.divider()

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export to MARC"):
            try:
                marc_data = export_books_to_marc(st.session_state.all_books)
                st.success("MARC file exported successfully!")
                st.download_button(
                    "Download MARC File",
                    data=marc_data,
                    file_name="manga_export.mrc",
                    mime="application/marc",
                )
            except Exception as e:
                st.error(f"Error exporting MARC: {e!s}")

    with col2:
        if st.button("Generate Labels"):
            st.info("Label generation will be implemented")


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

    # Route to appropriate step
    if st.session_state.workflow_step == "barcode_input":
        display_barcode_input()
    elif st.session_state.workflow_step == "barcode_confirmation":
        display_barcode_confirmation()
    elif st.session_state.workflow_step == "series_search":
        display_series_search()
    elif st.session_state.workflow_step == "volume_input":
        display_volume_input()
    elif st.session_state.workflow_step == "series_confirmation":
        display_series_confirmation()
    elif st.session_state.workflow_step == "processing":
        display_processing()
    elif st.session_state.workflow_step == "results":
        display_results()


if __name__ == "__main__":
    main()