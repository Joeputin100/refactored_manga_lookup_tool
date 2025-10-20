#!/usr/bin/env python3
import json
import os
from manga_lookup import VertexAIAPI, ProjectState

# Load secrets from the project root
secrets_path = os.path.join(os.path.dirname(__file__), 'secrets.toml')
try:
    with open(secrets_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                if key == 'project_id': # Handle nested key
                    os.environ['VERTEX_AI_PROJECT_ID'] = value
                else:
                    os.environ[key] = value
except FileNotFoundError:
    print(f"⚠️ {secrets_path} not found. Relying on pre-set environment variables.")


# --- Configuration ---
SERIES_TO_TEST = "One Piece"  # <-- Change this to test different series
VOLUME_TO_TEST = 1            # <-- Change this to test different volumes

def test_series_info():
    """Tests the get_comprehensive_series_info method."""
    print(f"--- Testing Series Info for: {SERIES_TO_TEST} ---")
    try:
        vertex_api = VertexAIAPI()
        # We pass a dummy ProjectState since we're not using caching for this test.
        project_state = ProjectState(db_file=":memory:")
        series_info = vertex_api.get_comprehensive_series_info(SERIES_TO_TEST, project_state)
        
        print("✅ Success! API Response:")
        print(json.dumps(series_info, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_book_info():
    """Tests the get_book_info method."""
    print(f"\n--- Testing Book Info for: {SERIES_TO_TEST} Vol. {VOLUME_TO_TEST} ---")
    try:
        vertex_api = VertexAIAPI()
        project_state = ProjectState(db_file=":memory:")
        book_info = vertex_api.get_book_info(SERIES_TO_TEST, VOLUME_TO_TEST, project_state)

        print("✅ Success! API Response:")
        print(json.dumps(book_info, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_series_info()
    test_book_info()
