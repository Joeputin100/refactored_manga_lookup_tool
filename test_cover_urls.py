#!/usr/bin/env python3
"""
Test script to examine cover image URLs returned by DeepSeek API
"""

import sys
import os
import requests

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import DeepSeekAPI, ProjectState

def test_cover_urls():
    """Test a few volumes to see what cover URLs are being returned"""
    print("🔍 Testing cover image URLs from DeepSeek API...")

    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()

    # Test a few popular volumes
    test_volumes = [
        ("Attack on Titan", 1),
        ("One Piece", 1),
        ("Naruto", 1)
    ]

    for series_name, volume_num in test_volumes:
        print(f"\n📚 Testing: {series_name} Volume {volume_num}")

        try:
            book_info = deepseek_api.get_book_info(
                series_name=series_name,
                volume_number=volume_num,
                project_state=project_state
            )

            if book_info:
                cover_url = book_info.get("cover_image_url")
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
            else:
                print(f"  ❌ Failed to get book info")

        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_cover_urls()