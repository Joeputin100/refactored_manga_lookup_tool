#!/usr/bin/env python3
"""
Test script to verify cover image fixes work
"""
import sys
import os
# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import GoogleBooksAPI, ProjectState

def test_cover_strategies():
    """Test different cover image retrieval strategies"""
    print("🔍 Testing cover image retrieval strategies...")

    # Initialize APIs
    google_books_api = GoogleBooksAPI()
    project_state = ProjectState()

    # Test series with known issues
    test_cases = [
        {
            "series": "Attack on Titan",
            "volume": 1,
            "isbn": "9781612620244"  # This is the duplicate ISBN
        },
        {
            "series": "One Piece",
            "volume": 1,
            "isbn": "9781569319017"  # Duplicate ISBN
        },
        {
            "series": "Berserk",
            "volume": 1,
            "isbn": None  # No ISBN
        }
    ]

    for test in test_cases:
        print(f"\n📚 Testing: {test['series']} Volume {test['volume']}")

        # Strategy 1: ISBN lookup
        if test['isbn']:
            try:
                cover_url = google_books_api.get_cover_image_url(test['isbn'], project_state)
                if cover_url:
                    print(f"  ✅ Cover from ISBN: {cover_url}")
                else:
                    print(f"  ❌ No cover from ISBN: {test['isbn']}")
            except Exception as e:
                print(f"  ❌ ISBN lookup failed: {e}")

        # Strategy 2: Series name search
        try:
            cover_url = google_books_api.get_series_cover_url(test['series'], project_state)
            if cover_url:
                print(f"  ✅ Cover from series: {cover_url}")
            else:
                print(f"  ❌ No cover from series: {test['series']}")
        except Exception as e:
            print(f"  ❌ Series lookup failed: {e}")

        # Strategy 3: Volume-specific search
        try:
            series_name = test['series']
            volume_num = test['volume']
            search_query = f'{series_name} vol. {volume_num} manga'
            cover_url = google_books_api.get_series_cover_url(search_query, project_state)
            if cover_url:
                print(f"  ✅ Cover from volume: {cover_url}")
            else:
                print(f"  ❌ No cover from volume: {search_query}")
        except Exception as e:
            print(f"  ❌ Volume lookup failed: {e}")

if __name__ == "__main__":
    test_cover_strategies()