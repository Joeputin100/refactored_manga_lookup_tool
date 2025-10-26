#!/usr/bin/env python3
"""
Simple Performance Test for Manga Lookup Tool
Tests cached vs uncached series with performance metrics
"""

import time
import json
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_performance_test():
    """Run simple performance test"""

    print("🎯 Manga Lookup Tool - Performance Test")
    print("=" * 60)

    # Import required modules
    try:
        import streamlit as st
        from app_new_workflow import search_series_info
        from manga_lookup import ProjectState, get_volume_info
        from marc_exporter import export_books_to_marc
        from label_generator import generate_labels_pdf
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    # Initialize session state
    st.session_state.project_state = ProjectState()
    st.session_state.debug_mode = True

    # Test series
    cached_series = "Attack on Titan"  # Should be in cache
    uncached_series = "Tokyo Ghoul"    # Should not be in cache

    test_results = {
        "timestamp": datetime.now().isoformat(),
        "cached_series": {},
        "uncached_series": {}
    }

    print(f"\n📊 Testing Cached Series: {cached_series}")
    print("-" * 40)

    # Test cached series
    start_time = time.time()

    # Step 1: Series info lookup
    series_start = time.time()
    series_info = search_series_info(cached_series)
    series_time = time.time() - series_start

    print(f"✅ Series Info: {series_time:.2f}s")
    if series_info:
        print(f"   Cache Hit: {series_info.get('cached', False)}")
        print(f"   Source: {series_info.get('cache_source', 'API')}")

    # Step 2: Volume info lookup (5 volumes)
    volume_times = []
    volumes_data = []
    for vol_num in range(1, 6):
        vol_start = time.time()
        volume_info = get_volume_info(cached_series, vol_num)
        vol_time = time.time() - vol_start
        volume_times.append(vol_time)

        if volume_info:
            volumes_data.append(volume_info)
            print(f"   Volume {vol_num}: {vol_time:.2f}s (Cache: {volume_info.get('cached', False)})")
        else:
            print(f"   Volume {vol_num}: ❌ Not found")

    # Step 3: MARC export
    marc_start = time.time()
    if volumes_data:
        marc_filename = export_books_to_marc(volumes_data)
        marc_time = time.time() - marc_start
        print(f"✅ MARC Export: {marc_time:.2f}s -> {marc_filename}")
    else:
        marc_time = 0
        print("❌ MARC Export: No volumes to export")

    # Step 4: Label PDF generation
    pdf_start = time.time()
    if volumes_data:
        pdf_filename = generate_labels_pdf(volumes_data)
        pdf_time = time.time() - pdf_start
        print(f"✅ PDF Labels: {pdf_time:.2f}s -> {pdf_filename}")
    else:
        pdf_time = 0
        print("❌ PDF Labels: No volumes to generate")

    total_time = time.time() - start_time

    # Store results
    test_results["cached_series"] = {
        "series_name": cached_series,
        "series_info_time": series_time,
        "volume_times": volume_times,
        "marc_export_time": marc_time,
        "pdf_generation_time": pdf_time,
        "total_time": total_time,
        "volumes_processed": len(volumes_data)
    }

    print(f"\n📊 Testing Uncached Series: {uncached_series}")
    print("-" * 40)

    # Test uncached series
    start_time = time.time()

    # Step 1: Series info lookup
    series_start = time.time()
    series_info = search_series_info(uncached_series)
    series_time = time.time() - series_start

    print(f"✅ Series Info: {series_time:.2f}s")
    if series_info:
        print(f"   Cache Hit: {series_info.get('cached', False)}")
        print(f"   Source: {series_info.get('cache_source', 'API')}")

    # Step 2: Volume info lookup (5 volumes)
    volume_times = []
    volumes_data = []
    for vol_num in range(1, 6):
        vol_start = time.time()
        volume_info = get_volume_info(uncached_series, vol_num)
        vol_time = time.time() - vol_start
        volume_times.append(vol_time)

        if volume_info:
            volumes_data.append(volume_info)
            print(f"   Volume {vol_num}: {vol_time:.2f}s (Cache: {volume_info.get('cached', False)})")
        else:
            print(f"   Volume {vol_num}: ❌ Not found")

    # Step 3: MARC export
    marc_start = time.time()
    if volumes_data:
        marc_filename = export_books_to_marc(volumes_data)
        marc_time = time.time() - marc_start
        print(f"✅ MARC Export: {marc_time:.2f}s -> {marc_filename}")
    else:
        marc_time = 0
        print("❌ MARC Export: No volumes to export")

    # Step 4: Label PDF generation
    pdf_start = time.time()
    if volumes_data:
        pdf_filename = generate_labels_pdf(volumes_data)
        pdf_time = time.time() - pdf_start
        print(f"✅ PDF Labels: {pdf_time:.2f}s -> {pdf_filename}")
    else:
        pdf_time = 0
        print("❌ PDF Labels: No volumes to generate")

    total_time = time.time() - start_time

    # Store results
    test_results["uncached_series"] = {
        "series_name": uncached_series,
        "series_info_time": series_time,
        "volume_times": volume_times,
        "marc_export_time": marc_time,
        "pdf_generation_time": pdf_time,
        "total_time": total_time,
        "volumes_processed": len(volumes_data)
    }

    # Performance Summary
    print("\n📈 PERFORMANCE SUMMARY")
    print("=" * 60)

    cached = test_results["cached_series"]
    uncached = test_results["uncached_series"]

    print(f"\n🔍 Cached Series ({cached['series_name']}):")
    print(f"   Series Info: {cached['series_info_time']:.2f}s")
    print(f"   Avg Volume: {sum(cached['volume_times'])/len(cached['volume_times']):.2f}s")
    print(f"   MARC Export: {cached['marc_export_time']:.2f}s")
    print(f"   PDF Labels: {cached['pdf_generation_time']:.2f}s")
    print(f"   Total Time: {cached['total_time']:.2f}s")

    print(f"\n🔍 Uncached Series ({uncached['series_name']}):")
    print(f"   Series Info: {uncached['series_info_time']:.2f}s")
    print(f"   Avg Volume: {sum(uncached['volume_times'])/len(uncached['volume_times']):.2f}s")
    print(f"   MARC Export: {uncached['marc_export_time']:.2f}s")
    print(f"   PDF Labels: {uncached['pdf_generation_time']:.2f}s")
    print(f"   Total Time: {uncached['total_time']:.2f}s")

    # Calculate speedup
    if cached['total_time'] > 0:
        speedup = uncached['total_time'] / cached['total_time']
        print(f"\n🚀 Performance Speedup: {speedup:.2f}x faster with cache")
    else:
        print(f"\n⚠️ Cannot calculate speedup (cached time is 0)")

    # Save results to JSON
    results_file = f"performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)

    print(f"\n📄 Results saved to: {results_file}")

    return test_results

if __name__ == "__main__":
    run_performance_test()