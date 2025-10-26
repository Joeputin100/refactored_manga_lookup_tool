#!/usr/bin/env python3
"""
Simple cache test without Streamlit dependencies
"""
import time
from bigquery_cache import BigQueryCache

print("🔍 Simple Cache Performance Test")
print("=" * 50)

cache = BigQueryCache()

if not cache.enabled:
    print("❌ BigQuery cache not enabled")
    exit(1)

print("✅ BigQuery cache is enabled")

# Test cached series
cached_series = ["Attack on Titan", "Attack on Titan: Colossal Edition", "Attack on Titan: No Regrets"]
print("\n🔍 Cached Series (Fast):")
cached_times = []

for series in cached_series:
    start = time.time()
    result = cache.get_series_info(series)
    end = time.time()
    time_ms = (end - start) * 1000
    cached_times.append(time_ms)

    if result:
        print(f"   📖 {series:<30} | {time_ms:6.1f}ms | CACHE HIT")
    else:
        print(f"   📖 {series:<30} | {time_ms:6.1f}ms | CACHE MISS")

# Test non-cached series
non_cached_series = ["Tokyo Ghoul", "Berserk", "Death Note"]
print("\n🔍 Non-Cached Series (API calls):")
non_cached_times = []

for series in non_cached_series:
    start = time.time()
    result = cache.get_series_info(series)
    end = time.time()
    time_ms = (end - start) * 1000
    non_cached_times.append(time_ms)

    if result:
        print(f"   📖 {series:<30} | {time_ms:6.1f}ms | CACHE HIT")
    else:
        print(f"   📖 {series:<30} | {time_ms:6.1f}ms | CACHE MISS")

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