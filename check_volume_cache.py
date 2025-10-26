#!/usr/bin/env python3
"""
Check volume cache status
"""
from bigquery_cache import BigQueryCache

def check_volume_cache():
    cache = BigQueryCache()
    print('✅ BigQuery cache initialized')

    # Check total volumes cached
    query = 'SELECT COUNT(*) as count FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`'
    result = cache.client.query(query).result()

    for row in result:
        print(f'📚 Total volumes cached: {row.count}')

    # Check if Attack on Titan volumes are cached
    query = """
    SELECT COUNT(*) as count
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name = "Attack on Titan"
    """
    result = cache.client.query(query).result()

    for row in result:
        print(f'📚 Attack on Titan volumes cached: {row.count}')

if __name__ == "__main__":
    check_volume_cache()