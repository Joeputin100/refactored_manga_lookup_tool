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
import warnings
from collections import defaultdict

# Suppress warnings before importing other modules
from warning_suppressor import configure_warnings
configure_warnings()

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
    generate_sequential_general_barcodes,
    parse_volume_range,
    validate_barcode,
    validate_general_barcode,
    validate_series_name,
    sanitize_series_name,
)
from marc_exporter_atriuum_descriptive import export_books_to_marc_atriuum_descriptive as export_books_to_marc
from mal_cover_fetcher import MALCoverFetcher
from mangadex_cover_fetcher import MangaDexCoverFetcher


def get_series_cover_from_bigquery(series_name: str):
    """Get series cover image from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Sanitize series name for query
        sanitized_name = sanitize_series_name(series_name)

        query = f'''
        SELECT cover_image_data
        FROM `static-webbing-461904-c4.manga_lookup_cache.cover_images`
        WHERE LOWER(series_name) = LOWER("{sanitized_name}")
        LIMIT 1
        '''

        result = cache.client.query(query).result()
        for row in result:
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                return row.cover_image_data

        return None
    except Exception as e:
        if st.session_state.get('debug_mode', False):
            st.warning(f"BigQuery series cover lookup failed: {e}")
        return None


def get_volume_cover_from_bigquery(series_name: str, volume_number: int):
    """Get volume cover image from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Sanitize series name for query
        sanitized_name = sanitize_series_name(series_name)

        query = f'''
        SELECT cover_image_data
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_covers`
        WHERE LOWER(series_name) = LOWER("{sanitized_name}")
        AND volume_number = {volume_number}
        LIMIT 1
        '''

        result = cache.client.query(query).result()
        for row in result:
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                return row.cover_image_data

        return None
    except Exception as e:
        if st.session_state.get('debug_mode', False):
            st.warning(f"BigQuery volume cover lookup failed: {e}")
        return None


def get_any_volume_cover_from_bigquery(series_name: str):
    """Get any available volume cover image from BigQuery cache for a series"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Sanitize series name for query
        sanitized_name = sanitize_series_name(series_name)

        query = f'''
        SELECT cover_image_data, volume_number
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_covers`
        WHERE LOWER(series_name) = LOWER("{sanitized_name}")
        ORDER BY volume_number
        LIMIT 1
        '''

        result = cache.client.query(query).result()
        for row in result:
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                return row.cover_image_data

        return None
    except Exception as e:
        if st.session_state.get('debug_mode', False):
            st.warning(f"BigQuery any volume cover lookup failed: {e}")
        return None


def generate_marc_filename(books: list) -> str:
    """
    Generate a MARC export filename with date/time and sanitized series names.

    Format: yyyy-mm-dd hhmm am/pm - series_names.mrc

    Args:
        books: List of BookInfo objects

    Returns:
        Sanitized filename string
    """
    from datetime import datetime
    import re

    # Get current date/time in Pacific Standard Time
    from datetime import timezone, timedelta
    import pytz

    # Convert to Pacific time
    utc_time = datetime.now(timezone.utc)
    pacific_tz = pytz.timezone('US/Pacific')
    current_time = utc_time.astimezone(pacific_tz)

    # Format date/time as "yyyy-mm-dd hhmm am/pm"
    date_part = current_time.strftime("%Y-%m-%d")

    # Format time as 12-hour with am/pm
    hour_12 = current_time.strftime("%I").lstrip('0')  # Remove leading zero
    minute_part = current_time.strftime("%M")
    am_pm = current_time.strftime("%p").lower()
    time_part = f"{hour_12}{minute_part} {am_pm}"

    # Extract unique series names
    series_names = []
    for book in books:
        if hasattr(book, 'series_name') and book.series_name:
            series_names.append(book.series_name)

    # Remove duplicates and sort
    unique_series = sorted(list(set(series_names)))

    # Create series name part - take first 3 series or use "multiple" if more
    if len(unique_series) == 0:
        series_part = "no_series"
    elif len(unique_series) == 1:
        series_part = sanitize_filename_part(unique_series[0])
    elif len(unique_series) <= 3:
        series_part = "_".join(sanitize_filename_part(name) for name in unique_series)
    else:
        series_part = f"{sanitize_filename_part(unique_series[0])}_and_{len(unique_series)-1}_more"

    # Combine all parts
    filename = f"{date_part} {time_part} - {series_part}.mrc"

    # Ensure filename is not too long (Windows 7 limit is 260 chars total path)
    if len(filename) > 100:
        # Truncate series part if needed
        max_series_length = 100 - len(f"{date_part} {time_part} - .mrc")
        if len(series_part) > max_series_length:
            series_part = series_part[:max_series_length-3] + "..."
        filename = f"{date_part} {time_part} - {series_part}.mrc"

    return filename


def sanitize_filename_part(text: str) -> str:
    """
    Sanitize text for use in filename parts.
    Removes characters not suitable for Windows 7 filenames.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text suitable for filenames
    """
    if not text:
        return ""

    # Remove characters not allowed in Windows filenames
    # Windows 7 disallowed: < > : " / \ | ? *
    # Also remove other problematic characters
    disallowed_chars = r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]'
    sanitized = re.sub(disallowed_chars, '', text)

    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Ensure not empty after sanitization
    if not sanitized:
        sanitized = "unnamed"

    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]

    return sanitized


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
        # Try BigQuery cache first
        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()
            if cache.enabled:
                cached_info = cache.get_series_info(series_name)
                if cached_info:
                    return cached_info
        except Exception as e:
            # Log cache failure but continue with fallback
            if st.session_state.get('debug_mode', False):
                st.warning(f"BigQuery cache lookup failed: {e}")

        # Fallback to session state cache
        return st.session_state.cache_series_info.get(series_name)

    def cache_series_info(self, series_name: str, series_info: dict):
        """Cache series information"""
        st.session_state.cache_series_info[series_name] = series_info

    def get_cached_cover_image(self, key: str):
        """Get cached cover image URL"""
        # Fallback to session state cache
        return st.session_state.cache_cover_images.get(key)

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
            # Log cache failure but continue
            if st.session_state.get('debug_mode', False):
                st.warning(f"Session state caching failed: {e}")


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
        key="barcode_input")

    if st.button("Confirm Starting Barcode"):
        # Sanitize input by removing leading/trailing spaces
        barcode_input = barcode_input.strip()

        if not barcode_input:
            st.error("Please enter a barcode number")
            return

        # Validate barcode format using enhanced validation
        if not validate_general_barcode(barcode_input):
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
        barcodes = generate_sequential_general_barcodes(
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
        key="first_series_input")

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


def format_authors(authors):
    """Format author names in 'Last, First' format"""
    if not authors:
        return []

    formatted = []
    for author in authors:
        if isinstance(author, str):
            # Simple heuristic: if there's a comma, assume it's already formatted
            if "," in author:
                formatted.append(author)
            else:
                # Try to split by spaces and reverse
                parts = author.strip().split()
                if len(parts) >= 2:
                    # Assume "First Last" format, convert to "Last, First"
                    formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
                else:
                    formatted.append(author)
        else:
            formatted.append(str(author))

    return formatted


def is_cover_url_accessible(url):
    """Check if a cover image URL is accessible"""
    if not url:
        return False

    try:
        import requests
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False


def get_series_info_from_bigquery(series_name: str):
    """Get series information from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Use case-insensitive query with LOWER() function
        query = f"""SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) = LOWER(\"{series_name}\")"""

        print(f"🔍 BigQuery query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            print(f"✅ Found series in BigQuery: {row.series_name}")
            return {
                "corrected_series_name": row.series_name,
                "authors": row.authors if hasattr(row, 'authors') else [],
                "extant_volumes": row.total_volumes if hasattr(row, 'total_volumes') else 0,
                "summary": row.summary if hasattr(row, 'summary') else "",
                "cover_image_url": row.cover_image_url if hasattr(row, 'cover_image_url') else None,
                "genres": row.genres if hasattr(row, 'genres') else [],
                "publisher": row.publisher if hasattr(row, 'publisher') else "",
                "status": row.status if hasattr(row, 'status') else "",
                "alternative_titles": row.alternative_titles if hasattr(row, 'alternative_titles') else [],
                "spinoff_series": row.spinoff_series if hasattr(row, 'spinoff_series') else [],
                "adaptations": row.adaptations if hasattr(row, 'adaptations') else []
            }

        if row_count == 0:
            print(f"❌ No series found in BigQuery for: {series_name}")

    except Exception as e:
        print(f"❌ BigQuery cache query failed: {e}")
    return None


def get_cover_image_from_bigquery(series_name: str):
    """Get compressed cover image from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Query for cover image data
        query = f'''SELECT cover_image_data FROM `static-webbing-461904-c4.manga_lookup_cache.cover_images` WHERE LOWER(series_name) = LOWER("{series_name}")'''

        print(f"🔍 BigQuery cover query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                print(f"✅ Found BigQuery stored cover for: {series_name}")
                # Convert base64 data to bytes
                try:
                    image_bytes = base64.b64decode(row.cover_image_data)
                    return image_bytes
                except Exception as e:
                    print(f"❌ Failed to decode BigQuery cover image: {e}")
                    return None

        if row_count == 0:
            print(f"❌ No BigQuery stored cover found for: {series_name}")

    except Exception as e:
        print(f"❌ BigQuery cover cache query failed: {e}")
    return None


def get_volume_cover_from_bigquery(series_name: str, volume_number: int):
    """Get compressed volume cover image from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Query for volume cover image data
        query = f'''SELECT cover_image_data FROM `static-webbing-461904-c4.manga_lookup_cache.volume_covers` WHERE LOWER(series_name) = LOWER("{series_name}") AND volume_number = {volume_number}'''

        print(f"🔍 BigQuery volume cover query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                print(f"✅ Found BigQuery stored volume cover for: {series_name} Vol {volume_number}")
                # Convert base64 data to bytes
                try:
                    image_bytes = base64.b64decode(row.cover_image_data)
                    return image_bytes
                except Exception as e:
                    print(f"❌ Failed to decode BigQuery volume cover image: {e}")
                    return None

        if row_count == 0:
            print(f"❌ No BigQuery stored volume cover found for: {series_name} Vol {volume_number}")

    except Exception as e:
        print(f"❌ BigQuery volume cover cache query failed: {e}")
    return None


def get_any_volume_cover_from_bigquery(series_name: str):
    """Get any available volume cover image from BigQuery cache for a series"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Query for any volume cover image data (prioritize volume 1, then any)
        query = f'''SELECT cover_image_data, volume_number FROM `static-webbing-461904-c4.manga_lookup_cache.volume_covers` WHERE LOWER(series_name) = LOWER("{series_name}") ORDER BY volume_number LIMIT 1'''

        print(f"🔍 BigQuery any volume cover query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            if hasattr(row, 'cover_image_data') and row.cover_image_data:
                print(f"✅ Found BigQuery stored volume cover for: {series_name} Vol {row.volume_number}")
                # Convert base64 data to bytes
                try:
                    image_bytes = base64.b64decode(row.cover_image_data)
                    return image_bytes
                except Exception as e:
                    print(f"❌ Failed to decode BigQuery volume cover image: {e}")
                    return None

        if row_count == 0:
            print(f"❌ No BigQuery stored volume covers found for: {series_name}")

    except Exception as e:
        print(f"❌ BigQuery any volume cover cache query failed: {e}")
    return None


def get_volume_info_from_bigquery(series_name: str, volume_number: int):
    """Get volume information from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Query for volume info
        query = f'''SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info` WHERE LOWER(series_name) = LOWER("{series_name}") AND volume_number = {volume_number}'''

        print(f"🔍 BigQuery volume query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            print(f"✅ Found volume in BigQuery: {series_name} Vol {volume_number}")
            return {
                "series_name": row.series_name,
                "volume_number": row.volume_number,
                "book_title": row.book_title if hasattr(row, 'book_title') else f"{series_name} Vol. {volume_number}",
                "authors": row.authors if hasattr(row, 'authors') else [],
                "isbn_13": row.isbn_13 if hasattr(row, 'isbn_13') else None,
                "publisher_name": row.publisher_name if hasattr(row, 'publisher_name') else "",
                "copyright_year": row.copyright_year if hasattr(row, 'copyright_year') else None,
                "description": row.description if hasattr(row, 'description') else "",
                "physical_description": row.physical_description if hasattr(row, 'physical_description') else "",
                "genres": row.genres if hasattr(row, 'genres') else [],
                "msrp_cost": row.msrp_cost if hasattr(row, 'msrp_cost') else None,
                "cover_image_url": row.cover_image_url if hasattr(row, 'cover_image_url') else None,
                "cached": True,
                "cache_source": "bigquery"
            }

        if row_count == 0:
            print(f"❌ No volume found in BigQuery for: {series_name} Vol {volume_number}")

    except Exception as e:
        print(f"❌ BigQuery volume cache query failed: {e}")
    return None


def search_series_info(series_name: str):
    """Search for series information using APIs"""
    results = []

    # Check BigQuery cache first
    try:
        cached_info = get_series_info_from_bigquery(series_name)
        if cached_info:
            st.success(f"🎯 Using BigQuery cached data for: {series_name}")
            # Convert cached data to the expected format
            results.append({
                "name": cached_info.get("corrected_series_name", series_name),
                "source": "BigQuery Cache",
                "authors": cached_info.get("authors", []),
                "volume_count": cached_info.get("extant_volumes", 0),
                "summary": cached_info.get("summary", ""),
                "cover_url": cached_info.get("cover_image_url", None),
                "additional_info": {
                    "genres": cached_info.get("genres", []),
                    "publisher": cached_info.get("publisher", ""),
                    "status": cached_info.get("status", ""),
                    "alternative_titles": cached_info.get("alternative_titles", []),
                    "spin_offs": cached_info.get("spinoff_series", []),
                    "adaptations": cached_info.get("adaptations", [])
                }
            })
            return results
        else:
            st.info(f"🔍 No BigQuery cached data found for: {series_name}")
    except Exception as e:
        st.warning(f"BigQuery cache check failed: {e}")

    # Fall back to local SQLite cache
    try:
        cached_info = st.session_state.project_state.get_cached_series_info(series_name)
        if cached_info:
            st.success(f"🎯 Using local cached data for: {series_name}")
            # Convert cached data to the expected format
            results.append({
                "name": cached_info.get("corrected_series_name", series_name),
                "source": "Vertex AI (Cached)",
                "authors": cached_info.get("authors", []),
                "volume_count": cached_info.get("extant_volumes", 0),
                "summary": cached_info.get("summary", ""),
                "cover_url": cached_info.get("cover_image_url", None),
                "additional_info": {
                    "genres": cached_info.get("genres", []),
                    "publisher": cached_info.get("publisher", ""),
                    "status": cached_info.get("status", ""),
                    "alternative_titles": cached_info.get("alternative_titles", []),
                    "spin_offs": cached_info.get("spinoff_series", []),
                    "adaptations": cached_info.get("adaptations", [])
                }
            })
            return results
        else:
            st.info(f"🔍 No cached data found for: {series_name}, making API call...")
    except Exception as e:
        st.warning(f"Local cache check failed: {e}")

    # Initialize APIs with proper error handling
    vertex_api = None
    deepseek_api = None

    # Try to initialize DeepSeek (priority)
    try:
        deepseek_api = DeepSeekAPI()
        st.info(f"✅ DeepSeek API initialized successfully for: {series_name}")
    except Exception as e:
        st.error(f"❌ DeepSeek API initialization failed: {e}")

    # Try to initialize Vertex AI (fallback)
    try:
        vertex_api = VertexAIAPI()
        st.info(f"✅ Vertex AI API initialized (fallback) for: {series_name}")
    except Exception as e:
        st.error(f"❌ Vertex AI initialization failed: {e}")

    # If no APIs are available, show warning and return
    if not vertex_api and not deepseek_api:
        st.error("❌ No APIs are available. Cannot search for series information.")
        return results

    # Try DeepSeek first (priority)
    if deepseek_api:
        try:
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
            st.warning(f"DeepSeek API search failed: {ds_e}")

    # Fallback to Vertex AI if available and no results yet
    if not results and vertex_api:
        try:
            series_info = vertex_api.get_comprehensive_series_info(series_name, st.session_state.project_state)

            if series_info and series_info.get("corrected_series_name"):
                st.session_state.project_state.cache_series_info(series_name, series_info)
                main_series_name = series_info["corrected_series_name"]

                # Main series result
                results.append({
                    "name": main_series_name,
                    "source": "Vertex AI (fallback)",
                    "authors": series_info.get("authors", []),
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
                        "source": "Vertex AI (fallback)",
                        "authors": series_info.get("authors", []),
                        "volume_count": series_info.get("extant_volumes", 0),
                        "summary": series_info.get("summary", ""),
                        "cover_url": series_info.get("cover_image_url", None),
                        "volumes_per_book": edition.get("volumes_per_book"),
                        "additional_info": {}
                    })
        except Exception as e:
            st.warning(f"Vertex AI search failed: {e}.")

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


def fetch_cover_for_series(series_name: str):
    """Fetch cover image URL for a series - prioritize Google Books for English covers"""
    # Try Google Books first (best for English editions)
    try:
        google_api = GoogleBooksAPI()
        cover_url = google_api.get_series_cover_url(series_name)
        if cover_url:
            print(f"✅ Using Google Books cover for: {series_name}")
            return cover_url
    except Exception as e:
        print(f"❌ Google Books cover failed for {series_name}: {e}")

    # Try MangaDex (good for English editions)
    try:
        mangadex_fetcher = MangaDexCoverFetcher()
        cover_url = mangadex_fetcher.fetch_cover(series_name, 1)
        if cover_url:
            print(f"✅ Using MangaDex cover for: {series_name}")
            return cover_url
    except Exception as e:
        print(f"❌ MangaDex cover failed for {series_name}: {e}")

    # Try MAL as fallback (often Japanese editions)
    try:
        mal_fetcher = MALCoverFetcher()
        cover_url = mal_fetcher.fetch_cover(series_name, 1)
        if cover_url:
            print(f"⚠️ Using MAL cover (may be Japanese) for: {series_name}")
            return cover_url
    except Exception as e:
        print(f"❌ MAL cover failed for {series_name}: {e}")

    print(f"❌ No cover found for: {series_name}")
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
        key=f"series_input_{st.session_state.current_series_index}")

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
                    # Smart Cover Display for Series Cards:
                    # BigQuery series cover → BigQuery volume cover (1st volume if available, any volume if they are available) → Hotlinked URL

                    # Try BigQuery series cover first
                    series_cover_bytes = get_series_cover_from_bigquery(result["name"])
                    if series_cover_bytes:
                        st.image(series_cover_bytes, width=100, caption="Series Cover")
                    # Fallback to volume cover (try volume 1 first, then any volume)
                    else:
                        volume_cover_bytes = get_volume_cover_from_bigquery(result["name"], 1)
                        if not volume_cover_bytes:
                            volume_cover_bytes = get_any_volume_cover_from_bigquery(result["name"])
                        if volume_cover_bytes:
                            st.image(volume_cover_bytes, width=100, caption="Volume Cover")
                        # Fallback to hotlinked URL
                        elif result["cover_url"] and is_cover_url_accessible(result["cover_url"]):
                            st.image(result["cover_url"], width=100, caption="Hotlinked")
                        else:
                            st.write("No cover available")

                with col2:
                    st.write(f"**{result['name']}**")
                    st.caption(f"Source: {result['source']}")

                    if result["authors"]:
                        formatted_authors = format_authors(result['authors'])
                        st.write(f"**Authors:** {', '.join(formatted_authors)}")

                    if int(result.get("volume_count", 0)) > 0:
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

                    if additional_info.get("adaptations"):
                        st.write(f"**Adaptations:** {', '.join(additional_info['adaptations'])}")

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
        key=f"volume_range_{st.session_state.current_series_index}")

    if st.button("Continue"):
        if not volume_range:
            st.error("Please enter a volume range")
            return

        # Clean the input

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

                current_series["barcodes"] = generate_sequential_general_barcodes(
                    current_start_barcode,
                    len(volumes)
                )
            else:
                # Fallback: use the original logic but with proper numeric extraction
                numeric_part = ''.join(c for c in st.session_state.start_barcode if c.isdigit())
                if numeric_part:
                    start_num = int(numeric_part)
                    current_start_num = start_num
                    current_start_barcode = st.session_state.start_barcode.replace(numeric_part, str(current_start_num).zfill(len(numeric_part)))
                    current_series["barcodes"] = generate_sequential_general_barcodes(
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
                    # Get book info - check BigQuery cache first
                    book_data = None

                    # Try BigQuery cache first
                    try:
                        cached_volume = get_volume_info_from_bigquery(series_name, volume_num)
                        if cached_volume:
                            st.success(f"🎯 Using BigQuery cached data for: {series_name} Vol {volume_num}")
                            book_data = cached_volume
                    except Exception as e:
                        st.warning(f"BigQuery cache check failed for {series_name} Vol {volume_num}: {e}")

                    # If no cached data, try APIs
                    if not book_data:
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

                        # Try Google Books first for volume covers (best for English editions)
                        if not cover_url:
                            # Try by ISBN first
                            cover_url = google_books_api.get_cover_image_url(book_data.get("isbn_13"), st.session_state.project_state)

                        # If no ISBN or no cover from ISBN, try searching by title
                        if not cover_url:
                            # Search for specific volume using Google Books
                            search_query = f'"{series_name}" "volume {volume_num}" manga'
                            try:
                                # Use Google Books API directly to search for this specific volume
                                url = f"{google_books_api.base_url}?q={search_query}&maxResults=5"
                                response = requests.get(url, timeout=10, verify=True)
                                response.raise_for_status()
                                data = response.json()

                                if data.get("totalItems", 0) > 0:
                                    for item in data["items"]:
                                        volume_info = item["volumeInfo"]
                                        title = volume_info.get("title", "").lower()

                                        # Check if this looks like the right volume
                                        if f"volume {volume_num}" in title or f"vol. {volume_num}" in title:
                                            image_links = volume_info.get("imageLinks", {})
                                            for size in ["smallThumbnail", "thumbnail", "small", "medium", "large", "extraLarge"]:
                                                if size in image_links:
                                                    cover_url = image_links[size]
                                                    print(f"✅ Google Books found volume {volume_num} cover for: {series_name}")
                                                    break
                                            if cover_url:
                                                break
                            except Exception as e:
                                print(f"❌ Google Books volume cover search failed: {e}")

                        # Try MangaDex as fallback
                        if not cover_url:
                            cover_url = mangadex_fetcher.fetch_cover(series_name, volume_num)

                        # Normalize title quality
                        raw_title = book_data.get("book_title", "")
                        if not raw_title or raw_title.strip() == "":
                            # If blank or null, use default format
                            normalized_title = f"{series_name}: Volume {volume_num}"
                        else:
                            # Check if title includes series name and volume number
                            title_lower = raw_title.lower()
                            series_lower = series_name.lower()

                            has_series_name = series_lower in title_lower
                            has_volume_number = f"volume {volume_num}" in title_lower or f"vol. {volume_num}" in title_lower or f"vol {volume_num}" in title_lower

                            if has_series_name and has_volume_number:
                                # Title already has both, use as-is
                                normalized_title = raw_title
                            elif has_series_name and not has_volume_number:
                                # Has series name but not volume number, append volume
                                normalized_title = f"{raw_title}: Volume {volume_num}"
                            elif not has_series_name and has_volume_number:
                                # Has volume number but not series name, prepend series
                                normalized_title = f"{series_name}: {raw_title}"
                            else:
                                # Missing both, use full format
                                normalized_title = f"{series_name}: {raw_title} (Volume {volume_num})"

                        book = BookInfo(
                            series_name=book_data.get("series_name", series_name),
                            volume_number=volume_num,
                            book_title=normalized_title,
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
                    st.rerun()
                
                processed_count += 1
    else:
        st.session_state.processing_state["is_processing"] = False
        st.session_state.workflow_step = "results"
        st.rerun()


def display_results():
    """Step 7: Results display - Optimized for performance"""
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

        # Volume details table - optimized for performance
        st.subheader("Volume Details")

        # Pre-fetch all cover images for this series to avoid multiple BigQuery calls
        cover_cache = {}
        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            # Batch query for all volume covers in this series
            volume_numbers = [str(book.volume_number) for book in books]
            if volume_numbers:
                query = f'''
                SELECT volume_number, cover_image_data
                FROM `static-webbing-461904-c4.manga_lookup_cache.volume_covers`
                WHERE LOWER(series_name) = LOWER("{series_name}")
                AND volume_number IN ({','.join(volume_numbers)})
                '''

                result = cache.client.query(query).result()
                for row in result:
                    if hasattr(row, 'cover_image_data') and row.cover_image_data:
                        try:
                            image_bytes = base64.b64decode(row.cover_image_data)
                            cover_cache[row.volume_number] = image_bytes
                        except Exception:
                            pass
        except Exception:
            # If batch query fails, fall back to individual queries
            pass

        # Create optimized table using Streamlit's native table for better performance
        table_data = []
        for book in books:
            # Get cover from cache or fallback with error handling
            cover_display = "📚"
            try:
                if book.volume_number in cover_cache:
                    cover_display = f"![Cover](data:image/jpeg;base64,{base64.b64encode(cover_cache[book.volume_number]).decode()})"
                elif hasattr(book, 'cover_image_url') and book.cover_image_url:
                    # Test if the cover URL is accessible
                    if is_cover_url_accessible(book.cover_image_url):
                        cover_display = f"![Cover]({book.cover_image_url})"
            except Exception:
                # If any error occurs, fall back to default icon
                cover_display = "📚"

            table_data.append({
                "Cover": cover_display,
                "Title": book.book_title or f"{series_name} Vol. {book.volume_number}",
                "Vol": book.volume_number,
                "Barcode": book.barcode,
                "ISBN": book.isbn_13 or "N/A",
                "Publisher": book.publisher_name or "N/A",
                "MSRP": f"${float(book.msrp_cost):.2f}" if book.msrp_cost else "N/A",
                "Physical Desc": book.physical_description or "N/A",
                "Summary": (book.description or "No description")[:100] + ("..." if len(book.description or "") > 100 else "")
            })

        # Display as a single table for better performance with proper column widths
        st.dataframe(table_data, use_container_width=True)

        st.divider()

    # Export options
    st.divider()
    st.subheader("Export Options")

    col1, col2 = st.columns(2)

    with col1:
        try:
            # DIAGNOSTIC: Log BookInfo objects before MARC export
            print(f"\n🔍 DIAGNOSTIC: BookInfo objects before MARC export")
            print(f"Number of books: {len(st.session_state.all_books)}")

            for i, book in enumerate(st.session_state.all_books):
                print(f"\nBook {i+1}:")
                print(f"  series_name: {getattr(book, 'series_name', 'MISSING')}")
                print(f"  volume_number: {getattr(book, 'volume_number', 'MISSING')}")
                print(f"  book_title: {repr(getattr(book, 'book_title', 'MISSING'))}")
                print(f"  authors: {getattr(book, 'authors', 'MISSING')}")
                print(f"  barcode: {getattr(book, 'barcode', 'MISSING')}")
                print(f"  msrp_cost: {getattr(book, 'msrp_cost', 'MISSING')}")
                print(f"  copyright_year: {getattr(book, 'copyright_year', 'MISSING')}")
                print(f"  publisher_name: {getattr(book, 'publisher_name', 'MISSING')}")
                print(f"  isbn_13: {getattr(book, 'isbn_13', 'MISSING')}")

            marc_data = export_books_to_marc(st.session_state.all_books)

            # Generate filename with date/time and sanitized series names
            filename = generate_marc_filename(st.session_state.all_books)

            st.download_button(
                "Download MARC File",
                data=marc_data,
                file_name=filename,
                mime="application/marc",
            )
        except Exception as e:
            st.error("Sorry! An error occurred while exporting the file.")
            print(f"Error exporting MARC: {e!s}")

    with col2:
        try:
            from label_generator import generate_pdf_labels
            import pandas as pd

            # Prompt for library identifier with default 'B'
            library_id = st.text_input(
                "Library Identifier",
                value="B",
                max_chars=1,
                help="Enter a 1-character library identifier (e.g., B for main library)"
            )

            # Prepare data for label generation in the format expected by generate_pdf_labels
            label_data = []
            for book in st.session_state.all_books:
                label_data.append({
                    'Holdings Barcode': book.barcode,
                    'Title': book.book_title or f"{book.series_name} Vol. {book.volume_number}",
                    'Author': ', '.join(book.authors) if book.authors else "Unknown Author",
                    'Copyright Year': str(book.copyright_year) if book.copyright_year else "",
                    'Series Info': book.series_name,
                    'Series Number': str(book.volume_number),
                    'Call Number': "",  # Empty for manga
                    'MSRP': str(book.msrp_cost) if book.msrp_cost else "",  # Add MSRP for labels
                    'spine_label_id': "M"  # M for manga
                })

            if label_data:
                # Convert to DataFrame as expected by generate_pdf_labels
                df = pd.DataFrame(label_data)
                pdf_data = generate_pdf_labels(df, library_name="Manga Collection", library_id=library_id)
                st.download_button(
                    "Print Labels",
                    data=pdf_data,
                    file_name="manga_labels.pdf",
                    mime="application/pdf",
                )
            else:
                st.button("Print Labels", disabled=True, help="No books to generate labels for")

        except Exception as e:
            st.error("Sorry! An error occurred while generating labels.")
            print(f"Error generating labels: {e!s}")


def display_queued_series_summary():
    """Display a persistent top sticky bar showing queued series and volume counts"""
    # Only show if we have confirmed series
    confirmed_series = [s for s in st.session_state.series_entries if s.get("confirmed")]
    if not confirmed_series:
        return

    # Calculate totals
    total_series = len(confirmed_series)
    total_volumes = sum(len(s["volumes"]) for s in confirmed_series)

    # Create compact summary
    with st.container():
        st.markdown("""
        <style>
        .queued-series-summary {
            background-color: #374151;
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid #4b5563;
            margin-bottom: 20px;
            font-size: 14px;
            color: white;
        }
        .queued-series-summary h4 {
            margin: 0 0 8px 0;
            color: cyan;
        }
        .series-item {
            display: inline-block;
            background: #1f2937;
            padding: 4px 8px;
            margin: 2px 4px 2px 0;
            border-radius: 4px;
            border: 1px solid #4b5563;
            font-size: 12px;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="queued-series-summary">
            <h4>📚 Queued Series ({total_series} series, {total_volumes} volumes)</h4>
        """, unsafe_allow_html=True)

        # Display series in a compact format
        for series in confirmed_series:
            series_name = series.get("selected_series", series.get("name", "Unknown"))
            volume_count = len(series.get("volumes", []))
            st.markdown(f"""
            <span class="series-item">{series_name} ({volume_count} vols)</span>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main application function"""
    st.set_page_config(
        page_title="Atriuum Manga Importer",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Hide Streamlit menu and footer, and add background styling
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Keep header visible for sidebar show button */
    /* header {visibility: hidden;} */

    /* Sidebar styling - black background */
    section[data-testid="stSidebar"] > div {
        background-color: #000000 !important;
    }

    /* Background styling */
    .stApp {
        background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0)),
                    url('static/background.jpg');
        background-size: cover;
        background-attachment: fixed;
    }

    /* Custom header styling */
    .main-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }

    .logo {
        width: 320px;
        height: 80px;
        border-radius: 10px;
        object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .title-container {
        flex: 1;
    }

    /* Card styling */
    .stContainer {
        background-color: rgba(255,255,255,0.95);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Sidebar with logo and help card
    with st.sidebar:
        # Logo in sidebar
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="static/logo.jpg" style="width: 280px; height: 70px; border-radius: 10px; object-fit: cover; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" alt="AET Logo">
        </div>
        """, unsafe_allow_html=True)

        # App title in sidebar
        st.markdown("""
        <h2 style="text-align: center; color: cyan; margin-bottom: 5px;">📚 Atriuum Manga Importer</h2>
        <p style="text-align: center; color: #6b7280; font-size: 14px; margin-bottom: 20px;">Professional Library Cataloging Tool</p>
        """, unsafe_allow_html=True)

        # About card in sidebar
        with st.expander("ℹ️ About This Project", expanded=True):
            st.markdown("""
            This Manga Collection Importer is a professional library cataloging tool designed to streamline the process of importing manga collections into Atriuum library management systems.

            The application automatically generates comprehensive MARC records with accurate metadata, sequential barcodes, and optimized cover images. It leverages AI-powered metadata lookup, BigQuery caching for performance, and batch processing to handle large collections efficiently.

            Built for library professionals, this tool reduces cataloging time while maintaining high data quality standards.
            """)

        # Help card in sidebar
        with st.expander("📖 How to Use This App", expanded=False):
            st.markdown("""
            ### Step-by-Step Guide

            #### 1. **Starting Barcode**
            - Enter your starting barcode number (e.g., `T000001`, `MANGA001`)
            - Format: Any combination of letters and numbers ending with a number
            - The app will generate sequential barcodes for your volumes

            #### 2. **Series Selection**
            - Enter the manga series name
            - The app searches multiple sources (BigQuery cache, DeepSeek AI, Google Books)
            - Select the correct series from search results
            - View cached cover images or hotlinked covers

            #### 3. **Volume Range**
            - Enter volume numbers using:
              - **Ranges**: `1-10` (volumes 1 through 10)
              - **Individual volumes**: `1,3,5,7`
              - **Mixed**: `1-5,8,10`
              - **Omnibus**: `17-18-19` (3 volumes in 1 book)

            #### 4. **Processing**
            - The app fetches metadata for each volume
            - Uses cached data when available for speed
            - Downloads and compresses cover images
            - Generates barcodes automatically

            #### 5. **Export & Import into Atriuum**

            **MARC File Import:**
            1. **Download MARC File**: Click "Download MARC File" button
            2. **File Format**: `.mrc` file with proper MARC21 encoding
            3. **Import into Atriuum**:
               - Go to **Cataloging** → **Import/Export** → **MARC Import**
               - Select the downloaded `.mrc` file
               - Choose appropriate import profile for manga
               - Map fields as needed (usually works with default settings)
               - Run the import

            **Label Printing:**
            1. **Download Labels**: Click "Print Labels" button
            2. **Print Settings**: Use standard label paper (Avery 5160/5161)
            3. **Apply Labels**: Place on spine or cover of each volume

            #### 6. **Cover Image Storage**
            - **BigQuery Cache**: Compressed thumbnails (20-30KB) stored for fast loading
            - **Fallback Logic**: Uses hotlinked URLs when cached images unavailable
            - **Manual Updates**: Missing covers can be manually added using the generated list

            #### 7. **Troubleshooting**
            - **Missing Covers**: Check the generated missing covers list for manual updates
            - **Barcode Issues**: Ensure barcode format follows your library's system
            - **Import Errors**: Verify MARC file format and Atriuum import settings

            #### 8. **Batch Processing**
            - Add multiple series in one session
            - Each series gets its own barcode range
            - Export all series in a single MARC file

            ### Technical Details
            - **Cover Compression**: Images compressed to ~50KB for BigQuery storage
            - **Metadata Sources**: BigQuery cache, DeepSeek AI, Google Books API
            - **Export Format**: MARC21 with Atriuum-compatible descriptive cataloging
            - **Label Format**: PDF with barcodes, titles, authors, and volume numbers

            Need help? Check the missing covers list for series that need manual cover image updates.
            """)

    # Main content area - simplified header
    st.markdown("""
    <h1 style="color: cyan; margin-bottom: 10px;">📚 Manga Collection Importer</h1>
    <p style="color: #6b7280; font-size: 16px; margin-bottom: 20px;">Import manga collections with automatic metadata lookup and MARC record generation</p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Display queued series summary (sticky top bar)
    display_queued_series_summary()

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
