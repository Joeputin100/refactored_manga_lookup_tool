#!/usr/bin/env python3
"""
Enhanced VertexAIAPI class with Gemini 2.5 models and fallback logic
"""

import json
import re
import time
import os
from typing import Dict, Any, Optional


class EnhancedVertexAIAPI:
    """Enhanced Vertex AI API with Gemini 2.5 models and fallback logic"""

    def __init__(self):
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'vertex_ai' in st.secrets:
                # Read from [vertex_ai] section in secrets.toml
                vertex_secrets = st.secrets["vertex_ai"]
                self.project_id = vertex_secrets.get("project_id")
                self.location = vertex_secrets.get("location", "us-central1")
                # For service account key, we need the entire JSON content
                self.service_account_info = {
                    "type": vertex_secrets.get("type"),
                    "project_id": vertex_secrets.get("project_id"),
                    "private_key_id": vertex_secrets.get("private_key_id"),
                    "private_key": vertex_secrets.get("private_key"),
                    "client_email": vertex_secrets.get("client_email"),
                    "client_id": vertex_secrets.get("client_id"),
                    "auth_uri": vertex_secrets.get("auth_uri"),
                    "token_uri": vertex_secrets.get("token_uri"),
                    "auth_provider_x509_cert_url": vertex_secrets.get("auth_provider_x509_cert_url"),
                    "client_x509_cert_url": vertex_secrets.get("client_x509_cert_url"),
                    "universe_domain": vertex_secrets.get("universe_domain", "googleapis.com")
                }
            else:
                self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
                self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
                self.service_account_info = None
        except ImportError:
            # If streamlit is not available, try to read from environment variables
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID")
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            self.service_account_info = None

        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID must be set.")

        import vertexai

        # Initialize Vertex AI with service account credentials if available
        if self.service_account_info:
            # Use service account credentials
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(
                self.service_account_info
            )
            vertexai.init(
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
        else:
            vertexai.init(project=self.project_id, location=self.location)

        from vertexai.generative_models import GenerativeModel
        self.GenerativeModel = GenerativeModel

    def _call_model_with_fallback(self, prompt: str, model_name: str = "gemini-2.5-flash-lite") -> Optional[str]:
        """Call model with fallback to more capable model if response is incomplete"""
        try:
            # Try primary model first
            model = self.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            response_text = response.text

            # Check if response is complete and valid
            if self._is_response_complete(response_text):
                return response_text

            # If response is incomplete, try fallback model
            if model_name == "gemini-2.5-flash-lite":
                print(f"⚠️ Primary model response incomplete, trying fallback model...")
                time.sleep(1)  # Rate limiting
                return self._call_model_with_fallback(prompt, "gemini-2.5-pro")

            return response_text

        except Exception as e:
            print(f"❌ Model {model_name} failed: {e}")
            # Try fallback model if primary fails
            if model_name == "gemini-2.5-flash-lite":
                print(f"🔄 Trying fallback model...")
                time.sleep(1)
                return self._call_model_with_fallback(prompt, "gemini-2.5-pro")
            return None

    def _is_response_complete(self, response_text: str) -> bool:
        """Check if response appears complete and valid"""
        if not response_text or len(response_text.strip()) < 50:
            return False

        # Check for common incomplete patterns
        incomplete_patterns = [
            r"I cannot.*",
            r"I don't know.*",
            r"I'm sorry.*",
            r"Unable to.*",
            r"No information.*",
            r"Not available.*",
            r"null",
            r"undefined"
        ]

        for pattern in incomplete_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return False

        return True

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from response text with error handling"""
        try:
            # Extract JSON from response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)

            # Try direct JSON parsing
            return json.loads(response_text)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Response text: {response_text[:200]}...")
            return None

    def get_comprehensive_series_info(self, series_name: str, project_state=None) -> Optional[Dict[str, Any]]:
        """Get comprehensive series information using Gemini 2.5 models"""
        try:
            # Create a comprehensive prompt for series information
            prompt = f"""
            Provide comprehensive information about the manga series "{series_name}".

            Please provide the following information in JSON format:
            {{
                "corrected_series_name": "The correct full name of the series",
                "authors": ["List of authors"],
                "extant_volumes": "Total number of volumes published",
                "summary": "Brief description of the series",
                "spinoff_series": ["List of any spinoff series or sequels"],
                "alternate_editions": ["List of alternate editions (omnibus, collector's, etc.)"],
                "genres": ["List of genres"],
                "publisher": "Main publisher",
                "status": "Publication status (ongoing/completed)",
                "alternative_titles": ["List of alternative titles or English translations"],
                "adaptations": ["List of anime, live-action, or other adaptations"]
            }}

            Focus on authoritative sources and accurate information. For "Attack on Titan",
            include spinoffs like "Attack on Titan: Before the Fall", "Attack on Titan: No Regrets",
            and alternate editions like omnibus volumes.
            """

            # Generate response with fallback
            response_text = self._call_model_with_fallback(prompt)
            if not response_text:
                return None

            # Parse JSON response
            series_info = self._parse_json_response(response_text)
            if series_info:
                print(f"✅ Successfully retrieved series info for {series_name}")
                return series_info

            return None

        except Exception as e:
            print(f"❌ Vertex AI series info failed: {e}")
            return None

    def get_book_info(self, series_name: str, volume_number: int, project_state=None) -> Optional[Dict[str, Any]]:
        """Get book information for a specific volume using Gemini 2.5 models"""
        try:
            # Create a comprehensive prompt for book information
            prompt = f"""
            Provide comprehensive information about "{series_name}" Volume {volume_number}.

            Please provide the following information in JSON format:
            {{
                "series_name": "The series name",
                "volume_number": "The volume number",
                "book_title": "The specific title of this volume",
                "authors": ["List of authors"],
                "msrp_cost": "MSRP price in USD",
                "isbn_13": "ISBN-13 number",
                "publisher_name": "Publisher name",
                "copyright_year": "Copyright year",
                "description": "Book description",
                "physical_description": "Physical description (pages, dimensions)",
                "genres": ["List of genres"],
                "number_of_extant_volumes": "Total volumes in the series"
            }}

            Focus on accurate, authoritative information. For "Attack on Titan" volumes,
            provide specific titles, ISBNs, and publisher information for English editions.
            """

            # Generate response with fallback
            response_text = self._call_model_with_fallback(prompt)
            if not response_text:
                return None

            # Parse JSON response
            book_info = self._parse_json_response(response_text)
            if book_info:
                print(f"✅ Successfully retrieved volume info for {series_name} Vol {volume_number}")
                return book_info

            return None

        except Exception as e:
            print(f"❌ Vertex AI book info failed: {e}")
            return None

    def batch_get_book_info(self, series_name: str, volume_numbers: list, project_state=None) -> Dict[int, Dict[str, Any]]:
        """Batch get book information for multiple volumes"""
        results = {}

        for volume_number in volume_numbers:
            try:
                book_info = self.get_book_info(series_name, volume_number, project_state)
                if book_info:
                    results[volume_number] = book_info

                # Rate limiting for batch operations
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Failed to get info for {series_name} Vol {volume_number}: {e}")

        return results