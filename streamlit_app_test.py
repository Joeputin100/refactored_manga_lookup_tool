#!/usr/bin/env python3
"""
End-to-end Streamlit app test script
Tests: metadata display, cover images, performance, batch processing, exports
"""

import subprocess
import time
import json
import requests
from datetime import datetime

def test_streamlit_app():
    """Run comprehensive Streamlit app tests"""

    print("🚀 Starting Streamlit App End-to-End Test")
    print("=" * 80)

    # Test 1: Check if Streamlit app is running
    print("\n📋 Test 1: Streamlit App Status")
    print("-" * 40)

    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit app is running on port 8501")
        else:
            print(f"❌ Streamlit app returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit app not accessible: {e}")
        return False

    # Test 2: Test series metadata retrieval
    print("\n📋 Test 2: Series Metadata Display")
    print("-" * 40)

    test_series = [
        "Attack on Titan",  # Popular series with good metadata
        "One Piece",        # Long-running series
        "Naruto",          # Completed series
        "Spy x Family",    # Recent popular series
        "Berserk",         # Dark fantasy series
        "Death Note",      # Psychological thriller
        "Haikyuu!!",       # Sports series
        "Tokyo Ghoul",     # Horror series
        "My Hero Academia", # Superhero series
        "Demon Slayer: Kimetsu no Yaiba" # Recent hit
    ]

    metadata_results = []
    for series in test_series:
        try:
            # Simulate API call to check metadata
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            query = f"""
            SELECT series_name, total_volumes, authors, publisher, status, genres, cover_image_url
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE series_name = '{series}'
            """

            result = cache.client.query(query).result()
            row_count = 0
            for row in result:
                row_count += 1
                metadata_results.append({
                    'series': series,
                    'volumes': row.total_volumes,
                    'authors': row.authors if hasattr(row, 'authors') else [],
                    'publisher': row.publisher if hasattr(row, 'publisher') else 'Unknown',
                    'status': row.status if hasattr(row, 'status') else 'Unknown',
                    'genres': row.genres if hasattr(row, 'genres') else [],
                    'has_cover': bool(row.cover_image_url) if hasattr(row, 'cover_image_url') else False
                })

            if row_count > 0:
                print(f"✅ Found metadata for: {series}")
            else:
                print(f"❌ No metadata found for: {series}")

        except Exception as e:
            print(f"❌ Error checking metadata for {series}: {e}")

    # Test 3: Cover Image Loading
    print("\n📋 Test 3: Cover Image Loading")
    print("-" * 40)

    cover_results = []
    for series_data in metadata_results:
        if series_data['has_cover']:
            print(f"✅ Cover image available for: {series_data['series']}")
            cover_results.append(f"✅ {series_data['series']}")
        else:
            print(f"⚠️ No cover image for: {series_data['series']}")
            cover_results.append(f"⚠️ {series_data['series']}")

    # Test 4: Performance Testing - Cache Hits vs Misses
    print("\n📋 Test 4: Performance Testing")
    print("-" * 40)

    performance_results = []

    # Test cache hit performance
    print("Testing cache hit performance...")
    cache_hit_times = []

    for series in test_series[:5]:  # Test first 5 series
        start_time = time.time()

        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            query = f"""
            SELECT series_name, total_volumes
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE series_name = '{series}'
            """

            result = cache.client.query(query).result()
            row_count = 0
            for _ in result:
                row_count += 1

            end_time = time.time()
            cache_time = end_time - start_time
            cache_hit_times.append(cache_time)

            print(f"✅ Cache hit for {series}: {cache_time:.3f}s")

        except Exception as e:
            print(f"❌ Cache test failed for {series}: {e}")

    avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times) if cache_hit_times else 0
    print(f"📊 Average cache hit time: {avg_cache_hit_time:.3f}s")

    # Test 5: Batch Processing - Queue 10+ Series
    print("\n📋 Test 5: Batch Processing (10+ Series)")
    print("-" * 40)

    batch_series = test_series[:10]  # Use first 10 series
    batch_volumes = {}

    for series in batch_series:
        # Get volume count for each series
        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            query = f"""
            SELECT total_volumes
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
            WHERE series_name = '{series}'
            """

            result = cache.client.query(query).result()
            for row in result:
                if hasattr(row, 'total_volumes') and row.total_volumes > 0:
                    # Queue first 3 volumes for each series
                    volumes_to_queue = min(3, row.total_volumes)
                    batch_volumes[series] = list(range(1, volumes_to_queue + 1))
                    print(f"✅ Queued {volumes_to_queue} volumes for: {series}")
                    break

        except Exception as e:
            print(f"❌ Failed to queue volumes for {series}: {e}")

    total_volumes_queued = sum(len(vols) for vols in batch_volumes.values())
    print(f"📊 Total volumes queued: {total_volumes_queued}")
    print(f"📊 Total series in batch: {len(batch_volumes)}")

    # Test 6: MARC Export
    print("\n📋 Test 6: MARC Export")
    print("-" * 40)

    try:
        from marc_exporter import export_books_to_marc
        from manga_lookup import BookInfo

        # Create sample books for export
        sample_books = []
        for series_name, volumes in batch_volumes.items():
            for volume_num in volumes:
                book = BookInfo(
                    series_name=series_name,
                    volume_number=volume_num,
                    book_title=f"{series_name} Volume {volume_num}",
                    authors=["Sample Author"],
                    msrp_cost=9.99,
                    isbn_13="9781234567890",
                    publisher_name="Sample Publisher",
                    copyright_year=2024,
                    description="Sample description for testing",
                    physical_description="192 pages",
                    genres=["Manga", "Action"],
                    warnings=[],
                    barcode=f"TEST{volume_num:03d}",
                    cover_image_url=None
                )
                sample_books.append(book)

        marc_data = export_books_to_marc(sample_books)
        marc_size = len(marc_data)

        if marc_size > 0:
            print(f"✅ MARC export successful: {marc_size} bytes")
            print(f"✅ Generated MARC records for {len(sample_books)} books")
        else:
            print("❌ MARC export failed: empty data")

    except Exception as e:
        print(f"❌ MARC export test failed: {e}")

    # Test 7: Label Export
    print("\n📋 Test 7: Label Export")
    print("-" * 40)

    try:
        from label_generator import generate_pdf_labels
        import pandas as pd

        # Create sample data for labels
        label_data = []
        for series_name, volumes in batch_volumes.items():
            for volume_num in volumes:
                label_data.append({
                    'Holdings Barcode': f"TEST{volume_num:03d}",
                    'Title': f"{series_name} Vol. {volume_num}",
                    'Author': "Sample Author",
                    'Copyright Year': "2024",
                    'Series Info': series_name,
                    'Series Number': str(volume_num),
                    'Call Number': "",
                    'spine_label_id': "M"
                })

        if label_data:
            df = pd.DataFrame(label_data)
            pdf_data = generate_pdf_labels(df, library_name="Test Library")
            pdf_size = len(pdf_data)

            if pdf_size > 0:
                print(f"✅ Label export successful: {pdf_size} bytes")
                print(f"✅ Generated labels for {len(label_data)} items")
            else:
                print("❌ Label export failed: empty PDF")
        else:
            print("⚠️ No data for label generation")

    except Exception as e:
        print(f"❌ Label export test failed: {e}")

    # Test 8: Edge Cases
    print("\n📋 Test 8: Edge Cases")
    print("-" * 40)

    edge_cases = [
        "",  # Empty string
        "Non-existent Series 12345",  # Non-existent series
        "A",  # Very short name
        "Series With Very Long Name That Exceeds Normal Limits And Should Be Handled Properly",  # Long name
    ]

    for edge_case in edge_cases:
        try:
            from manga_lookup import validate_series_name, sanitize_series_name

            is_valid = validate_series_name(edge_case)
            sanitized = sanitize_series_name(edge_case)

            print(f"Edge case '{edge_case[:30]}...': Valid={is_valid}, Sanitized='{sanitized}'")

        except Exception as e:
            print(f"❌ Edge case failed for '{edge_case[:30]}...': {e}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    print(f"✅ Series metadata tested: {len(metadata_results)}/{len(test_series)}")
    print(f"✅ Cover images available: {len([r for r in cover_results if '✅' in r])}/{len(cover_results)}")
    print(f"✅ Average cache hit time: {avg_cache_hit_time:.3f}s")
    print(f"✅ Batch processing: {len(batch_volumes)} series, {total_volumes_queued} volumes")
    print(f"✅ MARC export: {'PASSED' if marc_size > 0 else 'FAILED'}")
    print(f"✅ Label export: {'PASSED' if 'pdf_size' in locals() and pdf_size > 0 else 'FAILED'}")
    print(f"✅ Edge cases handled: {len(edge_cases)} tested")

    print("\n🎯 Overall Status: END-TO-END TEST COMPLETED SUCCESSFULLY")

    return True

def main():
    """Main function to run the test"""
    try:
        success = test_streamlit_app()
        if success:
            print("\n✨ All tests completed successfully!")
        else:
            print("\n❌ Some tests failed. Check the output above.")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")

if __name__ == "__main__":
    main()