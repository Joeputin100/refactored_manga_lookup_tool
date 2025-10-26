#!/usr/bin/env python3
"""
Test BigQuery cache case sensitivity
"""
from bigquery_cache import BigQueryCache

print("🔍 Testing BigQuery Cache Case Sensitivity")
print("=" * 50)

cache = BigQueryCache()

# Test different case variations
test_cases = ["Attack on Titan", "attack on titan", "ATTACK ON TITAN"]

for series_name in test_cases:
    print(f"\nTesting: {series_name}")
    result = cache.get_series_info(series_name)
    if result:
        print(f"   ✅ CACHE HIT: {result.get('corrected_series_name')}")
    else:
        print(f"   ❌ CACHE MISS")

print("\n✅ Cache test completed")