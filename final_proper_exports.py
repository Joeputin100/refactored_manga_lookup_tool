#!/usr/bin/env python3
"""
Final Proper Export Test - Generate real MARC and PDF files with correct data mapping
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
from label_generator import generate_pdf_labels

def generate_final_exports():
    print("🚀 Generating Final Proper Export Files")
    print("=" * 60)

    cache = BigQueryCache()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get series with volumes for label generation
    test_series = ["One Piece", "Naruto", "Attack on Titan", "Demon Slayer: Kimetsu no Yaiba", "My Hero Academia"]

    print(f"📚 Generating exports for {len(test_series)} series...")

    # Test 1: Generate proper PDF labels
    print(f"\n🏷️  Test 1: Generating PDF Labels")
    print("-" * 40)

    try:
        # Get volume data for label generation
        volume_data = []
        for series_name in test_series:
            query = f"""
            SELECT
                v.series_name,
                v.volume_number,
                v.book_title,
                v.isbn_13,
                v.copyright_year,
                v.physical_description,
                v.msrp_cost,
                s.authors
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info` v
            LEFT JOIN `static-webbing-461904-c4.manga_lookup_cache.series_info` s
            ON v.series_name = s.series_name
            WHERE v.series_name = '{series_name}'
            ORDER BY v.volume_number
            LIMIT 5
            """

            result = cache.client.query(query)
            for row in result:
                # Map to expected label generator format
                volume_data.append({
                    'Title': row['book_title'] or f"{row['series_name']} Volume {row['volume_number']}",
                    'Author': row['authors'] or '',
                    'Copyright Year': row['copyright_year'] or 2023,
                    'Series Info': row['series_name'],
                    'Series Number': row['volume_number'],
                    'Call Number': '741.5',  # Default Dewey for manga
                    'Holdings Barcode': f"B{row['volume_number']:03d}",
                    'MSRP': row['msrp_cost'] or 9.99
                })

        print(f"📖 Found {len(volume_data)} volumes for label generation")

        if volume_data:
            # Create DataFrame for label generator
            df = pd.DataFrame(volume_data)

            # Generate proper PDF labels
            pdf_data = generate_pdf_labels(df, library_name="Manga Library", library_id='B')

            # Save the PDF
            pdf_filename = f"final_proper_labels_{timestamp}.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_data)

            print(f"✅ Proper PDF labels generated: {pdf_filename}")

            # Check file size
            file_size = os.path.getsize(pdf_filename)
            print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    except Exception as e:
        print(f"❌ PDF label generation failed: {e}")
        pdf_filename = None

    # Test 2: Generate proper MARC export
    print(f"\n📄 Test 2: Generating MARC Export")
    print("-" * 40)

    try:
        # Try to use the marc_exporter
        from marc_exporter import export_books_to_marc

        # Get comprehensive data for MARC export
        marc_data = []
        for series_name in test_series:
            query = f"""
            SELECT
                s.series_name,
                s.authors,
                s.total_volumes,
                s.summary,
                s.cover_image_url,
                s.publisher,
                v.volume_number,
                v.book_title,
                v.isbn_13,
                v.copyright_year,
                v.physical_description,
                v.msrp_cost
            FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` s
            LEFT JOIN `static-webbing-461904-c4.manga_lookup_cache.volume_info` v
            ON s.series_name = v.series_name
            WHERE s.series_name = '{series_name}'
            ORDER BY v.volume_number
            LIMIT 5
            """

            result = cache.client.query(query)
            for row in result:
                # Map to expected MARC format
                marc_data.append({
                    'title': row['book_title'] or f"{row['series_name']} Volume {row['volume_number']}",
                    'author': row['authors'] or '',
                    'isbn': row['isbn_13'] or '',
                    'publisher': row['publisher'] or 'Unknown',
                    'publication_year': row['copyright_year'] or 2023,
                    'page_count': 200,  # Default
                    'series': row['series_name'],
                    'volume_number': row['volume_number'],
                    'summary': row['summary'] or '',
                    'cover_url': row['cover_image_url'] or ''
                })

        print(f"📖 Found {len(marc_data)} volume records for MARC export")

        # Generate MARC export
        marc_filename = f"final_proper_export_{timestamp}.mrc"
        marc_binary = export_books_to_marc(marc_data)

        with open(marc_filename, 'wb') as f:
            f.write(marc_binary)

        print(f"✅ Proper MARC export generated: {marc_filename}")

        # Check file size
        file_size = os.path.getsize(marc_filename)
        print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    except Exception as e:
        print(f"❌ MARC export failed: {e}")
        marc_filename = None

    print(f"\n🎯 Export Summary")
    print("=" * 60)
    print(f"📚 Series Processed: {len(test_series)}")
    print(f"📖 Volumes Found: {len(volume_data) if 'volume_data' in locals() else 0}")
    print(f"🏷️  PDF Labels: {'✅' if pdf_filename else '❌'}")
    print(f"📄 MARC Export: {'✅' if marc_filename else '❌'}")

    return marc_filename, pdf_filename

if __name__ == "__main__":
    marc_file, pdf_file = generate_final_exports()