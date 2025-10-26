#!/usr/bin/env python3
"""
Debug script to test why cache isn't working in Streamlit app
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_cache():
    """Debug cache lookup issue"""

    print("🔍 Debugging Cache Lookup Issue")
    print("=" * 50)

    try:
        # Import required modules
        from manga_lookup import ProjectState
        from bigquery_cache import BigQueryCache

        print("✅ Modules imported successfully")

        # Test 1: Direct BigQuery cache lookup
        print("\n📊 Test 1: Direct BigQuery Cache Lookup")
        cache = BigQueryCache()
        if cache.enabled:
            result = cache.get_series_info("Inuyashiki")
            print(f"   BigQuery cache result: {result}")
            if result:
                print(f"   ✅ Cache HIT for Inuyashiki")
            else:
                print(f"   ❌ Cache MISS for Inuyashiki")
        else:
            print(f"   ❌ BigQuery cache not enabled")

        # Test 2: ProjectState cache lookup
        print("\n📊 Test 2: ProjectState Cache Lookup")
        project_state = ProjectState()
        result = project_state.get_cached_series_info("Inuyashiki")
        print(f"   ProjectState cache result: {result}")
        if result:
            print(f"   ✅ ProjectState cache HIT for Inuyashiki")
        else:
            print(f"   ❌ ProjectState cache MISS for Inuyashiki")

        # Test 3: Check if ProjectState is using BigQuery
        print("\n📊 Test 3: ProjectState Cache Implementation")
        print(f"   ProjectState type: {type(project_state)}")
        print(f"   ProjectState methods: {[m for m in dir(project_state) if not m.startswith('_')]}")

        # Test 4: Check session state cache
        print("\n📊 Test 4: Session State Cache")
        import streamlit as st
        st.session_state.project_state = project_state
        st.session_state.cache_series_info = {}

        result = st.session_state.project_state.get_cached_series_info("Inuyashiki")
        print(f"   Session State cache result: {result}")

    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cache()