#!/usr/bin/env python3
"""
Batch API request optimizer for token efficiency and speed
Uses MLE-Star inspired optimization principles
"""
import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any
from warning_suppressor import configure_warnings

configure_warnings()

class BatchAPIOptimizer:
    """Optimizes API calls using batching and parallel processing"""

    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.stats = {
            'total_requests': 0,
            'batched_requests': 0,
            'sequential_time': 0,
            'batched_time': 0,
            'tokens_saved': 0
        }

    def batch_series_requests(self, series_list: List[str]) -> List[Dict[str, Any]]:
        """
        Batch process series information requests
        Returns list of results with timing information
        """
        print(f"🔧 Batch processing {len(series_list)} series...")

        # Sequential processing (baseline)
        print("\n🔍 Sequential processing (baseline)...")
        sequential_results = []
        sequential_start = time.time()

        for series in series_list:
            start_time = time.time()
            result = self._process_single_series(series)
            end_time = time.time()

            sequential_results.append({
                'series': series,
                'result': result,
                'time': end_time - start_time
            })

        sequential_time = time.time() - sequential_start
        self.stats['sequential_time'] = sequential_time

        print(f"   Sequential time: {sequential_time:.2f}s")
        print(f"   Average per series: {sequential_time/len(series_list):.2f}s")

        # Parallel processing
        print("\n🔧 Parallel processing...")
        parallel_start = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_series = {
                executor.submit(self._process_single_series, series): series
                for series in series_list
            }

            parallel_results = []
            for future in concurrent.futures.as_completed(future_to_series):
                series = future_to_series[future]
                try:
                    result = future.result()
                    parallel_results.append({
                        'series': series,
                        'result': result,
                        'parallel': True
                    })
                except Exception as e:
                    print(f"❌ Error processing {series}: {e}")

        parallel_time = time.time() - parallel_start
        self.stats['batched_time'] = parallel_time
        self.stats['total_requests'] = len(series_list)
        self.stats['batched_requests'] = len(parallel_results)

        print(f"   Parallel time: {parallel_time:.2f}s")
        print(f"   Speedup: {sequential_time/parallel_time:.2f}x faster")

        return parallel_results

    def _process_single_series(self, series_name: str) -> Dict[str, Any]:
        """Process a single series - simulate API call"""
        # Simulate API call delay
        time.sleep(0.5)  # Simulate 500ms API call

        # Mock response
        return {
            'series_name': series_name,
            'corrected_name': series_name.title(),
            'authors': ['Mock Author'],
            'total_volumes': 10,
            'summary': f'Mock summary for {series_name}',
            'cached': False
        }

    def optimize_cache_lookups(self, series_list: List[str]) -> Dict[str, Any]:
        """
        Optimize cache lookups by batching BigQuery queries
        """
        print(f"🔧 Optimizing cache lookups for {len(series_list)} series...")

        try:
            from bigquery_cache import BigQueryCache
            cache = BigQueryCache()

            if not cache.enabled:
                print("❌ BigQuery cache not available")
                return {}

            # Sequential cache lookups
            sequential_start = time.time()
            sequential_hits = 0

            for series in series_list:
                result = cache.get_series_info(series)
                if result:
                    sequential_hits += 1

            sequential_time = time.time() - sequential_start

            # Parallel cache lookups
            parallel_start = time.time()
            parallel_hits = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_series = {
                    executor.submit(cache.get_series_info, series): series
                    for series in series_list
                }

                for future in concurrent.futures.as_completed(future_to_series):
                    result = future.result()
                    if result:
                        parallel_hits += 1

            parallel_time = time.time() - parallel_start

            print(f"\n📊 Cache Lookup Optimization:")
            print(f"   Sequential: {sequential_time:.3f}s, {sequential_hits} hits")
            print(f"   Parallel:   {parallel_time:.3f}s, {parallel_hits} hits")
            print(f"   Speedup:    {sequential_time/parallel_time:.2f}x faster")

            return {
                'sequential_time': sequential_time,
                'parallel_time': parallel_time,
                'sequential_hits': sequential_hits,
                'parallel_hits': parallel_hits,
                'speedup': sequential_time / parallel_time
            }

        except Exception as e:
            print(f"❌ Cache optimization failed: {e}")
            return {}

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if self.stats['sequential_time'] > 0 and self.stats['batched_time'] > 0:
            speedup = self.stats['sequential_time'] / self.stats['batched_time']
            efficiency = (self.stats['batched_requests'] / self.stats['total_requests']) * 100

            return {
                'speedup': speedup,
                'efficiency': efficiency,
                'total_requests': self.stats['total_requests'],
                'successful_requests': self.stats['batched_requests'],
                'sequential_time': self.stats['sequential_time'],
                'batched_time': self.stats['batched_time'],
                'tokens_saved': self.stats['tokens_saved']
            }
        return {}

def test_batch_optimization():
    """Test the batch optimization system"""
    print("🔍 Testing Batch API Optimization")
    print("=" * 50)

    optimizer = BatchAPIOptimizer(max_workers=3, batch_size=5)

    # Test series
    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Dragon Ball Z",
        "Berserk",
        "Tokyo Ghoul",
        "Death Note",
        "Bleach",
        "Fairy Tail",
        "Hunter x Hunter"
    ]

    # Test batch processing
    results = optimizer.batch_series_requests(test_series)

    # Test cache optimization
    cache_stats = optimizer.optimize_cache_lookups(test_series)

    # Get optimization statistics
    stats = optimizer.get_optimization_stats()

    print(f"\n📈 Optimization Summary:")
    print(f"   Speedup: {stats.get('speedup', 0):.2f}x")
    print(f"   Efficiency: {stats.get('efficiency', 0):.1f}%")
    print(f"   Total requests: {stats.get('total_requests', 0)}")
    print(f"   Successful: {stats.get('successful_requests', 0)}")

    print("\n✅ Batch optimization test completed")

if __name__ == "__main__":
    test_batch_optimization()