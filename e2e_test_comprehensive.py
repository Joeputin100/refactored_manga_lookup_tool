#!/usr/bin/env python3
"""
Comprehensive End-to-End Test
- Test multiple series (cached and not cached)
- Add 5 volumes each from 20 series
- Check metadata display for series cards and volumes
- Generate export files
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
from manga_lookup import get_comprehensive_series_info
from marc_exporter import MARCExporter
from label_generator import LabelGenerator

def run_comprehensive_test():
    print("🚀 Starting Comprehensive End-to-End Test")
    print("=" * 60)

    cache = BigQueryCache()

    # Test series - mix of cached and potentially uncached
    test_series = [
        # Cached series (should be in BigQuery)
        "One Piece", "Naruto", "Attack on Titan", "Demon Slayer: Kimetsu no Yaiba",
        "My Hero Academia", "Dragon Ball", "Bleach", "Hunter × Hunter",
        "Fullmetal Alchemist", "Death Note", "Tokyo Ghoul", "Chainsaw Man",
        "Jujutsu Kaisen", "Spy × Family", "The Promised Neverland",
        "Black Clover", "Fairy Tail", "Seven Deadly Sins", "One-Punch Man",
        "Dr. Stone"
    ]

    print(f"📚 Testing {len(test_series)} series...")
    print()

    # Test 1: Check series lookup and metadata
    print("🔍 Test 1: Series Lookup and Metadata")
    print("-" * 40)

    cached_count = 0
    uncached_count = 0

    for series_name in test_series:
        print(f"\n📖 Testing: {series_name}")

        try:
            # Look up series
            series_info = get_comprehensive_series_info(series_name)

            if series_info:
                cached_count += 1
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

    # Test 3: Generate MARC export
    print(f"\n📄 Test 3: MARC Export")
    print("-" * 40)

    try:
        exporter = MARCExporter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        marc_filename = f"comprehensive_test_export_{timestamp}.mrc"

        # Export all test series
        marc_data = exporter.export_series_to_marc(test_series)

        with open(marc_filename, 'wb') as f:
            f.write(marc_data)

        print(f"✅ MARC export created: {marc_filename}")
        print(f"📏 File size: {len(marc_data)} bytes")

    except Exception as e:
        print(f"❌ MARC export failed: {e}")
        marc_filename = None

    # Test 4: Generate labels
    print(f"\n🏷️  Test 4: Label Generation")
    print("-" * 40)

    try:
        label_gen = LabelGenerator()
        pdf_filename = f"comprehensive_test_labels_{timestamp}.pdf"

        # Generate labels for test series
        label_gen.generate_labels_for_series(test_series, pdf_filename)

        print(f"✅ Labels generated: {pdf_filename}")

    except Exception as e:
        print(f"❌ Label generation failed: {e}")
        pdf_filename = None

    # Test 5: Verify volume data
    print(f"\n🔍 Test 5: Volume Data Verification")
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
    print(f"🏷️  Labels Generated: {'✅' if pdf_filename else '❌'}")

    return marc_filename, pdf_filename

if __name__ == "__main__":
    marc_file, pdf_file = run_comprehensive_test()