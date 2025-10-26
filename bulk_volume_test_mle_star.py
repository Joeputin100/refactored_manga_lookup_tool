#!/usr/bin/env python3
"""
Bulk Volume Test with MLE Star Cache Optimization
Tests 10 series with 10 volumes each using MLE Star optimized cache
"""
import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState, BookInfo
from mle_star_cache_optimizer import MLEStarCacheOptimizer
from bigquery_cache import BigQueryCache
from marc_export import export_to_marc
from label_generator import generate_labels_pdf

def main():
    print("🚀 Starting bulk volume test with MLE Star optimization...")
    print("Testing 10 series with 10 volumes each using MLE Star cache")

    # Initialize APIs
    deepseek_api = DeepSeekAPI()
    google_books_api = GoogleBooksAPI()
    project_state = ProjectState()
    bigquery_cache = BigQueryCache()
    mle_optimizer = MLEStarCacheOptimizer(bigquery_cache)

    # Test series (same as original bulk test)
    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Dragon Ball Z",
        "Death Note",
        "Tokyo Ghoul",
        "Berserk",
        "Hunter x Hunter",
        "Fairy Tail",
        "My Hero Academia"
    ]

    all_books = []
    start_time = time.time()

    # Generate barcodes
    barcodes = [f"TEST{str(i).zfill(6)}" for i in range(1, 101)]
    barcode_index = 0

    # Track performance metrics
    performance_metrics = {
        'total_volumes': 0,
        'cache_hits': 0,
        'api_calls': 0,
        'series_times': {},
        'start_time': start_time
    }

    for series_name in test_series:
        print(f"\n📚 Processing: {series_name}")
        series_start_time = time.time()
        series_books = []

        # Prepare batch query for this series
        series_volumes = [
            {'series_name': series_name, 'volume_number': volume_num}
            for volume_num in range(1, 11)
        ]

        # Use MLE Star batch optimization
        batch_results = mle_optimizer.batch_get_volume_info(series_volumes)

        for volume_num, book_info in enumerate(batch_results, 1):
            if book_info:
                # Cache hit - use cached data
                print(f"  ✅ Volume {volume_num}: Loaded from cache")
                performance_metrics['cache_hits'] += 1

                # Get cover image using optimized strategies
                cover_url = None
                if google_books_api:
                    # Strategy 1: Try ISBN lookup
                    isbn = book_info.get("isbn_13")
                    if isbn:
                        try:
                            cover_url = google_books_api.get_cover_image_url(isbn, project_state)
                            if cover_url:
                                print(f"  🖼️ Cover image from ISBN")
                        except Exception as e:
                            print(f"  ❌ ISBN cover failed - {e}")

                    # Strategy 2: Fallback to series name search
                    if not cover_url:
                        try:
                            cover_url = google_books_api.get_series_cover_url(series_name, project_state)
                            if cover_url:
                                print(f"  🖼️ Cover image from series search")
                        except Exception as e:
                            print(f"  ❌ Series cover failed - {e}")

                    # Strategy 3: Try volume-specific search
                    if not cover_url:
                        try:
                            search_query = f'{series_name} vol. {volume_num} manga'
                            cover_url = google_books_api.get_series_cover_url(search_query, project_state)
                            if cover_url:
                                print(f"  🖼️ Cover image from volume search")
                        except Exception as e:
                            print(f"  ❌ Volume cover failed - {e}")

                # Create BookInfo object
                book = BookInfo(
                    series_name=book_info.get("series_name", series_name),
                    volume_number=volume_num,
                    book_title=book_info.get("book_title", f"{series_name} Volume {volume_num}"),
                    authors=book_info.get("authors", []),
                    isbn_13=book_info.get("isbn_13"),
                    publisher_name=book_info.get("publisher_name"),
                    copyright_year=book_info.get("copyright_year"),
                    description=book_info.get("description"),
                    physical_description=book_info.get("physical_description"),
                    genres=book_info.get("genres", []),
                    msrp_cost=book_info.get("msrp_cost"),
                    warnings=[],
                    barcode=barcodes[barcode_index],
                    cover_image_url=cover_url
                )

                # Add cache source as attribute
                book.cache_source = "bigquery"

                series_books.append(book)
                all_books.append(book)
                barcode_index += 1

            else:
                # Cache miss - make API call
                print(f"  🔍 Volume {volume_num}: Cache miss, calling API...")
                performance_metrics['api_calls'] += 1

                book_info = None
                try:
                    book_info = deepseek_api.get_book_info(series_name, volume_num, project_state)
                    if book_info:
                        print(f"  ✅ Volume {volume_num}: Loaded via DeepSeek")
                    else:
                        print(f"  ❌ Volume {volume_num}: DeepSeek failed")
                except Exception as e:
                    print(f"  ❌ Volume {volume_num}: DeepSeek failed - {e}")

                if book_info:
                    # Get cover image
                    cover_url = None
                    if google_books_api:
                        try:
                            cover_url = google_books_api.get_cover_image_url(
                                book_info.get("isbn_13"),
                                project_state
                            )
                            if cover_url:
                                print(f"  🖼️ Cover image from Google Books")
                        except Exception as e:
                            print(f"  ❌ Google Books cover failed - {e}")

                    # Create BookInfo object
                    book = BookInfo(
                        series_name=book_info.get("series_name", series_name),
                        volume_number=volume_num,
                        book_title=book_info.get("book_title", f"{series_name} Volume {volume_num}"),
                        authors=book_info.get("authors", []),
                        isbn_13=book_info.get("isbn_13"),
                        publisher_name=book_info.get("publisher_name"),
                        copyright_year=book_info.get("copyright_year"),
                        description=book_info.get("description"),
                        physical_description=book_info.get("physical_description"),
                        genres=book_info.get("genres", []),
                        msrp_cost=book_info.get("msrp_cost"),
                        warnings=[],
                        barcode=barcodes[barcode_index],
                        cover_image_url=cover_url
                    )

                    series_books.append(book)
                    all_books.append(book)
                    barcode_index += 1

        series_time = time.time() - series_start_time
        performance_metrics['series_times'][series_name] = series_time
        print(f"  ⏱️ Series completed in {series_time:.2f} seconds")

        # Prefetch related volumes for next access
        mle_optimizer.prefetch_related_volumes(series_name, 5)

    total_time = time.time() - start_time
    performance_metrics['total_volumes'] = len(all_books)

    print(f"\n🎯 MLE Star Performance Summary:")
    print(f"   Total volumes processed: {len(all_books)}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Books per second: {len(all_books) / total_time:.2f}")
    print(f"   Cache hits: {performance_metrics['cache_hits']}")
    print(f"   API calls: {performance_metrics['api_calls']}")
    print(f"   Cache hit rate: {performance_metrics['cache_hits'] / len(all_books) * 100:.1f}%")

    # Get MLE Star performance report
    mle_report = mle_optimizer.get_performance_report()
    print(f"\n📈 MLE Star Performance Report:")
    for key, value in mle_report.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     {k}: {v}")
        else:
            print(f"   {key}: {value}")

    # Export to MARC
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marc_filename = f"bulk_test_mle_star_export_{timestamp}.mrc"

    try:
        export_to_marc(all_books, marc_filename)
        print(f"\n📄 MARC export saved: {marc_filename}")
    except Exception as e:
        print(f"❌ MARC export failed: {e}")

    # Export to PDF labels
    pdf_filename = f"bulk_test_mle_star_labels_{timestamp}.pdf"

    try:
        generate_labels_pdf(all_books, pdf_filename)
        print(f"📄 Label PDF saved: {pdf_filename}")
    except Exception as e:
        print(f"❌ Label PDF failed: {e}")

    # Save performance metrics
    metrics_filename = f"bulk_test_mle_star_metrics_{timestamp}.json"
    with open(metrics_filename, 'w') as f:
        json.dump({
            'performance_metrics': performance_metrics,
            'mle_star_report': mle_report,
            'test_config': {
                'series_count': len(test_series),
                'volumes_per_series': 10,
                'total_volumes': len(all_books)
            }
        }, f, indent=2)

    print(f"\n📊 Performance metrics saved: {metrics_filename}")

    # Compare with original performance
    original_time = 1198.14  # First test time
    improvement = (original_time - total_time) / original_time * 100

    print(f"\n🎯 Performance Comparison:")
    print(f"   Original test time: {original_time:.2f} seconds")
    print(f"   MLE Star test time: {total_time:.2f} seconds")
    print(f"   Performance improvement: {improvement:.1f}% faster")

    if improvement > 0:
        print(f"   ✅ MLE Star optimization successful!")
    else:
        print(f"   🔧 Further optimization needed")

if __name__ == "__main__":
    main()