#!/usr/bin/env python3
"""
Test script to debug Google Books API cover image retrieval
"""

import sys
import os
import requests

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import GoogleBooksAPI, ProjectState

def test_google_books_covers():
    """Test Google Books API cover image retrieval"""
    print("🔍 Testing Google Books API cover image retrieval...")

    google_books_api = GoogleBooksAPI()
    project_state = ProjectState()

    # Test with known manga ISBNs
    test_isbns = [
        "9781421502670",  # Naruto Vol 1
        "9781569319000",  # One Piece Vol 1
        "9781612620244",  # Attack on Titan Vol 1
        "9781591162209",  # Death Note Vol 1
        "9781421505862"   # Tokyo Ghoul Vol 1
    ]

    print(f"Using API key: {google_books_api.api_key[:10]}..." if google_books_api.api_key else "No API key found")

    for isbn in test_isbns:
        print(f"\n📚 Testing ISBN: {isbn}")

        try:
            cover_url = google_books_api.get_cover_image_url(isbn, project_state)
            print(f"  Cover URL: {cover_url}")

            if cover_url:
                # Test if the URL is accessible
                try:
                    response = requests.head(cover_url, timeout=5)
                    print(f"  HTTP Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"  ✅ URL is accessible")
                    else:
                        print(f"  ❌ URL returned {response.status_code}")
                except Exception as e:
                    print(f"  ❌ URL test failed: {e}")
            else:
                print(f"  ❌ No cover URL returned")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Test with series name search
    print("\n🔍 Testing series name search...")
    test_series = ["Naruto", "One Piece", "Attack on Titan"]

    for series_name in test_series:
        print(f"\n📚 Testing series: {series_name}")
        try:
            cover_url = google_books_api.get_series_cover_url(series_name, project_state)
            print(f"  Series Cover URL: {cover_url}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_google_books_covers()