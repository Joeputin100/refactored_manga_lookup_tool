#!/usr/bin/env python3
"""
Test Streamlit app cache lookup directly
"""
import sys
import traceback

# Redirect stderr to stdout to capture all output
sys.stderr = sys.stdout

print("🔍 Testing Streamlit App Cache Lookup")
print("=" * 50)

try:
    print("\n📦 Importing Streamlit and app components...")
    import streamlit as st
    from app_new_workflow import initialize_session_state

    print("✅ Imports successful")

    print("\n🔧 Initializing session state...")
    initialize_session_state()
    print("✅ Session state initialized")

    print("\n🔍 Testing cache lookup for 'Attack on Titan'...")

    # Test the cache lookup directly
    cached_info = st.session_state.project_state.get_cached_series_info("Attack on Titan")

    if cached_info:
        print(f"✅ CACHE HIT!")
        print(f"   Data: {cached_info}")
    else:
        print(f"❌ CACHE MISS")

    print("\n🔍 Testing cache lookup for 'attack on titan' (lowercase)...")

    # Test with lowercase
    cached_info_lower = st.session_state.project_state.get_cached_series_info("attack on titan")

    if cached_info_lower:
        print(f"✅ CACHE HIT!")
        print(f"   Data: {cached_info_lower}")
    else:
        print(f"❌ CACHE MISS")

    print("\n✅ Streamlit cache test completed!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    traceback.print_exc()