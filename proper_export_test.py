#!/usr/bin/env python3
"""
Proper Export Test - Generate real MARC and PDF files
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
from label_generator import generate_pdf_labels

def generate_proper_exports():
    print("🚀 Generating Proper Export Files")
    print("=" * 60)

    cache = BigQueryCache()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get series with volumes for label generation
    test_series = ["One Piece", "Naruto", "Attack on Titan", "Demon Slayer: Kimetsu no Yaiba", "My Hero Academia"]

    print(f"�� Generating exports for {len(test_series)} series...")

    # Test 1: Generate proper PDF labels
    print(f"\n🏷️  Test 1: Generating PDF Labels")
    print("-" * 40)

    try:
        # Get volume data for label generation
        volume_data = []
        for series_name in test_series:
            query = f"""
            SELECT
                series_name,
                volume_number,
                book_title,
                isbn_13,
                copyright_year,
                physical_description,
                msrp_cost
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            ORDER BY volume_number
            LIMIT 5
            """

            result = cache.client.query(query)
            for row in result:
                volume_data.append({
                    'series_name': row['series_name'],
                    'volume_number': row['volume_number'],
                    'book_title': row['book_title'],
                    'isbn_13': row['isbn_13'],
                    'copyright_year': row['copyright_year'],
                    'physical_description': row['physical_description'],
                    'msrp_cost': row['msrp_cost']
                })

        print(f"📖 Found {len(volume_data)} volumes for label generation")

        if volume_data:
            # Create DataFrame for label generator
            df = pd.DataFrame(volume_data)

            # Generate proper PDF labels
            pdf_filename = f"proper_labels_{timestamp}.pdf"
            generate_pdf_labels(df, library_name="Test Library", library_id='B')

            # The function might save the file differently, let's check
            if os.path.exists("labels.pdf"):
                os.rename("labels.pdf", pdf_filename)
                print(f"✅ Proper PDF labels generated: {pdf_filename}")

                # Check file size
                file_size = os.path.getsize(pdf_filename)
                print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            else:
                print("⚠️  PDF file not found at expected location")
                pdf_filename = None

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
                marc_data.append({
                    'series_name': row['series_name'],
                    'authors': row['authors'],
                    'total_volumes': row['total_volumes'],
                    'summary': row['summary'],
                    'cover_image_url': row['cover_image_url'],
                    'publisher': row['publisher'],
                    'volume_number': row['volume_number'],
                    'book_title': row['book_title'],
                    'isbn_13': row['isbn_13'],
                    'copyright_year': row['copyright_year'],
                    'physical_description': row['physical_description'],
                    'msrp_cost': row['msrp_cost']
                })

        print(f"📖 Found {len(marc_data)} volume records for MARC export")

        # Generate MARC export
        marc_filename = f"proper_export_{timestamp}.mrc"
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
    marc_file, pdf_file = generate_proper_exports()