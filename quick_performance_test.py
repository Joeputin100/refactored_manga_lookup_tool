#!/usr/bin/env python3
"""
Quick cache performance test
"""
import time
from app_new_workflow import search_series_info

print("🎯 Quick Cache Performance Test")
print("=" * 50)

# Test cached series
cached_series = ["Attack on Titan", "Attack on Titan: Colossal Edition", "Attack on Titan: No Regrets"]
print("\n🔍 Cached Series (Fast):")
cached_times = []
for series in cached_series:
    start = time.time()
    results = search_series_info(series)
    end = time.time()
    time_ms = (end - start) * 1000
    cached_times.append(time_ms)
    cache_status = "CACHE HIT" if results and results[0].get("source", "").endswith("(Cached)") else "API CALL"
    print(f"   📖 {series:<30} | {time_ms:6.1f}ms | {cache_status}")

# Test non-cached series
non_cached_series = ["Tokyo Ghoul", "Berserk", "Death Note"]
print("\n🔍 Non-Cached Series (Slow):")
non_cached_times = []
for series in non_cached_series:
    start = time.time()
    results = search_series_info(series)
    end = time.time()
    time_ms = (end - start) * 1000
    non_cached_times.append(time_ms)
    cache_status = "CACHE HIT" if results and results[0].get("source", "").endswith("(Cached)") else "API CALL"
    print(f"   📖 {series:<30} | {time_ms:6.1f}ms | {cache_status}")

# Calculate performance improvement
if cached_times and non_cached_times:
    avg_cached = sum(cached_times) / len(cached_times)
    avg_non_cached = sum(non_cached_times) / len(non_cached_times)
    speedup = (avg_non_cached - avg_cached) / avg_non_cached * 100

    print(f"\n📈 Performance Summary:")
    print(f"   Cached average:   {avg_cached:6.1f}ms")
    print(f"   API Call average: {avg_non_cached:6.1f}ms")
    print(f"   Speedup:          {speedup:6.1f}% faster")

print("\n✅ Quick test completed!")