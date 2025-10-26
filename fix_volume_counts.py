#!/usr/bin/env python3
"""
Fix volume count issue - update series cache with actual volume counts
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def fix_volume_counts():
    """Update series cache with actual volume counts"""
    cache = BigQueryCache()

    print('🔧 Fixing volume counts...')

    # Get all series from cache
    query = """
    SELECT DISTINCT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    ORDER BY series_name
    """
    query_job = cache.client.query(query)
    series_list = [row['series_name'] for row in query_job]

    print(f'📊 Found {len(series_list)} series to update')

    updated_count = 0

    for series_name in series_list:
        try:
            # Get current series info
            series_info = cache.get_series_info(series_name)
            if not series_info:
                continue

            # Count actual volumes
            volume_query = f"""
            SELECT COUNT(*) as volume_count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """
            volume_job = cache.client.query(volume_query)
            volume_count = list(volume_job)[0]['volume_count']

            # Update series info with correct volume count
            series_info['extant_volumes'] = volume_count

            # Re-cache the series info
            cache.cache_series_info(series_name, series_info, api_source="volume_count_fix")

            print(f'✅ {series_name}: {volume_count} volumes')
            updated_count += 1

        except Exception as e:
            print(f'❌ {series_name}: Error - {e}')

    print(f'\n🎯 Update complete: {updated_count}/{len(series_list)} series updated')

if __name__ == "__main__":
    fix_volume_counts()