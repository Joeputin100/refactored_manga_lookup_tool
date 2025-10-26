#!/usr/bin/env python3
"""
Bulk Volume Test Script with BigQuery Cache Integration
Tests 10 series with 10 volumes each, uses BigQuery cache first, then API fallback
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import (
    DeepSeekAPI,
    VertexAIAPI,
    GoogleBooksAPI,
    ProjectState,
    generate_sequential_general_barcodes,
    BookInfo
)
from bigquery_cache import BigQueryCache
from marc_exporter import export_books_to_marc

# Test series (popular manga series)
TEST_SERIES = [
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

def load_volumes_with_cache():
    """Load 10 volumes for each of 10 series using BigQuery cache first"""
    print("🚀 Loading 10 volumes for each of 10 series with BigQuery cache...")

    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    vertex_api = VertexAIAPI()
    google_books_api = GoogleBooksAPI()
    bigquery_cache = BigQueryCache()

    all_books = []

    # Generate barcodes for 100 volumes
    start_barcode = "TEST000001"
    barcodes = generate_sequential_general_barcodes(start_barcode, 100)
    barcode_index = 0

    for series_name in TEST_SERIES:
        print(f"\n📚 Processing: {series_name}")
        series_books = []

        for volume_num in range(1, 11):  # 10 volumes per series
            book_info = None
            cache_source = None

            # Try BigQuery cache first
            if bigquery_cache.enabled:
                try:
                    cached_info = bigquery_cache.get_volume_info(series_name, volume_num)
                    if cached_info:
                        book_info = cached_info
                        cache_source = "BigQuery"
                        print(f"  ✅ Volume {volume_num}: Loaded from BigQuery cache")
                except Exception as e:
                    print(f"  ❌ Volume {volume_num}: BigQuery cache failed - {e}")

            # If cache miss, try DeepSeek API
            if not book_info:
                try:
                    book_info = deepseek_api.get_book_info(
                        series_name=series_name,
                        volume_number=volume_num,
                        project_state=project_state
                    )
                    if book_info:
                        cache_source = "DeepSeek API"
                        print(f"  ✅ Volume {volume_num}: Loaded via DeepSeek")

                        # Cache the result in BigQuery
                        if bigquery_cache.enabled:
                            try:
                                bigquery_cache.cache_volume_info(series_name, volume_num, book_info, "deepseek")
                                print(f"  💾 Cached volume info for: {series_name} Vol {volume_num}")
                            except Exception as cache_error:
                                print(f"  ❌ Failed to cache volume info: {cache_error}")
                except Exception as e:
                    print(f"  ❌ Volume {volume_num}: DeepSeek failed - {e}")

            # Fallback to Vertex AI
            if not book_info and vertex_api:
                try:
                    book_info = vertex_api.get_book_info(
                        series_name=series_name,
                        volume_number=volume_num,
                        project_state=project_state
                    )
                    if book_info:
                        cache_source = "Vertex AI (fallback)"
                        print(f"  ✅ Volume {volume_num}: Loaded via Vertex AI (fallback)")

                        # Cache the result in BigQuery
                        if bigquery_cache.enabled:
                            try:
                                bigquery_cache.cache_volume_info(series_name, volume_num, book_info, "vertex_ai")
                                print(f"  💾 Cached volume info for: {series_name} Vol {volume_num}")
                            except Exception as cache_error:
                                print(f"  ❌ Failed to cache volume info: {cache_error}")
                except Exception as e:
                    print(f"  ❌ Volume {volume_num}: Vertex AI failed - {e}")

            if book_info:
                # Get cover image - try multiple strategies
                cover_url = None
                if google_books_api:
                    # Strategy 1: Try ISBN lookup
                    isbn = book_info.get("isbn_13")
                    if isbn:
                        try:
                            cover_url = google_books_api.get_cover_image_url(isbn, project_state)
                            if cover_url:
                                print(f"  🖼️ Cover image from ISBN: {isbn}")
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
                            search_query = f'"{series_name}" "vol. {volume_num}" manga'
                            # Use the series cover method with custom query
                            cover_url = google_books_api.get_series_cover_url(search_query, project_state)
                            if cover_url:
                                print(f"  🖼️ Cover image from volume search")
                        except Exception as e:
                            print(f"  ❌ Volume cover failed - {e}")

                # Create BookInfo object
                book = BookInfo(
                    series_name=book_info.get("series_name", series_name),
                    volume_number=volume_num,
                    book_title=book_info.get("book_title", f"{series_name} Vol. {volume_num}"),
                    authors=book_info.get("authors", []),
                    msrp_cost=book_info.get("msrp_cost"),
                    isbn_13=book_info.get("isbn_13"),
                    publisher_name=book_info.get("publisher_name"),
                    copyright_year=book_info.get("copyright_year"),
                    description=book_info.get("description"),
                    physical_description=book_info.get("physical_description"),
                    genres=book_info.get("genres", []),
                    warnings=[],
                    barcode=barcodes[barcode_index],
                    cover_image_url=cover_url
                )

                # Add cache source as an attribute
                book.cache_source = cache_source

                series_books.append(book)
                all_books.append(book)
                barcode_index += 1

                # Add small delay to avoid rate limiting (only for API calls)
                if cache_source and "API" in cache_source:
                    time.sleep(1)
            else:
                print(f"  ❌ Volume {volume_num}: Failed to load")

        print(f"  📊 Loaded {len(series_books)} volumes for {series_name}")

    return all_books

def validate_data_quality(all_books):
    """Validate data quality for all books"""
    print("\n🔍 Validating data quality...")

    validation_results = {
        'total_books': len(all_books),
        'field_completion': {},
        'cache_stats': {'total': 0, 'cached': 0, 'api_calls': 0},
        'cover_stats': {'total': 0, 'has_cover': 0, 'broken_links': 0, 'issues': []}
    }

    # Check field completion
    required_fields = ['series_name', 'volume_number', 'book_title', 'authors', 'msrp_cost',
                      'isbn_13', 'publisher_name', 'copyright_year', 'description',
                      'physical_description', 'genres', 'cover_image_url']

    for field in required_fields:
        validation_results['field_completion'][field] = {
            'total': 0,
            'present': 0,
            'percentage': 0.0
        }

    for book in all_books:
        # Check field completion
        for field in required_fields:
            value = getattr(book, field, None)
            if value and (not isinstance(value, list) or len(value) > 0):
                validation_results['field_completion'][field]['present'] += 1
            validation_results['field_completion'][field]['total'] += 1

        # Check cache source
        validation_results['cache_stats']['total'] += 1
        cache_source = getattr(book, 'cache_source', None)
        if cache_source == "BigQuery":
            validation_results['cache_stats']['cached'] += 1
        elif cache_source and "API" in cache_source:
            validation_results['cache_stats']['api_calls'] += 1

        # Check cover images
        validation_results['cover_stats']['total'] += 1
        if book.cover_image_url:
            validation_results['cover_stats']['has_cover'] += 1
            # Test if cover URL is accessible
            try:
                response = requests.head(book.cover_image_url, timeout=5)
                if response.status_code != 200:
                    validation_results['cover_stats']['broken_links'] += 1
                    validation_results['cover_stats']['issues'].append({
                        'series': book.series_name,
                        'volume': book.volume_number,
                        'url': book.cover_image_url,
                        'issue': f'HTTP {response.status_code}'
                    })
            except Exception as e:
                validation_results['cover_stats']['broken_links'] += 1
                validation_results['cover_stats']['issues'].append({
                    'series': book.series_name,
                    'volume': book.volume_number,
                    'url': book.cover_image_url,
                    'issue': str(e)
                })

    # Calculate percentages
    for field in required_fields:
        stats = validation_results['field_completion'][field]
        if stats['total'] > 0:
            stats['percentage'] = (stats['present'] / stats['total']) * 100

    return validation_results

def generate_exports(all_books):
    """Generate MARC and label exports"""
    print("\n📤 Generating exports...")

    # Generate MARC file
    try:
        marc_data = export_books_to_marc(all_books)
        marc_filename = f"bulk_test_cache_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mrc"
        with open(marc_filename, 'wb') as f:
            f.write(marc_data)
        print(f"✅ MARC export created: {marc_filename}")
    except Exception as e:
        print(f"❌ MARC export failed: {e}")
        marc_filename = None

    # Generate label PDF
    try:
        from label_generator import generate_pdf_labels
        import pandas as pd

        label_data = []
        for book in all_books:
            label_data.append({
                'Holdings Barcode': book.barcode,
                'Title': book.book_title or f"{book.series_name} Vol. {book.volume_number}",
                'Author': ', '.join(book.authors) if book.authors else "Unknown Author",
                'Copyright Year': str(book.copyright_year) if book.copyright_year else "",
                'Series Info': book.series_name,
                'Series Number': str(book.volume_number),
                'Call Number': "",  # Empty for manga
                'spine_label_id': "M"  # M for manga
            })

        if label_data:
            df = pd.DataFrame(label_data)
            pdf_data = generate_pdf_labels(df, library_name="Manga Collection Cache Test")
            pdf_filename = f"bulk_test_cache_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_data)
            print(f"✅ Label PDF created: {pdf_filename}")
        else:
            print("❌ No data for label generation")
            pdf_filename = None
    except Exception as e:
        print(f"❌ Label PDF generation failed: {e}")
        pdf_filename = None

    return marc_filename, pdf_filename

def main():
    """Main test function"""
    print("🚀 Starting bulk volume test with BigQuery cache...")
    print(f"Testing {len(TEST_SERIES)} series with 10 volumes each")

    start_time = time.time()

    # Step 1: Load volumes with cache
    all_books = load_volumes_with_cache()

    # Step 2: Validate data quality
    validation_results = validate_data_quality(all_books)

    # Step 3: Generate exports
    marc_file, pdf_file = generate_exports(all_books)

    # Summary
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "="*60)
    print("📊 BULK TEST WITH CACHE SUMMARY")
    print("="*60)
    print(f"Total books processed: {len(all_books)}")
    print(f"Total series tested: {len(TEST_SERIES)}")
    print(f"Test duration: {duration:.2f} seconds")
    print(f"Books per second: {len(all_books)/duration:.2f}")

    print("\n📈 FIELD COMPLETION RATES:")
    for field, stats in validation_results['field_completion'].items():
        print(f"  {field}: {stats['percentage']:.1f}% ({stats['present']}/{stats['total']})")

    print("\n💾 CACHE STATISTICS:")
    cache_stats = validation_results['cache_stats']
    if cache_stats['total'] > 0:
        cache_rate = (cache_stats['cached'] / cache_stats['total']) * 100
        api_rate = (cache_stats['api_calls'] / cache_stats['total']) * 100
        print(f"  Cache hits: {cache_rate:.1f}% ({cache_stats['cached']}/{cache_stats['total']})")
        print(f"  API calls: {api_rate:.1f}% ({cache_stats['api_calls']}/{cache_stats['total']})")

    print("\n🖼️ COVER IMAGE STATS:")
    cover_stats = validation_results['cover_stats']
    if cover_stats['total'] > 0:
        cover_rate = (cover_stats['has_cover'] / cover_stats['total']) * 100
        broken_rate = (cover_stats['broken_links'] / cover_stats['total']) * 100
        print(f"  Total covers: {cover_rate:.1f}% ({cover_stats['has_cover']}/{cover_stats['total']})")
        print(f"  Broken links: {broken_rate:.1f}% ({cover_stats['broken_links']}/{cover_stats['total']})")

    print("\n📁 EXPORTS:")
    print(f"  MARC file: {marc_file}")
    print(f"  Label PDF: {pdf_file}")

    if cover_stats['issues']:
        print(f"\n⚠️ COVER ISSUES ({len(cover_stats['issues'])}):")
        for issue in cover_stats['issues'][:5]:  # Show first 5
            print(f"  {issue['series']} Vol {issue['volume']}: {issue['issue']}")

    print("\n✅ Bulk test with cache completed!")

    # Return file names for SCP
    return marc_file, pdf_file

if __name__ == "__main__":
    marc_file, pdf_file = main()