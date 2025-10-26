#!/usr/bin/env python3
"""
Quick test for MLE Star cache optimization
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def test_quick_performance():
    """Quick test to verify MLE Star components work"""
    print("🔍 Quick MLE Star Performance Test...")

    try:
        # Initialize cache
        bigquery_cache = BigQueryCache()

        if not bigquery_cache.enabled:
            print("⚠️ BigQuery cache not available")
            return

        print("✅ BigQuery cache available")

        # Test the new batch query method
        print("\n📊 Testing batch query method...")

        # Test with a small batch
        volumes = [1, 2, 3]
        start_time = time.time()
        results = bigquery_cache.get_volumes_for_series("Attack on Titan", volumes)
        batch_time = time.time() - start_time

        print(f"   Batch query time: {batch_time:.4f} seconds")
        print(f"   Results: {sum(1 for r in results if r)}/{len(results)} found")

        # Test individual queries for comparison
        print("\n📊 Testing individual queries...")
        individual_times = []
        for volume in volumes:
            start_time = time.time()
            result = bigquery_cache.get_volume_info("Attack on Titan", volume)
            individual_time = time.time() - start_time
            individual_times.append(individual_time)
            print(f"   Volume {volume}: {individual_time:.4f} seconds - {'Found' if result else 'Not found'}")

        # Calculate performance improvement
        if batch_time > 0 and individual_times:
            total_individual_time = sum(individual_times)
            improvement = total_individual_time / batch_time
            print(f"\n🚀 Performance improvement: {improvement:.2f}x faster with batch queries")

        # Test cache statistics
        print(f"\n📈 Cache Statistics:")
        print(f"   Total volumes in test: {len(volumes)}")
        print(f"   Volumes found: {sum(1 for r in results if r)}")
        print(f"   Cache hit rate: {sum(1 for r in results if r) / len(volumes) * 100:.1f}%")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_performance()