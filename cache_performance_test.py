#!/usr/bin/env python3
"""
Cache performance test script
Compares response times for cached vs non-cached series
"""
import time
import sys
import os
from datetime import datetime

class CachePerformanceTest:
    def __init__(self):
        self.results = []

    def test_series_info_lookup(self, series_name: str, test_name: str):
        """Test series info lookup performance"""
        try:
            from app_new_workflow import search_series_info

            start_time = time.time()
            results = search_series_info(series_name)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            result = {
                'test_name': test_name,
                'series_name': series_name,
                'response_time_ms': response_time,
                'results_count': len(results),
                'cache_status': 'cached' if results and results[0].get('source', '').endswith('(Cached)') else 'api_call',
                'timestamp': datetime.now()
            }

            self.results.append(result)
            return result

        except Exception as e:
            print(f"❌ Error testing {series_name}: {e}")
            return None

    def test_volume_lookup(self, series_name: str, volume_numbers: list, test_name: str):
        """Test volume lookup performance"""
        try:
            from bigquery_cache import BigQueryCache
            from manga_lookup import DeepSeekAPI, VertexAIAPI

            cache = BigQueryCache()
            deepseek_api = DeepSeekAPI()
            vertex_api = VertexAIAPI()

            volume_times = []
            cache_hits = 0
            api_calls = 0

            for volume_num in volume_numbers:
                start_time = time.time()

                # Try cache first
                cached_volume = cache.get_volume_info(series_name, volume_num)
                if cached_volume:
                    cache_hits += 1
                    end_time = time.time()
                else:
                    # Fallback to API
                    api_calls += 1
                    book_data = None
                    if deepseek_api:
                        try:
                            book_data = deepseek_api.get_book_info(series_name, volume_num, None)
                        except Exception:
                            pass

                    if not book_data and vertex_api:
                        try:
                            book_data = vertex_api.get_book_info(series_name, volume_num, None)
                        except Exception:
                            pass

                    end_time = time.time()

                volume_time = (end_time - start_time) * 1000
                volume_times.append(volume_time)

            avg_time = sum(volume_times) / len(volume_times) if volume_times else 0

            result = {
                'test_name': test_name,
                'series_name': series_name,
                'volumes_tested': volume_numbers,
                'avg_response_time_ms': avg_time,
                'cache_hits': cache_hits,
                'api_calls': api_calls,
                'cache_hit_rate': cache_hits / len(volume_numbers) * 100 if volume_numbers else 0,
                'timestamp': datetime.now()
            }

            self.results.append(result)
            return result

        except Exception as e:
            print(f"❌ Error testing volumes for {series_name}: {e}")
            return None

    def run_comprehensive_test(self):
        """Run comprehensive cache performance test"""
        print("🎯 Cache Performance Test")
        print("=" * 60)

        # Test series that should be cached (from pre-seed)
        cached_series = [
            "Attack on Titan",
            "Attack on Titan: Colossal Edition",
            "Attack on Titan: No Regrets",
            "Attack on Titan: Before the Fall"
        ]

        # Test series that should NOT be cached
        non_cached_series = [
            "Tokyo Ghoul",
            "Berserk",
            "Death Note",
            "Hunter x Hunter"
        ]

        print("\n📊 Testing Series Information Lookup")
        print("-" * 40)

        # Test cached series
        for series in cached_series:
            result = self.test_series_info_lookup(series, f"Cached Series - {series}")
            if result:
                status = "✅ CACHE HIT" if result['cache_status'] == 'cached' else "❌ CACHE MISS"
                print(f"{status} | {series:<30} | {result['response_time_ms']:6.1f}ms | {result['results_count']} results")

        # Test non-cached series
        for series in non_cached_series:
            result = self.test_series_info_lookup(series, f"Non-Cached Series - {series}")
            if result:
                status = "✅ CACHE HIT" if result['cache_status'] == 'cached' else "❌ CACHE MISS"
                print(f"{status} | {series:<30} | {result['response_time_ms']:6.1f}ms | {result['results_count']} results")

        print("\n📚 Testing Volume Lookup (5 volumes)")
        print("-" * 40)

        # Test volume lookup for cached series
        test_volumes = [1, 2, 3, 4, 5]

        for series in cached_series[:2]:  # Test first 2 cached series
            result = self.test_volume_lookup(series, test_volumes, f"Cached Volumes - {series}")
            if result:
                print(f"📖 {series:<30} | Avg: {result['avg_response_time_ms']:6.1f}ms | "
                      f"Cache: {result['cache_hits']}/5 ({result['cache_hit_rate']:.0f}%)")

        for series in non_cached_series[:2]:  # Test first 2 non-cached series
            result = self.test_volume_lookup(series, test_volumes, f"Non-Cached Volumes - {series}")
            if result:
                print(f"📖 {series:<30} | Avg: {result['avg_response_time_ms']:6.1f}ms | "
                      f"Cache: {result['cache_hits']}/5 ({result['cache_hit_rate']:.0f}%)")

        print("\n📈 Performance Summary")
        print("-" * 40)

        # Calculate averages
        cached_series_times = [r['response_time_ms'] for r in self.results
                              if 'Cached Series' in r['test_name'] and r['cache_status'] == 'cached']
        non_cached_series_times = [r['response_time_ms'] for r in self.results
                                  if 'Non-Cached Series' in r['test_name'] and r['cache_status'] == 'api_call']

        cached_volumes_times = [r['avg_response_time_ms'] for r in self.results
                               if 'Cached Volumes' in r['test_name'] and r['cache_hit_rate'] > 0]
        non_cached_volumes_times = [r['avg_response_time_ms'] for r in self.results
                                   if 'Non-Cached Volumes' in r['test_name'] and r['cache_hit_rate'] == 0]

        if cached_series_times:
            avg_cached_series = sum(cached_series_times) / len(cached_series_times)
            print(f"📊 Series Info - Cached:    {avg_cached_series:6.1f}ms (avg)")

        if non_cached_series_times:
            avg_non_cached_series = sum(non_cached_series_times) / len(non_cached_series_times)
            print(f"📊 Series Info - API Call:  {avg_non_cached_series:6.1f}ms (avg)")

        if cached_series_times and non_cached_series_times:
            speedup = (avg_non_cached_series - avg_cached_series) / avg_non_cached_series * 100
            print(f"🚀 Series Info Speedup:     {speedup:6.1f}% faster")

        if cached_volumes_times:
            avg_cached_volumes = sum(cached_volumes_times) / len(cached_volumes_times)
            print(f"\n📚 Volume Lookup - Cached:  {avg_cached_volumes:6.1f}ms (avg)")

        if non_cached_volumes_times:
            avg_non_cached_volumes = sum(non_cached_volumes_times) / len(non_cached_volumes_times)
            print(f"📚 Volume Lookup - API Call:{avg_non_cached_volumes:6.1f}ms (avg)")

        if cached_volumes_times and non_cached_volumes_times:
            speedup = (avg_non_cached_volumes - avg_cached_volumes) / avg_non_cached_volumes * 100
            print(f"🚀 Volume Lookup Speedup:   {speedup:6.1f}% faster")

        print("\n✅ Test completed successfully!")

        return self.results

if __name__ == "__main__":
    try:
        test = CachePerformanceTest()
        results = test.run_comprehensive_test()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()