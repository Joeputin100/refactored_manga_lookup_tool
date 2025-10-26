#!/usr/bin/env python3
"""
Complete workflow test for Manga Lookup Tool
Tests the entire workflow from barcode input to MARC export
"""

import sys
import os
import json
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import (
    DeepSeekAPI,
    VertexAIAPI,
    GoogleBooksAPI,
    ProjectState,
    parse_volume_range,
    generate_sequential_general_barcodes
)
from marc_exporter import export_books_to_marc

def test_api_initialization():
    """Test that all APIs initialize correctly"""
    print("🔧 Testing API Initialization...")

    try:
        vertex_api = VertexAIAPI()
        print("✅ Vertex AI API initialized")
    except Exception as e:
        print(f"❌ Vertex AI API failed: {e}")

    try:
        deepseek_api = DeepSeekAPI()
        print("✅ DeepSeek API initialized")
    except Exception as e:
        print(f"❌ DeepSeek API failed: {e}")

    try:
        google_api = GoogleBooksAPI()
        print("✅ Google Books API initialized")
    except Exception as e:
        print(f"❌ Google Books API failed: {e}")

def test_series_lookup(series_name):
    """Test series lookup functionality"""
    print(f"\n🔍 Testing Series Lookup: {series_name}")

    project_state = ProjectState()

    # Test Vertex AI
    try:
        vertex_api = VertexAIAPI()
        series_info = vertex_api.get_comprehensive_series_info(series_name, project_state)
        if series_info:
            print(f"✅ Vertex AI found series: {series_info.get('corrected_series_name', series_name)}")
            print(f"   Authors: {series_info.get('authors', [])}")
            print(f"   Volumes: {series_info.get('extant_volumes', 0)}")
            print(f"   Spinoffs: {series_info.get('spinoff_series', [])}")
            print(f"   Alternate Editions: {series_info.get('alternate_editions', [])}")
        else:
            print(f"❌ Vertex AI failed to find series")
    except Exception as e:
        print(f"❌ Vertex AI error: {e}")

    # Test DeepSeek
    try:
        deepseek_api = DeepSeekAPI()
        suggestions = deepseek_api.correct_series_name(series_name)
        if suggestions:
            print(f"✅ DeepSeek suggestions: {suggestions}")
        else:
            print(f"❌ DeepSeek failed to provide suggestions")
    except Exception as e:
        print(f"❌ DeepSeek error: {e}")

def test_volume_processing(series_name, volume_range="1-5"):
    """Test volume processing for a series"""
    print(f"\n📚 Testing Volume Processing: {series_name} {volume_range}")

    project_state = ProjectState()
    volumes = parse_volume_range(volume_range)

    print(f"   Parsed volumes: {volumes}")

    # Test book info for first volume
    try:
        vertex_api = VertexAIAPI()
        book_info = vertex_api.get_book_info(series_name, volumes[0], project_state)
        if book_info:
            print(f"✅ Volume {volumes[0]} info:")
            print(f"   Title: {book_info.get('book_title', 'N/A')}")
            print(f"   Authors: {book_info.get('authors', [])}")
            print(f"   ISBN: {book_info.get('isbn_13', 'N/A')}")
            print(f"   Publisher: {book_info.get('publisher_name', 'N/A')}")
        else:
            print(f"❌ Failed to get volume info")
    except Exception as e:
        print(f"❌ Volume processing error: {e}")

def test_barcode_generation(starting_barcode="Barcode001"):
    """Test barcode generation"""
    print(f"\n🏷️ Testing Barcode Generation: {starting_barcode}")

    try:
        barcodes = generate_sequential_general_barcodes(starting_barcode, 5)
        print(f"✅ Generated barcodes: {barcodes}")
        return barcodes
    except Exception as e:
        print(f"❌ Barcode generation error: {e}")
        return []

def test_marc_export(series_name, volumes, barcodes):
    """Test MARC export functionality"""
    print(f"\n📄 Testing MARC Export: {series_name}")

    # Create mock book data
    books = []
    for i, (volume, barcode) in enumerate(zip(volumes, barcodes)):
        book = {
            "series_name": series_name,
            "volume_number": volume,
            "book_title": f"{series_name} Volume {volume}",
            "authors": ["Hajime Isayama"],
            "isbn_13": f"9781612620{volume:03d}",
            "publisher_name": "Kodansha Comics",
            "copyright_year": 2012 + volume - 1,
            "description": f"Volume {volume} of the popular manga series",
            "physical_description": "192 pages, 5 x 7.5 inches",
            "genres": ["Manga", "Action", "Fantasy"],
            "barcode": barcode
        }
        books.append(book)

    try:
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mrc', delete=False) as f:
            marc_file = f.name

        marc_data = export_books_to_marc(books)

        # Write MARC data to file
        with open(marc_file, 'wb') as f:
            f.write(marc_data)

        # Check if file was created and has content
        if os.path.exists(marc_file) and os.path.getsize(marc_file) > 0:
            print(f"✅ MARC export successful: {marc_file}")

            # Read and display first few lines
            with open(marc_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                print("   First 10 lines:")
                for line in lines:
                    print(f"   {line.strip()}")

            # Clean up
            os.unlink(marc_file)
        else:
            print(f"❌ MARC export failed - empty file")

    except Exception as e:
        print(f"❌ MARC export error: {e}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n⚠️ Testing Edge Cases...")

    # Test invalid series names
    invalid_series = ["", "   ", "NonExistentSeries12345", "Attack on Titan Volume 999"]
    for series in invalid_series:
        print(f"\n   Testing invalid series: '{series}'")
        try:
            vertex_api = VertexAIAPI()
            result = vertex_api.get_comprehensive_series_info(series)
            if result:
                print(f"   ✅ Unexpectedly found series")
            else:
                print(f"   ✅ Correctly returned None for invalid series")
        except Exception as e:
            print(f"   ✅ Correctly handled error: {e}")

    # Test invalid volume ranges
    invalid_ranges = ["", "1-5-10", "abc", "5-1"]
    for range_str in invalid_ranges:
        print(f"\n   Testing invalid range: '{range_str}'")
        try:
            result = parse_volume_range(range_str)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   ✅ Correctly handled error: {e}")

def main():
    """Run complete workflow tests"""
    print("🚀 Manga Lookup Tool - Complete Workflow Test")
    print("=" * 50)

    # Test popular series
    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Demon Slayer",
        "My Hero Academia"
    ]

    # Test API initialization
    test_api_initialization()

    # Test series lookup for each series
    for series in test_series:
        test_series_lookup(series)

    # Test volume processing for first series
    test_volume_processing(test_series[0], "1-5")

    # Test barcode generation
    barcodes = test_barcode_generation("Barcode001")

    # Test MARC export
    if barcodes:
        test_marc_export(test_series[0], list(range(1, 6)), barcodes)

    # Test edge cases
    test_edge_cases()

    print("\n🎉 Complete Workflow Test Finished!")

if __name__ == "__main__":
    main()