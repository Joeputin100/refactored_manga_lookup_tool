#!/usr/bin/env python3
"""
Update Vertex AI to use gemini-2.5-flash-lite with fallback to gemini-2.5-pro
"""

def update_vertex_ai_with_fallback():
    """Replace VertexAIAPI with enhanced version that includes fallback logic"""

    # Read the current file
    with open('manga_lookup.py', 'r') as f:
        content = f.read()

    # Find the VertexAIAPI class
    class_start = 'class VertexAIAPI:'
    # Find the end of the class (look for the next class definition)
    class_end_markers = ['class DeepSeekAPI:', 'class GoogleBooksAPI:', 'def ']

    start_pos = content.find(class_start)
    if start_pos == -1:
        print("❌ Could not find VertexAIAPI class")
        return False

    # Find the end of the class
    end_pos = -1
    for marker in class_end_markers:
        pos = content.find(marker, start_pos + len(class_start))
        if pos != -1 and (end_pos == -1 or pos < end_pos):
            end_pos = pos

    if end_pos == -1:
        print("❌ Could not find end of VertexAIAPI class")
        return False

    # Create the enhanced VertexAIAPI class with fallback logic
    enhanced_class = '''class VertexAIAPI:
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

        # Check for common incomplete response patterns
        incomplete_patterns = [
            "I cannot", "I don't know", "I'm not sure",
            "I don't have", "I'm unable", "I'm sorry",
            "I apologize", "I can't", "I won't",
            "This request", "Your request", "The request"
        ]

        for pattern in incomplete_patterns:
            if pattern.lower() in response_text.lower():
                return False

        return True

    def get_comprehensive_series_info(self, series_name: str, project_state=None):
        """Get comprehensive series information using enhanced model with fallback"""
        import time
        from typing import Optional

        prompt = f"""Provide comprehensive information about the manga series "{series_name}" including:

1. Corrected series name (if different from input)
2. Author(s)
3. Total number of volumes published
4. Brief summary/description
5. Genres
6. Publisher
7. Publication status (ongoing, completed, etc.)
8. Alternative titles
9. Spin-off series
10. Adaptations (anime, live-action, etc.)

Format the response as a JSON object with these keys:
- corrected_series_name
- authors (array)
- extant_volumes (integer)
- summary
- genres (array)
- publisher
- status
- alternative_titles (array)
- spinoff_series (array)
- adaptations (array)

If you cannot find information about this series, return an empty JSON object {{}}."""

        try:
            response_text = self._call_model_with_fallback(prompt)

            if not response_text:
                return {}

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                series_info = json.loads(json_match.group())

                # Validate required fields
                if series_info and 'corrected_series_name' in series_info:
                    return series_info

            return {}

        except Exception as e:
            print(f"❌ Vertex AI series info failed: {e}")
            return {}

    def get_book_info(self, series_name: str, volume_number: int, project_state=None):
        """Get book information for a specific volume using enhanced model with fallback"""
        import time
        from typing import Optional

        prompt = f"""Provide information about "{series_name}" Volume {volume_number} including:

1. Book title (if different from series name + volume number)
2. ISBN-13 (if available)
3. Publisher
4. Copyright year
5. Physical description (pages, dimensions)
6. Detailed description/summary
7. Genres
8. Content warnings (if any)

Format the response as a JSON object with these keys:
- book_title
- isbn_13
- publisher_name
- copyright_year (integer)
- physical_description
- description
- genres (array)
- warnings (array)

If you cannot find information about this specific volume, return an empty JSON object {{}}."""

        try:
            response_text = self._call_model_with_fallback(prompt)

            if not response_text:
                return {}

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                book_info = json.loads(json_match.group())

                # Validate required fields
                if book_info and 'book_title' in book_info:
                    return book_info

            return {}

        except Exception as e:
            print(f"❌ Vertex AI book info failed: {e}")
            return {}

    def get_msrp_with_grounding(self, series_name: str, volume_number: int, project_state=None):
        """Get MSRP with grounding using enhanced model with fallback"""
        import time
        from typing import Optional

        prompt = f"""What is the Manufacturer's Suggested Retail Price (MSRP) for "{series_name}" Volume {volume_number} in USD?

Please provide:
1. The MSRP in USD (as a number, e.g., 9.99)
2. Any relevant context about the pricing

Format the response as a JSON object with these keys:
- msrp (number)
- context (string)

If you cannot find the MSRP, return an empty JSON object {{}}."""

        try:
            response_text = self._call_model_with_fallback(prompt)

            if not response_text:
                return {}

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                msrp_info = json.loads(json_match.group())

                # Validate required fields
                if msrp_info and 'msrp' in msrp_info:
                    return msrp_info

            return {}

        except Exception as e:
            print(f"❌ Vertex AI MSRP failed: {e}")
            return {}

'''

    # Replace the current class with the enhanced version
    current_class = content[start_pos:end_pos]
    content = content.replace(current_class, enhanced_class)

    # Write the updated content
    with open('manga_lookup.py', 'w') as f:
        f.write(content)

    print("✅ Vertex AI updated with gemini-2.5-flash-lite and fallback logic")
    return True

if __name__ == "__main__":
    update_vertex_ai_with_fallback()