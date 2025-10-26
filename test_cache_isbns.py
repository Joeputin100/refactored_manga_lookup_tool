#!/usr/bin/env python3
"""
Test script to check ISBNs in BigQuery cache
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def test_cache_isbns():
    """Check what ISBNs are stored in BigQuery cache"""
    print("🔍 Checking ISBNs in BigQuery cache...")

    bigquery_cache = BigQueryCache()

    if not bigquery_cache.enabled:
        print("❌ BigQuery cache not enabled")
        return

    # Test series with volumes
    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Death Note",
        "Tokyo Ghoul",
        "Berserk",
        "Hunter x Hunter",
        "Fairy Tail",
        "My Hero Academia"
    ]

    for series_name in test_series:
        print(f"\n📚 Series: {series_name}")

        for volume_num in range(1, 4):  # Check first 3 volumes
            try:
                volume_info = bigquery_cache.get_volume_info(series_name, volume_num)
                if volume_info:
                    isbn = volume_info.get("isbn_13")
                    if isbn:
                        print(f"  Volume {volume_num}: ISBN {isbn}")
                    else:
                        print(f"  Volume {volume_num}: ❌ No ISBN")
                else:
                    print(f"  Volume {volume_num}: ❌ Not in cache")
            except Exception as e:
                print(f"  Volume {volume_num}: ❌ Error - {e}")

if __name__ == "__main__":
    test_cache_isbns()