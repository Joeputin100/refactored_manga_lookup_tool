#!/usr/bin/env python3
import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from dotenv import load_dotenv
from rich import print as rprint

# Load environment variables
load_dotenv()

HTTP_STATUS_TOO_MANY_REQUESTS = 429
EXPECTED_NAME_PARTS = 2
MAX_NAME_PARTS = 2
MIN_MSRP = 10
MAX_MSRP = 30
MIN_COPYRIGHT_YEAR = 1900


@dataclass
class BookInfo:
    """Data class to store comprehensive book information"""

    series_name: str
    volume_number: int
    book_title: str
    authors: list[str]
    msrp_cost: float | None
    isbn_13: str | None
    publisher_name: str | None
    copyright_year: int | None
    description: str | None
    physical_description: str | None
    genres: list[str]
    warnings: list[str]
    barcode: str | None = None
    cover_image_url: str | None = None


class ProjectState:
    """Advanced project state management with SQLite database for performance"""

    def __init__(self, db_file="project_state.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self._create_tables()
        self._ensure_metadata()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Metadata table for global stats
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """,
        )

        # Cached responses table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cached_responses (
                id INTEGER PRIMARY KEY,
                prompt_hash TEXT,
                volume INTEGER,
                response TEXT,
                timestamp TEXT,
                UNIQUE(prompt_hash, volume)
            )
        """,
        )

        # API calls table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY,
                prompt TEXT,
                response TEXT,
                volume INTEGER,
                success BOOLEAN,
                timestamp TEXT
            )
        """,
        )

        # Searches table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY,
                query TEXT,
                books_found INTEGER,
                timestamp TEXT
            )
        """,
        )

        # Cached cover images
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cached_cover_images (
                id INTEGER PRIMARY KEY,
                isbn TEXT UNIQUE,
                url TEXT,
                timestamp TEXT
            )
        """,
        )

        self.conn.commit()

    def _ensure_metadata(self):
        """Ensure default metadata exists"""
        cursor = self.conn.cursor()
        defaults = {
            "interaction_count": "0",
            "total_books_found": "0",
            "start_time": datetime.now(UTC).isoformat(),
        }
        for key, value in defaults.items():
            cursor.execute(
                "INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)",
                (key, value),
            )
        self.conn.commit()

    def _get_metadata(self, key: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else "0"

    def _set_metadata(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def record_api_call(
        self,
        prompt: str,
        response: str,
        volume: int,
        *,
        success: bool = True,
    ):
        """Record API call with full details for caching"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(UTC).isoformat()

        # Insert API call
        cursor.execute(
            """
            INSERT INTO api_calls (prompt, response, volume, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (prompt, response, volume, success, timestamp),
        )

        # Cache successful responses
        if success:
            prompt_hash = f"{prompt[:100]}_{volume}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO cached_responses (prompt_hash, volume, response, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (prompt_hash, volume, response, timestamp),
            )

        self.conn.commit()

    def get_cached_response(self, prompt: str, volume: int) -> str | None:
        """Get cached response if available"""
        cursor = self.conn.cursor()
        prompt_hash = f"{prompt[:100]}_{volume}"
        cursor.execute(
            "SELECT response FROM cached_responses WHERE prompt_hash = ? AND volume = ?",
            (prompt_hash, volume),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def record_interaction(self, search_query: str, books_found: int):
        """Record a new user interaction"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(UTC).isoformat()

        # Update metadata
        interaction_count = int(self._get_metadata("interaction_count")) + 1
        total_books = int(self._get_metadata("total_books_found")) + books_found
        self._set_metadata("interaction_count", str(interaction_count))
        self._set_metadata("total_books_found", str(total_books))

        # Insert search
        cursor.execute(
            "INSERT INTO searches (query, books_found, timestamp) VALUES (?, ?, ?)",
            (search_query, books_found, timestamp),
        )
        self.conn.commit()

    def get_cached_cover_image(self, isbn_key: str) -> str | None:
        """Get cached cover image URL by ISBN key"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT url FROM cached_cover_images WHERE isbn = ?",
            (isbn_key,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def cache_cover_image(self, isbn_key: str, url: str):
        """Cache a cover image URL"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(UTC).isoformat()
        cursor.execute(
            "INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp) VALUES (?, ?, ?)",
            (isbn_key, url, timestamp),
        )
        self.conn.commit()

    def find_similar_series(self, series_name: str) -> list[str]:
        """Find similar series names from API call history"""
        cursor = self.conn.cursor()

        # Search for series names in API calls
        cursor.execute("""
            SELECT DISTINCT json_extract(response, '$.series_name') as series
            FROM api_calls
            WHERE json_extract(response, '$.series_name') IS NOT NULL
            AND json_extract(response, '$.series_name') != ''
            ORDER BY timestamp DESC
            LIMIT 20
        """)

        all_series = [row[0] for row in cursor.fetchall() if row[0]]

        # Simple similarity matching - series that contain the input name
        similar_series = []
        for existing_series in all_series:
            if (series_name.lower() in existing_series.lower() or
                existing_series.lower() in series_name.lower()):
                similar_series.append(existing_series)

        # Remove duplicates and limit results
        return list(dict.fromkeys(similar_series))[:5]


class DataValidator:
    """Handles data validation and formatting"""

    @staticmethod
    def format_title(title: str) -> str:
        """Format title with leading articles shifted to the end"""
        articles = ["the", "a", "an"]
        words = title.split()

        if words and words[0].lower() in articles:
            article = words[0]
            rest = " ".join(words[1:])
            return f"{rest}, {article.capitalize()}"

        return title

    @staticmethod
    def format_author_name(author_name: str) -> str:
        """Format author name as 'Last, First M.'"""
        if not author_name:
            return ""

        # Check if already in "Last, First" format
        if ", " in author_name:
            return author_name

        # Handle common Japanese name formats
        name_parts = author_name.strip().split()

        if len(name_parts) == EXPECTED_NAME_PARTS:
            # Assume "First Last" format
            return f"{name_parts[1]}, {name_parts[0]}"
        if len(name_parts) == 1:
            # Single name (like "Oda")
            return name_parts[0]
        # Complex name, try to handle
        if any(part.endswith("-") for part in name_parts):
            # Handle hyphenated names
            return author_name
        # Default: assume first part is first name, last part is last name
        return f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"

    @staticmethod
    def format_authors_list(authors: list[str]) -> str:
        """Format list of authors as comma-separated 'Last, First M.'"""
        if not authors:
            return ""
        formatted_authors = [
            DataValidator.format_author_name(author) for author in authors
        ]
        return ", ".join(formatted_authors)


class DeepSeekAPI:
    """Handles DeepSeek API interactions with rate limiting and error handling"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            msg = "DEEPSEEK_API_KEY not found in environment variables"
            raise ValueError(msg)

        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # Using DeepSeek-V3.2-Exp (non-thinking mode)
        self.last_request_time = time.time()

    def correct_series_name(self, series_name: str) -> list[str]:
        """Use DeepSeek API to correct and suggest manga series names"""
        prompt = f"""
        Given the manga series name "{series_name}", provide 3-5 corrected or alternative names
        that are actual manga series or editions.
        that are actual manga series.

        IMPORTANT: If "{series_name}" is already a correct manga series name, include it as the first suggestion.
        If "{series_name}" is a valid manga series, prioritize it over other suggestions.
        For popular series with multiple editions, include different formats:
        - Regular edition (individual volumes)
        - Omnibus edition (3 volumes per book)
        - Colossal edition (5 volumes per book)
        Format edition names as "Series Name (Edition Type)"

        Only include actual manga series names, not unrelated popular series.
        If "{series_name}" is misspelled or incomplete, provide the correct full name first.

        Prioritize the main series over spinoffs, sequels, or adaptations.
        If the series has multiple parts (like Tokyo Ghoul and Tokyo Ghoul:re), include the main series first.
        Include recent and ongoing series, not just completed ones.

        Return only the names as a JSON list, no additional text.

        Example format: ["Attack on Titan (Regular Edition)", "Attack on Titan (Omnibus Edition)", "Attack on Titan (Colossal Edition)", "One Piece", "Naruto"]
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.3,
        }

        content = None  # Initialize content variable

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Debug logging

            # Parse JSON response
            suggestions = json.loads(content)

            # Filter out any None values from suggestions
            suggestions = [s for s in suggestions if s is not None]

            # Debug logging

            # Ensure the original series name is included if it's valid
            # Check if the original name is in the suggestions, if not add it
            if series_name not in suggestions:
                # Check if any suggestion contains the original name (case-insensitive)
                original_in_suggestions = any(
                    suggestion and series_name.lower() in suggestion.lower()
                    for suggestion in suggestions
                )
                if not original_in_suggestions:
                    # Add original name as first suggestion
                    suggestions.insert(0, series_name)

        except OSError as e:
            rprint(f"[red]Error using DeepSeek API: {e}[/red]")
            return [series_name]  # Fallback to original name
        else:
            return suggestions

    def get_book_info(
        self,
        series_name: str,
        volume_number: int,
        project_state: ProjectState,
    ) -> dict | None:
        """Get comprehensive book information using DeepSeek API"""

        # Create comprehensive prompt
        prompt = self._create_comprehensive_prompt(series_name, volume_number)

        # Check cache first
        cached_response = project_state.get_cached_response(prompt, volume_number)
        if cached_response:
            rprint(f"[cyan]📚 Using cached data for volume {volume_number}[/cyan]")
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                rprint("[yellow]⚠️ Cached data corrupted, fetching fresh data[/yellow]")

        # If we get here, we need to make a new API call
        rprint(f"[blue]🔍 Making API call for volume {volume_number}[/blue]")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.1,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # Parse JSON response
            content = content.strip()
            content = content.removeprefix("```json")
            content = content.removesuffix("```")
            content = content.strip()
            try:
                book_data = json.loads(content)
            except json.JSONDecodeError as e:
                rprint(
                    f"[red]Invalid JSON response for volume {volume_number}: {e}[/red]",
                )
                rprint(f"[red]Content: {content[:500]}[/red]")
                project_state.record_api_call(
                    prompt,
                    content,
                    volume_number,
                    success=False,
                )
            if not book_data.get("number_of_extant_volumes"):
                google_api = GoogleBooksAPI()
                book_data["number_of_extant_volumes"] = google_api.get_total_volumes(
                    series_name,
                )
                return None

            # Record successful API call
            project_state.record_api_call(prompt, content, volume_number, success=True)

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                rprint(
                    f"[yellow]Rate limit exceeded for volume {volume_number}, waiting 5 seconds...[/yellow]",
                )
                time.sleep(5)
                return self.get_book_info(series_name, volume_number, project_state)
            rprint(f"[red]HTTP error for volume {volume_number}: {e}[/red]")
        except OSError as e:
            rprint(f"[red]Error fetching data for volume {volume_number}: {e}[/red]")
            return None
        else:
            return book_data

    def _create_comprehensive_prompt(self, series_name: str, volume_number: int) -> str:
        """Create comprehensive prompt for book information"""
        return f"""
        Provide comprehensive information for the manga "{series_name}" Volume {volume_number}.

        Return a JSON object with these exact fields:
        - "series_name": The official series name
        - "book_title": The specific title for this volume (e.g., "Volume 1: The Beginning")
        - "authors": List of author names (e.g., ["Eiichiro Oda", "Masashi Kishimoto"])
        - "msrp_cost": The retail price in USD (e.g., 9.99)
        - "isbn_13": The 13-digit ISBN (e.g., "9781421502670")
        - "publisher_name": The publisher (e.g., "VIZ Media", "Kodansha Comics")
        - "copyright_year": The copyright year (e.g., 2003)
        - "description": A brief description of the volume's content
        - "physical_description": Physical details like pages, dimensions (e.g., "192 pages, 5 x 7.5 inches")
        - "genres": List of genres (e.g., ["Action", "Adventure", "Fantasy"])
        - "number_of_extant_volumes": Total number of volumes in the series
        - "cover_image_url": URL to the cover image if available

        Important:
        - Return ONLY valid JSON, no additional text
        - Use exact field names as specified
        - If information is unavailable, use null or empty values
        - Prioritize English edition information
        - For manga, typical MSRP is $9.99-$12.99 for standard volumes
        """


class GoogleBooksAPI:
    """Handles Google Books API interactions for cover image retrieval using keyless queries"""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    def _select_cover_image(self, image_links: dict) -> str | None:
        """Select the best available cover image from Google Books image links."""
        for size in ["smallThumbnail", "thumbnail", "small", "medium", "large", "extraLarge"]:
            if size in image_links:
                return image_links[size]
        return None

    def get_cover_image_url(
        self,
        isbn: str,
        project_state: ProjectState | None = None,
    ) -> str | None:
        """Get cover image URL for a book by ISBN using keyless Google Books API"""
        if not isbn:
            return None

        # Check cache first if project_state is provided
        if project_state:
            cached_url = project_state.get_cached_cover_image(f"isbn:{isbn}")
            if cached_url:
                return cached_url

        # Construct the keyless API URL
        url = f"{self.base_url}?q=isbn:{isbn}&maxResults=1"

        try:
            # Make the keyless HTTP request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("totalItems", 0) == 0:
                return None

            volume_info = data["items"][0]["volumeInfo"]
            image_links = volume_info.get("imageLinks", {})

            # Get the small thumbnail cover image URL
            cover_url = image_links.get("smallThumbnail")

            # If small thumbnail not available, try other sizes
            if not cover_url:
                for size in ["thumbnail", "small", "medium", "large", "extraLarge"]:
                    if size in image_links:
                        cover_url = image_links[size]
                        break

            if cover_url:
                # Cache the result
                if project_state:
                    project_state.cache_cover_image(f"isbn:{isbn}", cover_url)
            else:
                pass

        except requests.exceptions.RequestException:
            # Silently fail - cover images are optional
            return None
        except OSError:
            return None
        else:
            return cover_url

    def get_total_volumes(self, series_name: str) -> int:
        """Get the total number of volumes in a manga series using Google Books API"""
        query = f'intitle:"{series_name}" manga'
        url = f"{self.base_url}?q={query}&maxResults=40&orderBy=relevance"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("totalItems", 0) == 0:
                return 0

            # Extract volume numbers from titles
            volume_numbers = []
            for item in data.get("items", []):
                title = item["volumeInfo"].get("title", "").lower()
                # Look for volume patterns

                match = re.search(r"volume (\d+)", title)
                if match:
                    volume_numbers.append(int(match.group(1)))

            return max(volume_numbers) if volume_numbers else 0

        except OSError:
            return 0


class VertexAIClient:
    """Handles Vertex AI API interactions for manga data"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            msg = "GEMINI_API_KEY not found in environment variables"
            raise ValueError(msg)

        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    def correct_series_name(self, series_name: str) -> list[str]:
        """Use Vertex AI API to correct and suggest manga series names"""
        prompt = f"""
        Given the manga series name "{series_name}", provide 3-5 corrected or alternative names
        that are actual manga series or editions.

        IMPORTANT: If "{series_name}" is already a correct manga series name, include it as the first suggestion.
        If "{series_name}" is a valid manga series, prioritize it over other suggestions.
        For popular series with multiple editions, include different formats:
        - Regular edition (individual volumes)
        - Omnibus edition (3 volumes per book)
        - Colossal edition (5 volumes per book)
        Format edition names as "Series Name (Edition Type)"

        Only include actual manga series names, not unrelated popular series.
        If "{series_name}" is misspelled or incomplete, provide the correct full name first.

        Prioritize the main series over spinoffs, sequels, or adaptations.
        If the series has multiple parts (like Tokyo Ghoul and Tokyo Ghoul:re), include the main series first.
        Include recent and ongoing series, not just completed ones.

        Return only the names as a JSON list, no additional text.

        Example format: ["Attack on Titan (Regular Edition)", "Attack on Titan (Omnibus Edition)", "Attack on Titan (Colossal Edition)", "One Piece", "Naruto"]
        """

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 200,
            }
        }

        url = f"{self.base_url}?key={self.api_key}"

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]

            # Parse JSON response
            suggestions = json.loads(content)

            # Filter out any None values from suggestions
            suggestions = [s for s in suggestions if s is not None]

            # Ensure the original series name is included if it's valid
            if series_name not in suggestions:
                original_in_suggestions = any(
                    suggestion and series_name.lower() in suggestion.lower()
                    for suggestion in suggestions
                )
                if not original_in_suggestions:
                    suggestions.insert(0, series_name)

        except OSError as e:
            rprint(f"[red]Error using Vertex AI API: {e}[/red]")
            return [series_name]  # Fallback to original name
        else:
            return suggestions


def parse_volume_range(volume_input: str) -> list[int]:
    """Parse volume range input like '1-5,7,10' and omnibus formats like '17-18-19' into list of volume numbers"""
    volumes = []

    # Split by commas
    parts = [part.strip() for part in volume_input.split(",")]

    for part in parts:
        if "-" in part:
            # Count the number of hyphens to determine format
            hyphens_count = part.count("-")

            if hyphens_count == 1:
                # Handle range like '1-5' (single range)
                try:
                    start, end = map(int, part.split("-"))
                    volumes.extend(range(start, end + 1))
                except ValueError as e:
                    msg = f"Invalid volume range format: {part}"
                    raise ValueError(msg) from e
            else:
                # Handle omnibus format like '17-18-19' (multiple volumes in one book)
                try:
                    # Split by hyphens and convert all parts to integers
                    omnibus_volumes = list(map(int, part.split("-")))
                    volumes.extend(omnibus_volumes)
                except ValueError as e:
                    msg = f"Invalid omnibus format: {part}"
                    raise ValueError(msg) from e
        else:
            # Handle single volume like '7'
            try:
                volumes.append(int(part))
            except ValueError as e:
                msg = f"Invalid volume number: {part}"
                raise ValueError(msg) from e

    # Remove duplicates and sort
    return sorted(set(volumes))


def generate_sequential_barcodes(start_barcode: str, count: int) -> list[str]:
    """Generate sequential barcodes from a starting barcode"""
    barcodes = []

    # Extract prefix and numeric part

    match = re.match(r"([A-Za-z]*)(\d+)", start_barcode)

    if not match:
        msg = f"Invalid barcode format: {start_barcode}. Expected format like 'T000001'"
        raise ValueError(
            msg,
        )

    prefix = match.group(1) or ""
    start_num = int(match.group(2))
    num_digits = len(match.group(2))

    for i in range(count):
        current_num = start_num + i
        barcode = f"{prefix}{current_num:0{num_digits}d}"
        barcodes.append(barcode)

    return barcodes


class VertexAIAPI:
    """Handles Google Vertex AI API interactions for comprehensive manga data"""

    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.model_name = os.getenv("VERTEX_AI_MODEL", "gemini-1.5-flash")

        # Check if required environment variables are set
        if not self.project_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable is required for Vertex AI"
            )

    def _call_vertex_ai(self, prompt: str) -> str:
        """Make a call to Vertex AI API"""
        try:
            # Import Vertex AI (this would require google-cloud-aiplatform)
            from google.cloud import aiplatform

            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)

            # Create the model
            model = aiplatform.GenerativeModel(self.model_name)

            # Generate response
            response = model.generate_content(prompt)
            return response.text

        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform is required for Vertex AI. "
                "Install with: pip install google-cloud-aiplatform"
            )
        except Exception as e:
            raise Exception(f"Vertex AI API error: {e}")

    def get_comprehensive_series_info(self, series_name: str) -> dict:
        """Get comprehensive series information using Vertex AI"""
        prompt = f"""
        Please provide comprehensive information about the manga series "{series_name}" in JSON format.
        Include the following fields:
        - series_name: The official title
        - authors: List of authors/artists
        - number_of_extant_volumes: Total number of volumes published
        - description: Detailed plot summary
        - genres: List of genres
        - publisher: Main publisher
        - original_release_year: Year the series started
        - status: Current status (ongoing, completed, hiatus, etc.)
        - alternative_titles: Any alternative or English titles
        - spin_offs: List of related spin-off series
        - adaptations: Any anime, live-action, or other adaptations
        - notable_characters: Main characters
        - themes: Major themes explored
        - awards: Any awards or recognitions

        Please provide accurate, up-to-date information.
        """

        try:
            response_text = self._call_vertex_ai(prompt)

            # Parse the JSON response
            import json
            data = json.loads(response_text)

            return {
                "series_name": data.get("series_name", series_name),
                "authors": data.get("authors", []),
                "number_of_extant_volumes": data.get("number_of_extant_volumes", 0),
                "description": data.get("description", ""),
                "genres": data.get("genres", []),
                "publisher": data.get("publisher", ""),
                "original_release_year": data.get("original_release_year"),
                "status": data.get("status", ""),
                "alternative_titles": data.get("alternative_titles", []),
                "spin_offs": data.get("spin_offs", []),
                "adaptations": data.get("adaptations", []),
                "notable_characters": data.get("notable_characters", []),
                "themes": data.get("themes", []),
                "awards": data.get("awards", [])
            }

        except Exception as e:
            # If Vertex AI fails, return minimal data
            return {
                "series_name": series_name,
                "authors": [],
                "number_of_extant_volumes": 0,
                "description": "",
                "genres": [],
                "publisher": "",
                "original_release_year": None,
                "status": "",
                "alternative_titles": [],
                "spin_offs": [],
                "adaptations": [],
                "notable_characters": [],
                "themes": [],
                "awards": []
            }

    def get_book_info(
        self, series_name: str, volume_number: int, project_state: ProjectState | None = None
    ) -> dict | None:
        """Get detailed information for a specific volume"""
        # Get comprehensive series info first
        series_info = self.get_comprehensive_series_info(series_name)

        # Create volume-specific info
        volume_info = {
            "series_name": series_info["series_name"],
            "volume_number": volume_number,
            "book_title": f"{series_info['series_name']} Volume {volume_number}",
            "authors": series_info["authors"],
            "number_of_extant_volumes": series_info["number_of_extant_volumes"],
            "description": series_info["description"],
            "genres": series_info["genres"],
            "publisher_name": series_info["publisher"],
            "copyright_year": series_info["original_release_year"],
            "warnings": []
        }

        return volume_info

    def correct_series_name(self, series_name: str) -> list[str]:
        """Get corrected/suggested series names using Vertex AI"""
        prompt = f"""
        Given the manga series name "{series_name}", provide a list of possible correct or alternative names.
        Include:
        1. The most likely correct official title
        2. Any common alternative titles or translations
        3. Any spin-off series that might be confused with the main series
        4. Different editions (omnibus, collector's edition, etc.)

        Return only a JSON list of strings, no additional text.
        """

        try:
            response_text = self._call_vertex_ai(prompt)
            import json
            suggestions = json.loads(response_text)

            # Ensure we have at least the original name
            if series_name not in suggestions:
                suggestions.insert(0, series_name)

            return suggestions[:10]  # Limit to 10 suggestions

        except Exception:
            # If Vertex AI fails, return just the original name
            return [series_name]


def process_book_data(
    raw_data: dict,
    volume_number: int,
    google_books_api: GoogleBooksAPI | None = None,
    project_state: ProjectState | None = None,
) -> BookInfo:
    """Process raw API data into structured BookInfo"""
    warnings = []

    # Extract and validate data
    series_name = DataValidator.format_title(raw_data.get("series_name", ""))
    book_title = DataValidator.format_title(
        raw_data.get("book_title", f"{series_name} (Volume {volume_number})"),
    )

    # Ensure series name is in the title if missing
    if series_name and series_name.lower() not in book_title.lower():
        book_title = f"{series_name}: {book_title}"

    # Handle authors - ensure they're in list format
    authors_raw = raw_data.get("authors", [])
    if isinstance(authors_raw, str):
        # Check if the string contains multiple authors separated by commas
        # Look for patterns that indicate multiple authors vs single author with comma
        if ", " in authors_raw:
            # Check if it's likely a single author in "Last, First" format
            parts = authors_raw.split(", ")
            if (
                len(parts) == EXPECTED_NAME_PARTS
                and len(parts[0].split()) <= MAX_NAME_PARTS
                and len(parts[1].split()) <= MAX_NAME_PARTS
            ):
                # Likely a single author in "Last, First" format
                authors = [authors_raw.strip()]
            else:
                # Likely multiple authors, split by comma
                authors = [author.strip() for author in authors_raw.split(",")]
        else:
            # No commas, treat as single author
            authors = [authors_raw.strip()]
    else:
        authors = authors_raw

    # Validate MSRP
    msrp_cost = raw_data.get("msrp_cost")
    if msrp_cost is None:
        warnings.append("No MSRP found")
    else:
        try:
            msrp_cost = float(msrp_cost)
            if msrp_cost < MIN_MSRP:
                rounded_msrp = 10.0
                warnings.append(
                    f"MSRP ${msrp_cost:.2f} is below minimum $10 (rounded up to ${rounded_msrp:.2f})",
                )
            elif msrp_cost > MAX_MSRP:
                warnings.append(f"MSRP ${msrp_cost:.2f} exceeds typical maximum $30")
        except (ValueError, TypeError):
            warnings.append("Invalid MSRP format")
            msrp_cost = None

    # Validate copyright year
    copyright_year = None
    date_str = str(raw_data.get("copyright_year", ""))
    if date_str:

        year_patterns = [r"\b(19|20)\d{2}\b", r"\b\d{4}\b"]
        for pattern in year_patterns:
            matches = re.findall(pattern, date_str)
            if matches:
                year = int(matches[0])
                if MIN_COPYRIGHT_YEAR <= year <= datetime.now(UTC).year + 1:
                    copyright_year = year
                    break
    if not copyright_year:
        warnings.append("Could not extract valid copyright year")

    # Handle genres
    genres_raw = raw_data.get("genres", [])
    genres = (
        [genre.strip() for genre in genres_raw.split(",")]
        if isinstance(genres_raw, str)
        else genres_raw
    )

    # Extract cover image URL if available from DeepSeek data
    cover_image_url = raw_data.get("cover_image_url")

    # If no cover image from DeepSeek and Google Books API is available, try to fetch it
    if not cover_image_url and google_books_api:
        isbn = raw_data.get("isbn_13")
        if isbn:
            cover_image_url = google_books_api.get_cover_image_url(
                isbn,
                project_state=project_state,
            )
            # Debug: Print cover image status
            if cover_image_url:
                pass
            else:
                pass

    return BookInfo(
        series_name=series_name,
        volume_number=volume_number,
        book_title=book_title,
        authors=authors,
        msrp_cost=msrp_cost,
        isbn_13=raw_data.get("isbn_13"),
        publisher_name=raw_data.get("publisher_name"),
        copyright_year=copyright_year,
        description=raw_data.get("description"),
        physical_description=raw_data.get("physical_description"),
        genres=genres,
        warnings=warnings,
        cover_image_url=cover_image_url,
    )