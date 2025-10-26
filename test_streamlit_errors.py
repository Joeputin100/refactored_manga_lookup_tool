#!/usr/bin/env python3
"""
Test Streamlit app for type errors with detailed traceback
"""
import sys
import traceback

# Redirect stderr to stdout to capture all output
sys.stderr = sys.stdout

print("🔍 Testing Streamlit App for Type Errors")
print("=" * 60)

try:
    print("\n📦 Importing Streamlit...")
    import streamlit as st
    print("✅ Streamlit imported successfully")

    print("\n📦 Importing app_new_workflow...")
    from app_new_workflow import main, search_series_info, initialize_session_state
    print("✅ App imports successful")

    print("\n🔧 Testing session state initialization...")
    try:
        initialize_session_state()
        print("✅ Session state initialized successfully")
    except Exception as e:
        print(f"❌ Session state initialization failed: {e}")
        traceback.print_exc()

    print("\n🔍 Testing series search with cached series...")
    try:
        # Test with a series that should be cached
        results = search_series_info("Attack on Titan")
        print(f"✅ Series search successful: {len(results)} results")
        for result in results:
            print(f"   - {result.get('name')} ({result.get('source')})")
    except Exception as e:
        print(f"❌ Series search failed: {e}")
        traceback.print_exc()

    print("\n🔍 Testing series search with non-cached series...")
    try:
        # Test with a series that should NOT be cached
        results = search_series_info("Tokyo Ghoul")
        print(f"✅ Series search successful: {len(results)} results")
        for result in results:
            print(f"   - {result.get('name')} ({result.get('source')})")
    except Exception as e:
        print(f"❌ Series search failed: {e}")
        traceback.print_exc()

    print("\n✅ All tests completed successfully!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    traceback.print_exc()

print("\n📊 Streamlit Error Test Complete")