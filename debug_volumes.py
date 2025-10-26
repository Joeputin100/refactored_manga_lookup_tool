#!/usr/bin/env python3
"""
Debug volume count and duplicate issues
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def debug_berserk_volumes():
    """Debug Berserk volume data"""
    cache = BigQueryCache()

    # Check Berserk volumes using the same query as cache viewer
    print('🔍 Checking Berserk volumes:')
    query = f"""
    SELECT *
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name = 'Berserk'
    ORDER BY volume_number
    """
    query_job = cache.client.query(query)
    volumes = [dict(row) for row in query_job]
    print(f'Total volumes found: {len(volumes)}')

    # Group by volume number to find duplicates
    volume_numbers = {}
    for vol in volumes:
        vol_num = vol.get('volume_number', 'Unknown')
        book_title = vol.get('book_title', 'No title')

        if vol_num not in volume_numbers:
            volume_numbers[vol_num] = []
        volume_numbers[vol_num].append(book_title)

        print(f'  Volume {vol_num}: "{book_title}"')

    # Check for duplicates
    print('\n🔍 Duplicate volume numbers:')
    for vol_num, titles in volume_numbers.items():
        if len(titles) > 1:
            print(f'  Volume {vol_num}: {titles}')

    # Check series info for Berserk
    print('\n🔍 Checking Berserk series info:')
    series = cache.get_series_info('Berserk')
    if series:
        print(f'Extant volumes in series info: {series.get("extant_volumes", "Unknown")}')
        print(f'All series fields: {list(series.keys())}')

        # Check what fields are actually available
        for key, value in series.items():
            if key in ['extant_volumes', 'total_volumes']:
                print(f'  {key}: {value} (type: {type(value)})')
    else:
        print('No series info found')

def debug_volume_count_issue():
    """Debug why volume count shows 0"""
    cache = BigQueryCache()

    print('\n🔍 Debugging volume count issue:')

    # Check a few series
    test_series = ['Berserk', 'Attack on Titan', 'One Piece']

    for series_name in test_series:
        print(f'\n--- {series_name} ---')

        # Get series info
        series_info = cache.get_series_info(series_name)
        if series_info:
            extant_volumes = series_info.get('extant_volumes', 'Not found')
            print(f'  Series extant_volumes: {extant_volumes}')

            # Get actual volumes using same query as cache viewer
            query = f"""
            SELECT *
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            ORDER BY volume_number
            """
            query_job = cache.client.query(query)
            volumes = [dict(row) for row in query_job]
            print(f'  Actual volumes in cache: {len(volumes)}')

            # Check what fields are available
            print(f'  Available fields: {list(series_info.keys())}')

if __name__ == "__main__":
    debug_berserk_volumes()
    debug_volume_count_issue()