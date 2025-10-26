#!/usr/bin/env python3
"""
MLE Star Cache Optimizer
Machine Learning Enhanced cache performance optimization for manga lookup system
"""
import sys
import os
import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import statistics

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

@dataclass
class CachePerformanceMetrics:
    """Performance metrics for cache operations"""
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    throughput_books_per_sec: float = 0.0

class MLEStarCacheOptimizer:
    """
    Machine Learning Enhanced cache optimizer for manga lookup system
    Implements advanced caching strategies to maximize performance
    """

    def __init__(self, bigquery_cache: BigQueryCache):
        self.bigquery_cache = bigquery_cache
        self.metrics = CachePerformanceMetrics()
        self.query_times = []
        self.batch_size = 50  # Optimal batch size for BigQuery
        self.connection_pool = []
        self.prefetch_predictions = {}

    def batch_get_volume_info(self, series_volumes: List[Dict[str, Any]]) -> List[Optional[Dict]]:
        """
        Batch query multiple volumes in a single BigQuery request
        This reduces network overhead and improves throughput
        """
        start_time = time.time()

        if not series_volumes:
            return []

        # Group by series for efficient querying
        series_groups = {}
        for sv in series_volumes:
            series = sv['series_name']
            volume = sv['volume_number']
            if series not in series_groups:
                series_groups[series] = []
            series_groups[series].append(volume)

        results = []

        # Process series in batches
        for series, volumes in series_groups.items():
            # Sort volumes to leverage sequential access patterns
            volumes.sort()

            # Query all volumes for this series in one go
            try:
                series_results = self.bigquery_cache.get_volumes_for_series(series, volumes)
                results.extend(series_results)

                # Update metrics
                self.metrics.cache_hits += len([r for r in series_results if r])
                self.metrics.cache_misses += len([r for r in series_results if not r])

            except Exception as e:
                print(f"❌ Batch query failed for {series}: {e}")
                # Fallback to individual queries
                for volume in volumes:
                    try:
                        result = self.bigquery_cache.get_volume_info(series, volume)
                        results.append(result)
                        if result:
                            self.metrics.cache_hits += 1
                        else:
                            self.metrics.cache_misses += 1
                    except Exception as e2:
                        print(f"❌ Individual query failed for {series} vol {volume}: {e2}")
                        results.append(None)
                        self.metrics.cache_misses += 1

        # Update performance metrics
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        self.query_times.append(query_time)
        self.metrics.total_queries += len(series_volumes)

        if self.query_times:
            self.metrics.avg_response_time_ms = statistics.mean(self.query_times)
            self.metrics.max_response_time_ms = max(self.query_times)
            self.metrics.min_response_time_ms = min(self.query_times)

        # Calculate throughput
        if query_time > 0:
            self.metrics.throughput_books_per_sec = (len(series_volumes) / (query_time / 1000))

        return results

    def get_volumes_for_series(self, series_name: str, volumes: List[int]) -> List[Optional[Dict]]:
        """
        Get multiple volumes for a series with optimized query strategy
        """
        series_volumes = [
            {'series_name': series_name, 'volume_number': volume}
            for volume in volumes
        ]
        return self.batch_get_volume_info(series_volumes)

    def prefetch_related_volumes(self, series_name: str, current_volume: int, prefetch_window: int = 5):
        """
        Prefetch related volumes based on access patterns
        Users typically access volumes sequentially
        """
        prefetch_volumes = []

        # Predict next volumes to access
        for i in range(1, prefetch_window + 1):
            prefetch_volumes.extend([
                current_volume + i,  # Next volumes
                current_volume - i   # Previous volumes (for browsing)
            ])

        # Filter valid volumes
        prefetch_volumes = [v for v in prefetch_volumes if v > 0]

        # Batch prefetch
        if prefetch_volumes:
            self.get_volumes_for_series(series_name, prefetch_volumes)
            print(f"🔮 Prefetched volumes {prefetch_volumes} for {series_name}")

    def optimize_query_patterns(self, query_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze query patterns and suggest optimizations
        """
        if not query_history:
            return {}

        # Analyze access patterns
        series_access = {}
        volume_sequences = {}

        for query in query_history:
            series = query.get('series_name')
            volume = query.get('volume_number')

            if series not in series_access:
                series_access[series] = 0
                volume_sequences[series] = []

            series_access[series] += 1
            volume_sequences[series].append(volume)

        # Calculate sequential access patterns
        sequential_ratios = {}
        for series, volumes in volume_sequences.items():
            if len(volumes) > 1:
                sequential_count = 0
                for i in range(1, len(volumes)):
                    if abs(volumes[i] - volumes[i-1]) == 1:
                        sequential_count += 1
                sequential_ratios[series] = sequential_count / (len(volumes) - 1)

        # Generate optimization recommendations
        recommendations = {
            'top_series': sorted(series_access.items(), key=lambda x: x[1], reverse=True)[:5],
            'sequential_patterns': sequential_ratios,
            'suggested_batch_sizes': {},
            'prefetch_recommendations': {}
        }

        # Suggest batch sizes based on access patterns
        for series, access_count in series_access.items():
            if access_count > 10:
                recommendations['suggested_batch_sizes'][series] = min(50, access_count)

            # Recommend prefetching for series with high sequential access
            seq_ratio = sequential_ratios.get(series, 0)
            if seq_ratio > 0.7:
                recommendations['prefetch_recommendations'][series] = {
                    'window_size': 5,
                    'confidence': seq_ratio
                }

        return recommendations

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        """
        hit_rate = (self.metrics.cache_hits / self.metrics.total_queries * 100) if self.metrics.total_queries > 0 else 0

        return {
            'total_queries': self.metrics.total_queries,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'cache_hit_rate_percent': round(hit_rate, 2),
            'avg_response_time_ms': round(self.metrics.avg_response_time_ms, 2),
            'throughput_books_per_sec': round(self.metrics.throughput_books_per_sec, 2),
            'performance_improvement': {
                'target_throughput': 1.0,  # Target: 1 book/second
                'current_throughput': round(self.metrics.throughput_books_per_sec, 2),
                'improvement_needed': max(0, 1.0 - self.metrics.throughput_books_per_sec)
            }
        }

def test_mle_star_optimization():
    """
    Test the MLE Star cache optimization
    """
    print("🚀 Testing MLE Star Cache Optimization...")

    # Initialize BigQuery cache
    try:
        bigquery_cache = BigQueryCache()
        optimizer = MLEStarCacheOptimizer(bigquery_cache)

        # Test data - simulate real-world access patterns
        test_queries = []

        # Sequential access pattern (common for manga reading)
        for volume in range(1, 11):
            test_queries.append({'series_name': 'Attack on Titan', 'volume_number': volume})

        # Mixed access pattern
        test_queries.extend([
            {'series_name': 'One Piece', 'volume_number': 1},
            {'series_name': 'Naruto', 'volume_number': 1},
            {'series_name': 'One Piece', 'volume_number': 2},
            {'series_name': 'Attack on Titan', 'volume_number': 5},  # Return to series
            {'series_name': 'Naruto', 'volume_number': 2},
        ])

        print(f"🔍 Testing with {len(test_queries)} queries...")

        # Test batch optimization
        start_time = time.time()
        results = optimizer.batch_get_volume_info(test_queries)
        batch_time = time.time() - start_time

        # Calculate performance
        books_per_second = len(test_queries) / batch_time if batch_time > 0 else 0

        print(f"\n📊 MLE Star Performance Results:")
        print(f"   Total queries: {len(test_queries)}")
        print(f"   Batch processing time: {batch_time:.2f} seconds")
        print(f"   Throughput: {books_per_second:.2f} books/second")

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

        # Test prefetching
        print(f"\n🔮 Testing prefetching...")
        optimizer.prefetch_related_volumes('Attack on Titan', 5)

        # Test query pattern optimization
        print(f"\n🧠 Analyzing query patterns...")
        recommendations = optimizer.optimize_query_patterns(test_queries)
        print(f"   Top series: {recommendations.get('top_series', [])}")
        print(f"   Suggested batch sizes: {recommendations.get('suggested_batch_sizes', {})}")

        # Performance targets
        target_throughput = 1.0
        current_throughput = books_per_second

        print(f"\n🎯 Performance Targets:")
        print(f"   Current throughput: {current_throughput:.2f} books/second")
        print(f"   Target throughput: {target_throughput:.2f} books/second")

        if current_throughput >= target_throughput:
            print(f"   ✅ TARGET ACHIEVED!")
        else:
            improvement_needed = target_throughput - current_throughput
            print(f"   🔧 Improvement needed: {improvement_needed:.2f} books/second")

    except Exception as e:
        print(f"❌ MLE Star test failed: {e}")

if __name__ == "__main__":
    test_mle_star_optimization()