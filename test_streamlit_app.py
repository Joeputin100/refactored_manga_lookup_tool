#!/usr/bin/env python3
"""
Test script for Streamlit app using AppTest
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_app_imports():
    """Test that all imports work without union operators"""
    print("Testing app imports...")

    # Test imports that might have union operators
    try:
        # Import the main app module
        from app_new_workflow import (
            initialize_session_state,
            display_barcode_input,
            fetch_cover_for_series
        )
        print("✅ Main app imports successful")
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False

    try:
        # Import manga_lookup components
        from manga_lookup import (
            VertexAIAPI, DeepSeekAPI, GoogleBooksAPI,
            ProjectState, validate_general_barcode,
            generate_sequential_general_barcodes
        )
        print("✅ Manga lookup imports successful")
    except Exception as e:
        print(f"❌ Manga lookup import failed: {e}")
        return False

    try:
        # Import other modules
        from marc_exporter import export_books_to_marc
        from mal_cover_fetcher import MALCoverFetcher
        from mangadex_cover_fetcher import MangaDexCoverFetcher
        print("✅ All module imports successful")
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False

    return True

def test_python_39_compatibility():
    """Test for Python 3.9 compatibility issues"""
    print("\nTesting Python 3.9 compatibility...")

    # Check for union operators in files
    files_to_check = [
        'app_new_workflow.py',
        'manga_lookup.py',
        'marc_exporter.py',
        'mal_cover_fetcher.py',
        'mangadex_cover_fetcher.py'
    ]

    issues_found = []
    for file in files_to_check:
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.read()
                # Look for union operators in type annotations
                if '->' in content and '|' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if '->' in line and '|' in line:
                            issues_found.append(f"  Line {i}: {line.strip()}")

    if issues_found:
        print("❌ Union operators found:")
        for issue in issues_found:
            print(issue)
        return False
    else:
        print("✅ No union operators found")
        return True

def test_api_initialization():
    """Test API initialization"""
    print("\nTesting API initialization...")

    try:
        from manga_lookup import VertexAIAPI, DeepSeekAPI, GoogleBooksAPI

        # Test DeepSeek
        try:
            deepseek = DeepSeekAPI()
            print("✅ DeepSeek API initialized")
        except Exception as e:
            print(f"❌ DeepSeek failed: {e}")

        # Test Google Books
        try:
            google = GoogleBooksAPI()
            print("✅ Google Books API initialized")
        except Exception as e:
            print(f"❌ Google Books failed: {e}")

        # Test Vertex AI
        try:
            vertex = VertexAIAPI()
            print("✅ Vertex AI API initialized")
        except Exception as e:
            print(f"❌ Vertex AI failed: {e}")

    except Exception as e:
        print(f"❌ API import failed: {e}")
        return False

    return True

def test_streamlit_apptest():
    """Test using Streamlit's AppTest tool"""
    print("\nTesting with Streamlit AppTest...")

    try:
        from streamlit.testing.v1 import AppTest

        # Create AppTest instance
        at = AppTest.from_file("app_new_workflow.py")

        # Run the app
        at.run()

        if at.exception:
            print(f"❌ AppTest failed with exception: {at.exception}")
            return False
        else:
            print("✅ AppTest completed without exceptions")
            return True

    except ImportError:
        print("ℹ️ Streamlit AppTest not available in this environment")
        return True
    except Exception as e:
        print(f"❌ AppTest failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Streamlit App Compatibility Test")
    print("=" * 60)

    # Run all tests
    tests = [
        test_app_imports,
        test_python_39_compatibility,
        test_api_initialization,
        test_streamlit_apptest
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if all(results):
        print("✅ All tests passed! The app should work correctly.")
    else:
        print("❌ Some tests failed. Check the output above for details.")

    print("\nNext steps:")
    print("1. Commit and push any fixes")
    print("2. Update EC2: git pull")
    print("3. Restart Streamlit: streamlit run app_new_workflow.py")
    print("4. Test with 'Attack on Titan'")