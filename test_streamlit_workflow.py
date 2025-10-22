#!/usr/bin/env python3
"""
Test script to verify the complete Streamlit workflow
This simulates user interactions and tests the full workflow
"""

import sys
import os
import time
import requests
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_streamlit_app():
    """Test the Streamlit app by making HTTP requests"""
    print("🚀 Testing Streamlit App Workflow")
    print("=" * 50)

    # The app is running on EC2
    streamlit_url = "http://52.15.93.20:8501"

    print(f"📱 Testing Streamlit app at: {streamlit_url}")

    # Test 1: Check if app is accessible
    try:
        response = requests.get(streamlit_url, timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit app is accessible")
        else:
            print(f"❌ Streamlit app returned status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot access Streamlit app: {e}")
        return

    # Since we can't directly interact with Streamlit via HTTP (it's a web app),
    # let's test the core functionality through the APIs directly
    print("\n🔧 Testing Core APIs with Streamlit Secrets...")

    # Import the APIs - they should use Streamlit secrets
    try:
        from manga_lookup import DeepSeekAPI, VertexAIAPI, GoogleBooksAPI

        # Test DeepSeek API
        try:
            deepseek_api = DeepSeekAPI()
            print("✅ DeepSeek API initialized with Streamlit secrets")

            # Test series name correction
            suggestions = deepseek_api.correct_series_name("Attack on Titan")
            if suggestions:
                print(f"✅ DeepSeek suggestions: {suggestions[:3]}")  # Show first 3
            else:
                print("❌ DeepSeek failed to provide suggestions")
        except Exception as e:
            print(f"❌ DeepSeek API error: {e}")

        # Test Vertex AI API
        try:
            vertex_api = VertexAIAPI()
            print("✅ Vertex AI API initialized with Streamlit secrets")

            # Test series info
            series_info = vertex_api.get_comprehensive_series_info("Attack on Titan")
            if series_info:
                print(f"✅ Vertex AI found series: {series_info.get('corrected_series_name', 'Attack on Titan')}")
                print(f"   Authors: {series_info.get('authors', [])}")
                print(f"   Volumes: {series_info.get('extant_volumes', 0)}")
                print(f"   Spinoffs: {series_info.get('spinoff_series', [])}")
                print(f"   Alternate Editions: {series_info.get('alternate_editions', [])}")
            else:
                print("❌ Vertex AI failed to find series")
        except Exception as e:
            print(f"❌ Vertex AI API error: {e}")

        # Test Google Books API
        try:
            google_api = GoogleBooksAPI()
            print("✅ Google Books API initialized with Streamlit secrets")
        except Exception as e:
            print(f"❌ Google Books API error: {e}")

    except Exception as e:
        print(f"❌ Failed to import APIs: {e}")

    print("\n📚 Testing Volume Processing...")

    # Test volume processing
    try:
        from manga_lookup import parse_volume_range, generate_sequential_general_barcodes

        # Test volume range parsing
        volumes = parse_volume_range("1-5")
        print(f"✅ Volume range parsed: {volumes}")

        # Test barcode generation
        barcodes = generate_sequential_general_barcodes("Barcode001", 5)
        print(f"✅ Barcodes generated: {barcodes}")

        # Test book info for volumes
        vertex_api = VertexAIAPI()
        for volume in volumes[:2]:  # Test first 2 volumes
            book_info = vertex_api.get_book_info("Attack on Titan", volume)
            if book_info:
                print(f"✅ Volume {volume}: {book_info.get('book_title', 'N/A')}")
            else:
                print(f"❌ Failed to get info for volume {volume}")

    except Exception as e:
        print(f"❌ Volume processing error: {e}")

    print("\n📄 Testing MARC Export...")

    # Test MARC export
    try:
        from marc_exporter import export_books_to_marc

        # Create mock book data using BookInfo objects
        from manga_lookup import BookInfo
        books = []
        for i in range(1, 4):
            book = BookInfo(
                series_name="Attack on Titan",
                volume_number=i,
                book_title=f"Attack on Titan Volume {i}",
                authors=["Hajime Isayama"],
                msrp_cost=9.99,
                isbn_13=f"9781612620{i:03d}",
                publisher_name="Kodansha Comics",
                copyright_year=2012 + i - 1,
                description=f"Volume {i} of the popular manga series",
                physical_description="192 pages, 5 x 7.5 inches",
                genres=["Manga", "Action", "Fantasy"],
                warnings=[],
                barcode=f"Barcode00{i}",
                cover_image_url=None
            )
            books.append(book)

        marc_data = export_books_to_marc(books)
        if marc_data and len(marc_data) > 0:
            print(f"✅ MARC export successful ({len(marc_data)} bytes)")
            # Show first few characters
            print(f"   First 100 chars: {marc_data[:100]}")
        else:
            print("❌ MARC export failed")

    except Exception as e:
        print(f"❌ MARC export error: {e}")

    print("\n🖼️ Testing Cover Images...")

    # Test cover image fetching
    try:
        from mal_cover_fetcher import MALCoverFetcher
        from mangadex_cover_fetcher import MangaDexCoverFetcher

        # Test MAL cover fetcher
        mal_fetcher = MALCoverFetcher()
        mal_cover = mal_fetcher.fetch_cover("Attack on Titan")
        if mal_cover:
            print(f"✅ MAL cover found: {mal_cover}")
        else:
            print("❌ MAL cover not found")

        # Test MangaDex cover fetcher
        mangadex_fetcher = MangaDexCoverFetcher()
        mangadex_cover = mangadex_fetcher.fetch_cover("Attack on Titan")
        if mangadex_cover:
            print(f"✅ MangaDex cover found: {mangadex_cover}")
        else:
            print("❌ MangaDex cover not found")

    except Exception as e:
        print(f"❌ Cover image error: {e}")

    print("\n⚠️ Testing Edge Cases...")

    # Test edge cases
    try:
        from manga_lookup import parse_volume_range

        edge_cases = [
            ("", "Empty string"),
            ("1-5-10", "Invalid range"),
            ("abc", "Non-numeric"),
            ("5-1", "Reverse range")
        ]

        for case, description in edge_cases:
            result = parse_volume_range(case)
            print(f"   {description}: '{case}' -> {result}")

    except Exception as e:
        print(f"❌ Edge case testing error: {e}")

    print("\n🎉 Streamlit Workflow Test Complete!")
    print("\n📋 Summary:")
    print("   - APIs should be working with Streamlit secrets")
    print("   - Series lookup and volume processing should work")
    print("   - MARC export should generate valid data")
    print("   - Cover images should be fetched")
    print("   - Edge cases should be handled gracefully")
    print("\n🔍 Next: Test the actual Streamlit app manually at:")
    print(f"   {streamlit_url}")

if __name__ == "__main__":
    test_streamlit_app()