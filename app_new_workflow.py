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

import re
import sys
import time
from collections import defaultdict

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import requests

# Import existing core logic
from manga_lookup import (
    DeepSeekAPI,
    GoogleBooksAPI,
    VertexAIAPI,
    ProjectState,
    generate_sequential_barcodes,
    parse_volume_range,
    validate_barcode,
    validate_series_name,
    sanitize_series_name,
)
from marc_exporter import export_books_to_marc
from mal_cover_fetcher import MALCoverFetcher
from mangadex_cover_fetcher import MangaDexCoverFetcher


class SessionStateCache:
    """In-memory cache using Streamlit session state for persistence"""

    def __init__(self):
        # Initialize cache in session state if not exists
        if "cache_series_info" not in st.session_state:
            st.session_state.cache_series_info = {}
        if "cache_cover_images" not in st.session_state:
            st.session_state.cache_cover_images = {}

    def get_cached_series_info(self, series_name: str):
        """Get cached series information"""
        # Always return None to disable caching
        return None

    def cache_series_info(self, series_name: str, series_info: dict):
        """Cache series information"""
        st.session_state.cache_series_info[series_name] = series_info

    def get_cached_cover_image(self, key: str):
        """Get cached cover image URL"""
        # Always return None to disable caching
        return None

    def cache_cover_image(self, key: str, url: str):
        """Cache cover image URL"""
        st.session_state.cache_cover_images[key] = url


def initialize_precached_data():
    """Initialize comprehensive pre-cached data for specified manga series"""

    # All series with basic volume counts
    series_volume_counts = {
        # Attack on Titan universe
        "Attack on Titan": 34,
        "Attack on Titan: Colossal Edition": 6,
        "Attack on Titan: No Regrets": 2,
        "Attack on Titan: Before the Fall": 17,

        # One Piece
        "One Piece": 105,

        # Tokyo Ghoul universe
        "Tokyo Ghoul": 14,
        "Tokyo Ghoul: re": 16,

        # Bakuman
        "Bakuman": 20,

        # Hikaru no Go
        "Hikaru no Go": 23,

        # Tegami Bachi
        "Tegami Bachi": 20,

        # Naruto universe
        "Naruto": 72,
        "Boruto: Naruto Next Generation": 20,
        "Boruto: Two Blue Vortex": 4,

        # Dragon Ball
        "Dragon Ball Z": 26,

        # Psychological/Drama
        "Flowers of Evil": 11,
        "Goodnight Punpun": 13,
        "Happiness": 10,
        "All You Need is Kill": 2,

        # Berserk
        "Berserk": 41,

        # Modern hits
        "Tokyo Revengers": 31,
        "To Your Eternity": 20,

        # Sports
        "Haikyuu!": 45,

        # Fairy Tail
        "Fairy Tail": 63,

        # Assassination Classroom
        "Assassination Classroom": 21,

        # Cells at Work
        "Cells at Work": 6,

        # Akira
        "Akira": 6,

        # Gigant
        "Gigant": 10,

        # Inuyasha universe
        "Inuyasha": 56,
        "Inuyashiki": 10,

        # Gantz universe
        "Gantz": 37,
        "Gantz G": 3,

        # Alive
        "Alive": 21,

        # Orange
        "Orange": 5,

        # Welcome Back Alice
        "Welcome Back Alice": 10,

        # Barefoot Gen
        "Barefoot Gen": 10,

        # Platinum End
        "Platinum End": 14,

        # Death Note
        "Death Note": 12,

        # Magus of the Library
        "Magus of the Library": 7,

        # Spy x Family
        "Spy x Family": 12,

        # Hunter x Hunter
        "Hunter x Hunter": 36,

        # Samurai 8
        "Samurai 8": 5,

        # Thunder3
        "Thunder3": 10,

        # Tokyo Alien Bros.
        "Tokyo Alien Bros.": 8,

        # Centaur
        "Centaur": 6,

        # Blue Note
        "Blue Note": 4,

        # Children of Whales
        "Children of Whales": 23,

        # Bleach
        "Bleach": 74,

        # Crayon Shinchan
        "Crayon Shinchan": 50,

        # A Polar Bear in Love
        "A Polar Bear in Love": 5,

        # Sho-ha Shoten
        "Sho-ha Shoten": 8,

        # O Parts Hunter
        "O Parts Hunter": 19,

        # Mashle: Magic and Muscles
        "Mashle: Magic and Muscles": 18,
        "Mashle": 18
    }

    # Pre-cache all series with basic info
    for series, volume_count in series_volume_counts.items():
        cached_info = {
            "corrected_series_name": series,
            "authors": [],  # Will be populated by APIs
            "extant_volumes": volume_count,
            "summary": "",  # Will be populated by APIs
            "cover_image_url": None,  # Will be populated by APIs
            "alternative_titles": [],
            "spinoff_series": []
        }

        # Cache the series info
        try:
            st.session_state.project_state.cache_series_info(series, cached_info)
        except Exception as e:
            # Silently fail if caching doesn't work
            pass


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
        # Try SQLite database first (for permanent storage)
        try:
            st.session_state.project_state = ProjectState()
        except Exception as e:
            # Fallback to session state cache if SQLite fails
            st.warning(f"SQLite database initialization failed: {e}. Using session state cache.")
            st.session_state.project_state = SessionStateCache()

    # Initialize pre-cached data
    # initialize_precached_data()


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

        # Validate barcode format using enhanced validation
        if not validate_barcode(barcode_input):
            st.error("Invalid barcode format. Barcode must be 1-20 alphanumeric characters, ending with a number, and may contain hyphens.")
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
        barcode_list = ", ".join(barcodes)
        st.markdown(f"*{barcode_list}*")
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

        # Validate series name length
        if not validate_series_name(series_name):
            st.error("Series name is too long. Maximum 255 characters allowed.")
            return

        # Sanitize series name
        sanitized_name = sanitize_series_name(series_name)
        if not sanitized_name:
            st.error("Invalid series name format")
            return

        # Add first series entry
        st.session_state.series_entries.append({
            "name": sanitized_name,
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

    # Check cache first for the original series name
    try:
        cached_info = st.session_state.project_state.get_cached_series_info(series_name)
        if cached_info:
            st.success(f"🎯 Using cached data for: {series_name}")
            # Convert cached data to the expected format
            results.append({
                "name": cached_info.get("corrected_series_name", series_name),
                "source": "Vertex AI (Cached)",
                "authors": [cached_info.get("authors", "")] if cached_info.get("authors") else [],
                "volume_count": cached_info.get("extant_volumes", 0),
                "summary": cached_info.get("summary", ""),
                "cover_url": cached_info.get("cover_image_url", None),
                "additional_info": {
                    "genres": [],
                    "publisher": "",
                    "status": "",
                    "alternative_titles": cached_info.get("alternative_titles", []),
                    "spin_offs": cached_info.get("spinoff_series", []),
                    "adaptations": []
                }
            })
            return results
        else:
            st.info(f"🔍 No cached data found for: {series_name}, making API call...")
    except Exception as e:
        st.warning(f"Cache check failed: {e}")

    # Debug: Check if Vertex AI is properly configured
    try:
        vertex_api = VertexAIAPI()
        st.info(f"✅ Vertex AI API initialized successfully for: {series_name}")
    except Exception as e:
        st.error(f"❌ Vertex AI initialization failed: {e}")
        st.info("Falling back to DeepSeek API...")

    # Try DeepSeek API first
    try:
        deepseek_api = DeepSeekAPI()
        suggestions = deepseek_api.correct_series_name(series_name)
        for suggestion in suggestions[:5]:
            book_data = deepseek_api.get_book_info(suggestion, 1, st.session_state.project_state)
            if book_data:
                results.append({
                    "name": suggestion,
                    "source": "DeepSeek",
                    "authors": book_data.get("authors", []),
                    "volume_count": book_data.get("number_of_extant_volumes", 0),
                    "summary": book_data.get("description", ""),
                    "cover_url": None,
                    "additional_info": {
                        "genres": book_data.get("genres", []),
                        "publisher": book_data.get("publisher_name", ""),
                    }
                })
    except Exception as ds_e:
        st.error(f"DeepSeek API failed: {ds_e}")

    # Fallback to Vertex AI
    if not results:
        try:
            vertex_api = VertexAIAPI()
            series_info = vertex_api.get_comprehensive_series_info(series_name, st.session_state.project_state)

            if series_info and series_info.get("corrected_series_name"):
                st.session_state.project_state.cache_series_info(series_name, series_info)
                main_series_name = series_info["corrected_series_name"]

                # Main series result
                results.append({
                    "name": main_series_name,
                    "source": "Vertex AI",
                    "authors": [author.strip() for author in series_info.get("authors", "").split(",")] if series_info.get("authors") else [],
                    "volume_count": series_info.get("extant_volumes", 0),
                    "summary": series_info.get("summary", ""),
                    "cover_url": series_info.get("cover_image_url", None),
                    "additional_info": {
                        "spin_offs": series_info.get("spinoff_series", []),
                    }
                })

                # Alternate editions
                for edition in series_info.get("alternate_editions", []):
                    results.append({
                        "name": f"{main_series_name} ({edition.get('edition_name', '')})",
                        "source": "Vertex AI",
                        "authors": [author.strip() for author in series_info.get("authors", "").split(",")] if series_info.get("authors") else [],
                        "volume_count": series_info.get("extant_volumes", 0),
                        "summary": series_info.get("summary", ""),
                        "cover_url": series_info.get("cover_image_url", None),
                        "volumes_per_book": edition.get("volumes_per_book"),
                        "additional_info": {}
                    })
        except Exception as e:
            st.warning(f"Vertex AI failed: {e}.")

    # Try Google Books for additional series information
    try:
        google_api = GoogleBooksAPI()
        # Search for volume 1 of the series to get better metadata
        search_query = f"{series_name} 1"
        url = f"{google_api.base_url}?q={search_query}&maxResults=5"

        response = requests.get(url, timeout=10, verify=True)
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
        # Use generic error message for users, log detailed error
        print(f"Google Books API error: {e}")
        # Silently fail for Google Books - it's just an enhancement

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


def display_series_input():
    """Series name input for additional series"""
    current_series = st.session_state.series_entries[
        st.session_state.current_series_index
    ]

    st.header(f"Step 3: Add Series {st.session_state.current_series_index + 1}")

    series_name = st.text_input(
        "Series Name",
        placeholder="e.g., Naruto, One Piece, Attack on Titan",
        key=f"series_input_{st.session_state.current_series_index}"
    )

    if st.button("Confirm Series Name"):
        if not series_name:
            st.error("Please enter a series name")
            return

        # Validate series name length
        if not validate_series_name(series_name):
            st.error("Series name is too long. Maximum 255 characters allowed.")
            return

        # Sanitize series name
        sanitized_name = sanitize_series_name(series_name)
        if not sanitized_name:
            st.error("Invalid series name format")
            return

        # Update the series entry with the name
        current_series["name"] = sanitized_name
        st.session_state.workflow_step = "series_search"
        st.rerun()


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
                        st.write(f"**Number of Extant Volumes:** {result.get('volume_count', 'Unknown')}")

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
                    
                    if additional_info.get("spin_offs"):
                        st.write(f"**Spinoffs/Alternate Editions:** {', '.join(additional_info['spin_offs'])}")

                    if result.get("volumes_per_book"):
                        st.write(f"**Volumes per Book:** {result['volumes_per_book']}")

                    if result["summary"]:
                        st.write(f"**Description:** {result['summary']}")

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
        value="",
        placeholder="e.g., 1-10, 1,3,5,7, 1-5,8,10",
        key=f"volume_range_{st.session_state.current_series_index}"
    )

    if st.button("Continue"):
        if not volume_range:
            st.error("Please enter a volume range")
            return

        # Clean the input
        original_volume_range = volume_range

        try:
            volumes = parse_volume_range(volume_range)
            if not volumes:
                st.error("Invalid volume range format")
                return

            current_series["volume_range"] = volume_range
            current_series["volumes"] = volumes
            current_series["confirmed"] = True

            # Calculate the starting barcode for this series
            total_volumes_all_confirmed = sum(len(s["volumes"]) for s in st.session_state.series_entries if s["confirmed"])
            total_volumes_of_previous_series = total_volumes_all_confirmed - len(current_series["volumes"])


            # Use regex to extract prefix and numeric part of the barcode
            match = re.match(r"([a-zA-Z]*)(\d+)", st.session_state.start_barcode)
            if match:
                prefix = match.group(1)
                start_num = int(match.group(2))
                num_digits = len(match.group(2))

                # Calculate the starting barcode number for this series
                current_start_num = start_num + total_volumes_of_previous_series

                # Generate the starting barcode for this series
                current_start_barcode = f"{prefix}{current_start_num:0{num_digits}d}"

                current_series["barcodes"] = generate_sequential_barcodes(
                    current_start_barcode,
                    len(volumes)
                )
            else:
                # Fallback: use the original logic but with proper numeric extraction
                numeric_part = ''.join(c for c in st.session_state.start_barcode if c.isdigit())
                if numeric_part:
                    start_num = int(numeric_part)
                    current_start_num = start_num + total_volumes_so_far
                    current_start_barcode = st.session_state.start_barcode.replace(numeric_part, str(current_start_num).zfill(len(numeric_part)))
                    current_series["barcodes"] = generate_sequential_barcodes(
                        current_start_barcode,
                        len(volumes)
                    )
                else:
                    raise ValueError(f"Invalid barcode format: {st.session_state.start_barcode}")

            st.session_state.workflow_step = "series_confirmation"
            st.rerun()

        except ValueError as e:
            st.error(f"Error parsing volume range '{volume_range}': {e}")
            st.info("Valid formats: '1-10', '1,3,5,7', '1-5,8,10', or '17-18-19' for omnibus")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


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
            st.session_state.workflow_step = "series_input"
            st.rerun()

    with col2:
        if st.button("Start Processing"):
            st.session_state.workflow_step = "processing"
            st.rerun()


def display_processing():
    """Step 6: Processing display"""
    st.header("Processing Manga Volumes")

    # Initialize APIs
    try:
        vertex_api = VertexAIAPI()
    except Exception as e:
        st.warning(f"Vertex AI API not available: {e}")
        vertex_api = None

    try:
        deepseek_api = DeepSeekAPI()
    except Exception as e:
        st.error(f"DeepSeek API not available: {e}")
        deepseek_api = None

    if not vertex_api and not deepseek_api:
        st.error("No APIs are available. Cannot process books.")
        return

    # Initialize processing state
    if not st.session_state.processing_state["is_processing"]:
        total_volumes = sum(len(series["volumes"]) for series in st.session_state.series_entries)
        st.session_state.processing_state = {
            "is_processing": True,
            "progress": 0,
            "total_volumes": total_volumes,
            "start_time": time.time(),
        }
        st.session_state.all_books = []

    # Show progress
    state = st.session_state.processing_state
    progress = state["progress"]
    total = state["total_volumes"]

    st.write(f"Processing {progress} of {total} volumes")
    progress_bar = st.progress(progress / total if total > 0 else 0)

    # Process all books
    if progress < total:
        processed_count = 0
        for series_entry in st.session_state.series_entries:
            if not series_entry["confirmed"]:
                continue

            series_name = series_entry["selected_series"]
            volumes = series_entry["volumes"]
            barcodes = series_entry["barcodes"]

            for i, volume_num in enumerate(volumes):
                if processed_count >= progress:
                    # Get book info
                    book_data = None
                    if deepseek_api:
                        try:
                            book_data = deepseek_api.get_book_info(series_name, volume_num, st.session_state.project_state)
                        except Exception as e:
                            st.warning(f"DeepSeek API failed for {series_name} Vol {volume_num}: {e}")
                    
                    if not book_data and vertex_api:
                        try:
                            book_data = vertex_api.get_book_info(series_name, volume_num, st.session_state.project_state)
                        except Exception as e:
                            st.error(f"Vertex AI failed for {series_name} Vol {volume_num}: {e}")

                    if book_data:
                        # Create BookInfo object and add barcode
                        from manga_lookup import BookInfo, GoogleBooksAPI
                        google_books_api = GoogleBooksAPI()
                        mangadex_fetcher = MangaDexCoverFetcher()

                        cover_url = book_data.get("cover_image_url")
                        if not cover_url:
                            cover_url = google_books_api.get_cover_image_url(book_data.get("isbn_13"), st.session_state.project_state)
                        if not cover_url:
                            cover_url = mangadex_fetcher.fetch_cover(series_name, volume_num)

                        book = BookInfo(
                            series_name=book_data.get("series_name", series_name),
                            volume_number=volume_num,
                            book_title=book_data.get("book_title", f"{series_name} Vol. {volume_num}"),
                            authors=book_data.get("authors", []),
                            msrp_cost=book_data.get("msrp_cost"),
                            isbn_13=book_data.get("isbn_13"),
                            publisher_name=book_data.get("publisher_name"),
                            copyright_year=book_data.get("copyright_year"),
                            description=book_data.get("description"),
                            physical_description=book_data.get("physical_description"),
                            genres=book_data.get("genres", []),
                            warnings=[],
                            barcode=barcodes[i],
                            cover_image_url=cover_url
                        )
                        st.session_state.all_books.append(book)

                    # Update progress
                    st.session_state.processing_state["progress"] += 1
                    progress_bar.progress(st.session_state.processing_state["progress"] / total)
                    time.sleep(0.1) # Small delay to allow UI to update
                    st.rerun()
                
                processed_count += 1
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
    st.divider()
    st.subheader("Export Options")

    try:
        marc_data = export_books_to_marc(st.session_state.all_books)
        st.download_button(
            "Download MARC File",
            data=marc_data,
            file_name="manga_export.mrc",
            mime="application/marc",
        )
    except Exception as e:
        st.error("Sorry! An error occurred while exporting the file.")
        print(f"Error exporting MARC: {e!s}")


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
    elif st.session_state.workflow_step == "series_input":
        display_series_input()
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
