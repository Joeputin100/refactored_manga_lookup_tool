#!/usr/bin/env python3
"""
Simple test for MLE Star cache optimization
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mle_star_cache_optimizer import MLEStarCacheOptimizer
from bigquery_cache import BigQueryCache

def test_simple_performance():
    """Test simple cache performance"""
    print("🔍 Testing MLE Star Simple Performance...")

    try:
        # Initialize cache
        bigquery_cache = BigQueryCache()

        # Test if cache is available
        if not bigquery_cache.enabled:
            print("⚠️ BigQuery cache not available - testing locally")
            return

        print("✅ BigQuery cache available")

        # Test individual query performance
        start_time = time.time()
        result = bigquery_cache.get_volume_info("Attack on Titan", 1)
        individual_time = time.time() - start_time

        print(f"📊 Individual query time: {individual_time:.4f} seconds")
        print(f"📚 Result: {'Found' if result else 'Not found'}")

        # Test batch query performance
        optimizer = MLEStarCacheOptimizer(bigquery_cache)

        test_queries = [
            {'series_name': 'Attack on Titan', 'volume_number': 1},
            {'series_name': 'Attack on Titan', 'volume_number': 2},
            {'series_name': 'Attack on Titan', 'volume_number': 3},
        ]

        start_time = time.time()
        results = optimizer.batch_get_volume_info(test_queries)
        batch_time = time.time() - start_time

        print(f"📊 Batch query time: {batch_time:.4f} seconds")
        print(f"📚 Results: {sum(1 for r in results if r)}/{len(results)} found")

        # Calculate performance improvement
        if individual_time > 0 and batch_time > 0:
            improvement = (individual_time * len(test_queries)) / batch_time
            print(f"🚀 Performance improvement: {improvement:.2f}x faster")

        # Generate performance report
        report = optimizer.get_performance_report()
        print(f"\n📈 Performance Report:")
        for key, value in report.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     {k}: {v}")
            else:
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simple_performance()