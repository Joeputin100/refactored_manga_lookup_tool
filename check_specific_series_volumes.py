#!/usr/bin/env python3
"""
Check current volume data for specific problematic series
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def check_specific_series():
    """Check volume data for specific problematic series"""
    cache = BigQueryCache()

    print('🔍 Checking specific problematic series...')

    # The series you specifically mentioned
    problematic_series = [
        'Assassination Classroom',
        'A Polar Bear in Love',
        'Berserk'
    ]

    for series_name in problematic_series:
        print(f'\n--- {series_name} ---')

        # Get series info
        series_info = cache.get_series_info(series_name)
        if series_info:
            print(f'  Series total_volumes: {series_info.get("total_volumes", "Not found")}')
            print(f'  Series extant_volumes: {series_info.get("extant_volumes", "Not found")}')

        # Get actual volumes from volume table
        volume_query = f"""
        SELECT volume_number, book_title, isbn_13, publisher_name
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE series_name = '{series_name}'
        ORDER BY volume_number
        """
        volume_job = cache.client.query(volume_query)
        volumes = [dict(row) for row in volume_job]

        print(f'  Actual volumes in cache: {len(volumes)}')

        if volumes:
            print(f'  Volume details:')
            for vol in volumes:
                print(f'    Volume {vol["volume_number"]}: "{vol["book_title"]}"')
                print(f'      ISBN: {vol.get("isbn_13", "Unknown")}')
                print(f'      Publisher: {vol.get("publisher_name", "Unknown")}')
        else:
            print(f'  ❌ No volumes found in cache!')

        # Check what the expected volume count should be
        expected_counts = {
            'Assassination Classroom': 21,
            'A Polar Bear in Love': 5,
            'Berserk': 41
        }

        expected = expected_counts.get(series_name)
        if expected:
            print(f'  Expected volumes: {expected}')
            missing = expected - len(volumes)
            if missing > 0:
                print(f'  Missing volumes: {missing}')

if __name__ == "__main__":
    check_specific_series()