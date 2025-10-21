import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import timezone, datetime
from typing import Union

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
    msrp_cost: Union[float, None]
    isbn_13: Union[str, None]
    publisher_name: Union[str, None]
    copyright_year: Union[int, None]
    description: Union[str, None]
    physical_description: Union[str, None]
    genres: list[str]
    warnings: list[str]
    barcode: Union[str, None] = None
    cover_image_url: Union[str, None] = None


class ProjectState:
    """Advanced project state management with SQLite database for performance"""

    def __init__(self, db_file="project_state.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self._create_tables()
        self._ensure_metadata()

    def close(self):
        """Close database connection to prevent resource leaks"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection"""
        self.close()

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

        # Cached series information table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cached_series_info (
                series_name TEXT PRIMARY KEY,
                series_info TEXT,
                timestamp TEXT
            )
        """,
        )

        # API usage tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY,
                api_name TEXT,
                endpoint TEXT,
                tokens_used INTEGER,
                cost_estimate REAL,
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
            "start_time": datetime.now(timezone.utc).isoformat(),
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
        timestamp = datetime.now(timezone.utc).isoformat()

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

    def get_cached_response(self, prompt: str, volume: int) -> Union[str, None]:
        """Get cached response if available"""
        # Always return None to disable caching
        return None

    def record_search(self, search_query: str, books_found: int):
        """Record a new user interaction"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()

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

    def get_cached_cover_image(self, isbn_key: str) -> Union[str, None]:
        """Get cached cover image URL by ISBN key"""
        # Always return None to disable caching
        return None

    def cache_cover_image(self, isbn_key: str, url: str):
        """Cache a cover image URL"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()
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
            if (
                series_name.lower() in existing_series.lower()
                or existing_series.lower() in series_name.lower()
            ):
                similar_series.append(existing_series)

        # Remove duplicates and limit results
        return list(dict.fromkeys(similar_series))[:5]

    def cache_series_info(self, series_name: str, series_info: dict) -> None:
        """Cache series information for faster lookups"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cached_series_info
            (series_name, series_info, timestamp)
            VALUES (?, ?, ?)
        """, (series_name, json.dumps(series_info), datetime.now(timezone.utc).isoformat()))
        self.conn.commit()
        print(f"💾 Cached series info for: {series_name}")

    def get_cached_series_info(self, series_name: str) -> Union[dict, None]:
        """Get cached series information if available (permanent cache)"""
        # Always return None to disable caching
        return None

    def track_api_usage(self, api_name: str, endpoint: str, tokens_used: int):
        """Track API usage and estimate costs"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Cost estimates per 1K tokens (approximate rates as of 2024)
        cost_rates = {
            "deepseek": 0.00014,  # $0.14 per 1K tokens
            "vertex_ai": 0.00035,  # $0.35 per 1K tokens
            "google_books": 0.0,   # Free API
            "mal": 0.0,           # Free API
            "mangadex": 0.0       # Free API
        }

        cost_estimate = (tokens_used / 1000) * cost_rates.get(api_name.lower(), 0.0)

        cursor.execute("""
            INSERT INTO api_usage (api_name, endpoint, tokens_used, cost_estimate, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (api_name, endpoint, tokens_used, cost_estimate, timestamp))

        self.conn.commit()

    def generate_cost_report(self) -> dict:
        """Generate API usage and cost report (for internal monitoring)"""
        cursor = self.conn.cursor()

        # Get total usage by API
        cursor.execute("""
            SELECT
                api_name,
                COUNT(*) as call_count,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM api_usage
            GROUP BY api_name
        """)

        api_summary = {}
        total_cost = 0.0
        total_calls = 0

        for row in cursor.fetchall():
            api_name, call_count, total_tokens, api_cost = row
            api_summary[api_name] = {
                "calls": call_count,
                "tokens": total_tokens,
                "cost": api_cost
            }
            total_cost += api_cost
            total_calls += call_count

        # Get recent usage (last 30 days)
        cursor.execute("""
            SELECT
                api_name,
                COUNT(*) as call_count,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM api_usage
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY api_name
        """)

        recent_summary = {}
        recent_cost = 0.0
        recent_calls = 0

        for row in cursor.fetchall():
            api_name, call_count, total_tokens, api_cost = row
            recent_summary[api_name] = {
                "calls": call_count,
                "tokens": total_tokens,
                "cost": api_cost
            }
            recent_cost += api_cost
            recent_calls += call_count

        return {
            "total": {
                "calls": total_calls,
                "cost": total_cost
            },
            "recent_30_days": {
                "calls": recent_calls,
                "cost": recent_cost
            },
            "api_breakdown": api_summary,
            "recent_breakdown": recent_summary
        }


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
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'VERTEX_AI_PROJECT_ID' in st.secrets:
                self.project_id = st.secrets["VERTEX_AI_PROJECT_ID"]
                self.location = st.secrets.get("VERTEX_AI_LOCATION", "us-central1")
            else:
                self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
                self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        except ImportError:
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID must be set.")
        
        import vertexai
        vertexai.init(project=self.project_id, location=self.location)
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
                verify=True,  # Enable SSL verification
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
            logging.error(f"Error using DeepSeek API: {e}")
            return [series_name]  # Fallback to original name
        else:
            return suggestions

    def get_book_info(
        self,
        series_name: str,
        volume_number: int,
        project_state: ProjectState,
        retry_count: int = 0,
    ) -> Union[dict, None]:
        """Get comprehensive book information using DeepSeek API"""

        # Maximum retry limit to prevent infinite recursion
        MAX_RETRIES = 3
        if retry_count >= MAX_RETRIES:
            rprint(f"[red]❌ Maximum retry limit ({MAX_RETRIES}) reached for volume {volume_number}. Giving up.[/red]")
            return None

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
        if retry_count > 0:
            rprint(f"[yellow]🔄 Retry {retry_count}/{MAX_RETRIES} for volume {volume_number}[/yellow]")
        else:
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
                verify=True,  # Enable SSL verification
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

            # Track API usage with token estimation
            # Estimate tokens: prompt + response (rough approximation)
            estimated_tokens = len(prompt.split()) + len(content.split())
            project_state.track_api_usage("deepseek", "chat/completions", estimated_tokens)

        except requests.exceptions.HTTPError as e:
            if e.response:
                status_code = e.response.status_code
                if status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                    rprint(
                        f"[yellow]Rate limit exceeded for volume {volume_number}, waiting 10 seconds...[/yellow]",
                    )
                    time.sleep(10)
                    return self.get_book_info(series_name, volume_number, project_state, retry_count + 1)
                elif status_code == 400:
                    rprint(f"[red]Bad request for volume {volume_number}: {e}[/red]")
                    # Check for context window limitations
                    error_text = str(e.response.text).lower()
                    if "context" in error_text or "token" in error_text:
                        rprint("[red]Context window limitation detected. Try reducing prompt length.[/red]")
                elif status_code == 401:
                    rprint(f"[red]Authentication failed for volume {volume_number}. Check API key.[/red]")
                elif status_code == 402:
                    rprint(f"[red]Payment required for volume {volume_number}. Check account balance.[/red]")
                elif status_code == 429:
                    rprint(f"[yellow]Rate limit exceeded for volume {volume_number}, waiting 15 seconds...[/yellow]")
                    time.sleep(15)
                    return self.get_book_info(series_name, volume_number, project_state, retry_count + 1)
                elif status_code >= 500:
                    rprint(f"[yellow]Server error for volume {volume_number}, waiting 5 seconds...[/yellow]")
                    time.sleep(5)
                    return self.get_book_info(series_name, volume_number, project_state, retry_count + 1)
                else:
                    rprint(f"[red]HTTP error {status_code} for volume {volume_number}: {e}[/red]")
            else:
                rprint(f"[red]HTTP error for volume {volume_number}: {e}[/red]")
        except requests.exceptions.ConnectionError:
            rprint(f"[yellow]Connection error for volume {volume_number}, waiting 10 seconds...[/yellow]")
            time.sleep(10)
            return self.get_book_info(series_name, volume_number, project_state, retry_count + 1)
        except requests.exceptions.Timeout:
            rprint(f"[yellow]Timeout for volume {volume_number}, waiting 5 seconds...[/yellow]")
            time.sleep(5)
            return self.get_book_info(series_name, volume_number, project_state, retry_count + 1)
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
        - For manga, typical MSRP is $9.99-2.99 for standard volumes
        """


class GoogleBooksAPI:
    """Handles Google Books API interactions for cover image retrieval using keyless queries"""

    def __init__(self):
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'VERTEX_AI_PROJECT_ID' in st.secrets:
                self.project_id = st.secrets["VERTEX_AI_PROJECT_ID"]
                self.location = st.secrets.get("VERTEX_AI_LOCATION", "us-central1")
            else:
                self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
                self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        except ImportError:
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID must be set.")
        
        import vertexai
        vertexai.init(project=self.project_id, location=self.location)

    def _select_cover_image(self, image_links: dict) -> Union[str, None]:
        """Select the best available cover image from Google Books image links."""
        for size in ["smallThumbnail", "thumbnail", "small", "medium", "large", "extraLarge"]:
            if size in image_links:
                return image_links[size]
        return None

    def get_cover_image_url(
        self,
        isbn: str,
        project_state: Union[ProjectState, None] = None,
    ) -> Union[str, None]:
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
            response = requests.get(url, timeout=10, verify=True)
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
            response = requests.get(url, timeout=10, verify=True)
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


class VertexAIAPI:
    """Handles Google Vertex AI API interactions for comprehensive manga data using REST APIs"""

    def __init__(self):
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'VERTEX_AI_PROJECT_ID' in st.secrets:
                self.project_id = st.secrets["VERTEX_AI_PROJECT_ID"]
                self.location = st.secrets.get("VERTEX_AI_LOCATION", "us-central1")
            else:
                self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
                self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        except ImportError:
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID must be set.")
        
        import vertexai
        vertexai.init(project=self.project_id, location=self.location)


def generate_sequential_barcodes(start_isbn: str, count: int) -> list[str]:
    """
    Generate sequential barcodes starting from a given ISBN.
    
    Args:
        start_isbn: Starting ISBN-13 number
        count: Number of sequential barcodes to generate
        
    Returns:
        List of sequential ISBN-13 numbers
    """
    import re
    
    # Remove any non-digit characters
    clean_isbn = re.sub(r"[^\\d]", "", start_isbn)
    
    # Ensure it's a 13-digit ISBN
    if len(clean_isbn) != 13:
        raise ValueError(f"Invalid ISBN-13 format: {start_isbn}")
    
    barcodes = []
    base_number = int(clean_isbn[:-1])  # Remove check digit
    
    for i in range(count):
        current_number = base_number + i
        
        # Calculate ISBN-13 check digit
        digits = [int(d) for d in str(current_number)]
        
        # ISBN-13 check digit calculation
        sum_ = 0
        for j, digit in enumerate(digits):
            if j % 2 == 0:
                sum_ += digit
            else:
                sum_ += digit * 3
        
        check_digit = (10 - (sum_ % 10)) % 10
        
        # Create full ISBN-13
        full_isbn = f"{current_number}{check_digit}"
        barcodes.append(full_isbn)
    
    return barcodes
