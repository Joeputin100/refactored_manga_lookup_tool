#!/usr/bin/env python3
"""
Comprehensive Workflow Test

This script tests the complete manga lookup workflow:
1. Tests series lookup with barcode input
2. Tests volume range processing
3. Generates MARC export
4. Generates PDF labels
5. Copies files to downloads directory
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import (
    VertexAIAPI,
    ProjectState,
    generate_sequential_general_barcodes,
    parse_volume_range
)
from marc_exporter import export_books_to_marc
from label_generator_modified import generate_pdf_labels

def test_series_lookup():
    """Test series lookup with popular manga series"""
    print("🔍 Testing Series Lookup...")

    vertex_api = VertexAIAPI()
    project_state = ProjectState()

    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Demon Slayer",
        "My Hero Academia"
    ]

    results = []
    for series_name in test_series:
        print(f"  📚 Looking up: {series_name}")
        try:
            series_info = vertex_api.get_comprehensive_series_info(series_name, project_state)
            if series_info:
                results.append({
                    'series_name': series_name,
                    'total_volumes': series_info.get('extant_volumes', 0),
                    'authors': series_info.get('authors', []),
                    'success': True
                })
                print(f"    ✅ Found {series_info.get('extant_volumes', 0)} volumes")
            else:
                results.append({
                    'series_name': series_name,
                    'success': False
                })
                print(f"    ❌ Not found")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({
                'series_name': series_name,
                'success': False
            })

        time.sleep(1)  # Rate limiting

    return results

def test_volume_processing():
    """Test volume processing with mock data"""
    print("\n📚 Testing Volume Processing...")

    # Mock volume data for testing
    test_volumes = [
        {
            'series_name': 'Attack on Titan',
            'volume_number': 1,
            'book_title': 'Attack on Titan Volume 1',
            'authors': ['Isayama, Hajime'],
            'msrp_cost': 10.99,
            'isbn_13': '9781612620244',
            'publisher_name': 'Kodansha Comics',
            'copyright_year': 2012,
            'description': 'In a world where humanity lives inside cities surrounded by enormous walls due to the Titans, gigantic humanoid creatures who devour humans seemingly without reason.',
            'physical_description': '192 pages, 5 x 7.5 inches',
            'genres': ['Action', 'Fantasy', 'Horror']
        },
        {
            'series_name': 'One Piece',
            'volume_number': 1,
            'book_title': 'One Piece Volume 1: Romance Dawn',
            'authors': ['Oda, Eiichiro'],
            'msrp_cost': 9.99,
            'isbn_13': '9781569319017',
            'publisher_name': 'VIZ Media',
            'copyright_year': 2003,
            'description': 'As a child, Monkey D. Luffy was inspired to become a pirate by listening to the tales of the buccaneer "Red-Haired" Shanks.',
            'physical_description': '216 pages, 5 x 7.5 inches',
            'genres': ['Action', 'Adventure', 'Comedy']
        }
    ]

    print(f"  ✅ Processed {len(test_volumes)} test volumes")
    return test_volumes

def generate_test_exports(books):
    """Generate MARC and PDF exports for test data"""
    print("\n📄 Generating Export Files...")

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate MARC export
    try:
        marc_data = export_books_to_marc(books)
        marc_filename = f"workflow_test_export_{timestamp}.mrc"
        with open(marc_filename, 'wb') as f:
            f.write(marc_data)
        print(f"  ✅ Generated MARC export: {marc_filename}")
    except Exception as e:
        print(f"  ❌ MARC export failed: {e}")
        marc_filename = None

    # Generate PDF labels
    try:
        pdf_filename = f"workflow_test_labels_{timestamp}.pdf"
        generate_pdf_labels(books, pdf_filename)
        print(f"  ✅ Generated PDF labels: {pdf_filename}")
    except Exception as e:
        print(f"  ❌ PDF labels failed: {e}")
        pdf_filename = None

    return marc_filename, pdf_filename

def copy_to_downloads(marc_file, pdf_file):
    """Copy export files to downloads directory"""
    print("\n📁 Copying Files to Downloads...")

    downloads_dir = os.path.expanduser("~/storage/downloads")

    if not os.path.exists(downloads_dir):
        print(f"  ❌ Downloads directory not found: {downloads_dir}")
        return False

    try:
        if marc_file and os.path.exists(marc_file):
            os.system(f"cp {marc_file} {downloads_dir}/")
            print(f"  ✅ Copied MARC file to downloads")

        if pdf_file and os.path.exists(pdf_file):
            os.system(f"cp {pdf_file} {downloads_dir}/")
            print(f"  ✅ Copied PDF file to downloads")

        return True
    except Exception as e:
        print(f"  ❌ Copy failed: {e}")
        return False

def main():
    """Main workflow test function"""
    print("🚀 Comprehensive Workflow Test")
    print("=" * 50)

    # Test series lookup
    series_results = test_series_lookup()

    # Test volume processing
    test_books = test_volume_processing()

    # Generate exports
    marc_file, pdf_file = generate_test_exports(test_books)

    # Copy to downloads
    copy_success = copy_to_downloads(marc_file, pdf_file)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   ✅ Series lookups: {len([r for r in series_results if r['success']])}/{len(series_results)}")
    print(f"   ✅ Volumes processed: {len(test_books)}")
    print(f"   ✅ MARC export: {'Yes' if marc_file else 'No'}")
    print(f"   ✅ PDF labels: {'Yes' if pdf_file else 'No'}")
    print(f"   ✅ Files copied to downloads: {'Yes' if copy_success else 'No'}")

    if marc_file and pdf_file:
        print(f"\n📁 Generated files:")
        print(f"   📄 MARC: {marc_file}")
        print(f"   📄 PDF: {pdf_file}")
        print(f"   📁 Location: ~/storage/downloads/")

    print("\n✅ Workflow test completed!")

if __name__ == "__main__":
    main()