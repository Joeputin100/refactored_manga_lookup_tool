#!/usr/bin/env python3
"""
Debug the authors data structure issue
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_authors():
    """Debug authors data structure"""

    print("🔍 Debugging Authors Data Structure")
    print("=" * 50)

    try:
        from manga_lookup import ProjectState
        from bigquery_cache import BigQueryCache

        # Test 1: Check what the cached data actually looks like
        print("\n📊 Test 1: Direct BigQuery Cache Data")
        cache = BigQueryCache()
        if cache.enabled:
            result = cache.get_series_info("Inuyashiki")
            print(f"   Authors field: {result.get('authors')}")
            print(f"   Authors type: {type(result.get('authors'))}")
            if result.get('authors'):
                print(f"   First author: {result.get('authors')[0]}")
                print(f"   First author type: {type(result.get('authors')[0])}")

        # Test 2: Check ProjectState cache
        print("\n📊 Test 2: ProjectState Cache Data")
        project_state = ProjectState()
        result = project_state.get_cached_series_info("Inuyashiki")
        print(f"   Authors field: {result.get('authors')}")
        print(f"   Authors type: {type(result.get('authors'))}")
        if result.get('authors'):
            print(f"   First author: {result.get('authors')[0]}")
            print(f"   First author type: {type(result.get('authors')[0])}")

        # Test 3: Try to reproduce the error
        print("\n📊 Test 3: Reproduce the Join Error")
        if result and result.get('authors'):
            authors = result['authors']
            print(f"   Original authors: {authors}")
            try:
                joined = ", ".join([str(a) for a in authors])
                print(f"   ✅ Join successful: {joined}")
            except Exception as e:
                print(f"   ❌ Join failed: {e}")
                print(f"   Trying alternative approach...")
                # Try flattening nested lists
                flattened = []
                for author in authors:
                    if isinstance(author, list):
                        flattened.extend(author)
                    else:
                        flattened.append(author)
                print(f"   Flattened authors: {flattened}")
                try:
                    joined = ", ".join([str(a) for a in flattened])
                    print(f"   ✅ Flattened join successful: {joined}")
                except Exception as e2:
                    print(f"   ❌ Flattened join failed: {e2}")

    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_authors()