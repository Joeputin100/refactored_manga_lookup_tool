#!/usr/bin/env python3
"""
Final End-to-End Test
- Test multiple series in cache
- Add volumes to series
- Generate basic export files
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def run_final_test():
    print("🚀 Starting Final End-to-End Test")
    print("=" * 60)

    cache = BigQueryCache()

    # Test series - known cached series
    test_series = [
        "One Piece", "Naruto", "Attack on Titan", "Demon Slayer: Kimetsu no Yaiba",
        "My Hero Academia", "Dragon Ball", "Bleach", "Hunter × Hunter",
        "Fullmetal Alchemist", "Death Note", "Tokyo Ghoul", "Chainsaw Man",
        "Jujutsu Kaisen", "Spy × Family", "The Promised Neverland",
        "Black Clover", "Fairy Tail", "Seven Deadly Sins", "One-Punch Man",
        "Dr. Stone"
    ]

    print(f"📚 Testing {len(test_series)} series...")
    print()

    # Test 1: Check series in cache
    print("🔍 Test 1: Series Cache Check")
    print("-" * 40)

    cached_count = 0
    uncached_count = 0

    for series_name in test_series:
        print(f"\n📖 Checking: {series_name}")

        try:
            # Check if series exists in cache
            query = f"""
            SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE series_name = '{series_name}'
            """

            result = cache.client.query(query)
            rows = list(result)

            if rows:
                cached_count += 1
                series_info = dict(rows[0])
                print(f"   ✅ Found in cache")
                print(f"   📝 Author: {series_info.get('authors', 'N/A')}")
                print(f"   📚 Volumes: {series_info.get('total_volumes', 0)}")
                print(f"   🖼️  Cover: {'✅' if series_info.get('cover_image_url') else '❌'}")
                print(f"   📖 Summary: {'✅' if series_info.get('summary') else '❌'}")
            else:
                uncached_count += 1
                print(f"   ❌ Not in cache")

        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    print(f"\n📊 Cache Results: {cached_count} cached, {uncached_count} not cached")

    # Test 2: Add volumes to series
    print(f"\n📚 Test 2: Adding Volumes")
    print("-" * 40)

    volumes_added = 0
    for i, series_name in enumerate(test_series[:5]):  # Add to first 5 series
        print(f"\n📖 Adding volumes to: {series_name}")

        try:
            # Add 5 volumes
            for volume_num in range(1, 6):
                volume_data = {
                    'series_name': series_name,
                    'volume_number': volume_num,
                    'title': f"{series_name} Volume {volume_num}",
                    'isbn': f"97812345678{volume_num:02d}",
                    'publication_date': f"2023-{volume_num:02d}-01",
                    'page_count': 200 + volume_num,
                    'price': 9.99
                }

                # Add to cache
                cache.cache_volume_info(series_name, volume_num, volume_data)
                print(f"   ✅ Added Volume {volume_num}")
                volumes_added += 1

        except Exception as e:
            print(f"   ❌ Error adding volumes: {e}")

    print(f"\n📊 Volumes Added: {volumes_added}")

    # Test 3: Generate basic export files
    print(f"\n📄 Test 3: Export Files")
    print("-" * 40)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create MARC export placeholder
    marc_filename = f"final_test_export_{timestamp}.mrc"
    try:
        with open(marc_filename, 'w') as f:
            f.write("MARC Export Placeholder - Test Data\n")
            for series in test_series:
                f.write(f"Series: {series}\n")
        print(f"✅ MARC export created: {marc_filename}")
    except Exception as e:
        print(f"❌ MARC export failed: {e}")
        marc_filename = None

    # Create labels PDF placeholder
    pdf_filename = f"final_test_labels_{timestamp}.pdf"
    try:
        with open(pdf_filename, 'w') as f:
            f.write("PDF Labels Placeholder - Test Data\n")
            for series in test_series:
                f.write(f"Label: {series}\n")
        print(f"✅ Labels PDF created: {pdf_filename}")
    except Exception as e:
        print(f"❌ Labels PDF failed: {e}")
        pdf_filename = None

    # Test 4: Verify volume data
    print(f"\n🔍 Test 4: Volume Data Verification")
    print("-" * 40)

    try:
        for series_name in test_series[:3]:
            query = f"""
            SELECT COUNT(*) as volume_count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """

            result = cache.client.query(query)
            for row in result:
                print(f"📚 {series_name}: {row['volume_count']} volumes")

    except Exception as e:
        print(f"❌ Volume verification failed: {e}")

    print(f"\n🎯 Test Summary")
    print("=" * 60)
    print(f"📚 Series Tested: {len(test_series)}")
    print(f"💾 Cached Series: {cached_count}")
    print(f"❌ Uncached Series: {uncached_count}")
    print(f"📖 Volumes Added: {volumes_added}")
    print(f"📄 MARC Export: {'✅' if marc_filename else '❌'}")
    print(f"🏷️  Labels PDF: {'✅' if pdf_filename else '❌'}")

    return marc_filename, pdf_filename

if __name__ == "__main__":
    marc_file, pdf_file = run_final_test()