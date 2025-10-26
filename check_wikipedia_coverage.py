#!/usr/bin/env python3
"""
Check which Wikipedia series are already in the BigQuery cache
"""
from bigquery_cache import BigQueryCache
from wikipedia_complete_series_list import get_all_series

def check_wikipedia_coverage():
    """Check which Wikipedia series are in the cache"""
    bq = BigQueryCache()
    all_wikipedia_series = get_all_series()

    print(f"📊 Wikipedia Series Coverage in BigQuery Cache")
    print(f"=" * 60)
    print(f"Total Wikipedia Series: {len(all_wikipedia_series)}")

    # Get all series from cache
    query = 'SELECT DISTINCT series_name FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`'
    result = bq.client.query(query)
    cached_series = [row['series_name'] for row in result]

    print(f"Total Cached Series: {len(cached_series)}")

    # Check which Wikipedia series are in cache
    wikipedia_in_cache = []
    missing_wikipedia = []

    for series in all_wikipedia_series:
        # Try exact match first
        if series in cached_series:
            wikipedia_in_cache.append(series)
        else:
            # Try case-insensitive match
            series_lower = series.lower()
            cached_lower = [s.lower() for s in cached_series]
            if series_lower in cached_lower:
                # Find the actual cached name
                for cached_name in cached_series:
                    if cached_name.lower() == series_lower:
                        wikipedia_in_cache.append(f"{series} (cached as: {cached_name})")
                        break
            else:
                missing_wikipedia.append(series)

    print(f"\n✅ Wikipedia Series in Cache: {len(wikipedia_in_cache)}")
    print(f"❌ Missing Wikipedia Series: {len(missing_wikipedia)}")
    print(f"📈 Coverage: {len(wikipedia_in_cache)/len(all_wikipedia_series)*100:.1f}%")

    # Show series in cache
    print(f"\n📚 Wikipedia Series Already in Cache:")
    for series in sorted(wikipedia_in_cache):
        print(f"  - {series}")

    # Show missing series (first 20)
    print(f"\n📋 Missing Wikipedia Series (first 20):")
    for series in sorted(missing_wikipedia)[:20]:
        print(f"  - {series}")

    if len(missing_wikipedia) > 20:
        print(f"  ... and {len(missing_wikipedia) - 20} more")

if __name__ == "__main__":
    check_wikipedia_coverage()