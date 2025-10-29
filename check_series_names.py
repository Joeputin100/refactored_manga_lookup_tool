#!/usr/bin/env python3
"""
Check series names in database for validation issues
"""

import sys
sys.path.append('.')
from bigquery_cache import BigQueryCache

def check_series_names():
    cache = BigQueryCache()
    print('Checking series names in database:')
    print('==================================')

    # Check One Piece specifically
    query = "SELECT series_name FROM static-webbing-461904-c4.manga_lookup_cache.volume_info WHERE series_name LIKE '%One Piece%' GROUP BY series_name"
    df = cache.client.query(query).to_dataframe()
    print('\nOne Piece series names:')
    for index, row in df.iterrows():
        name = row['series_name']
        print(f'  - "{name}" (length: {len(name)})')

    # Check for any series with long names
    query = "SELECT series_name FROM static-webbing-461904-c4.manga_lookup_cache.volume_info GROUP BY series_name"
    df = cache.client.query(query).to_dataframe()
    print('\nAll series names (first 20):')
    for index, row in df.head(20).iterrows():
        name = row['series_name']
        print(f'  - "{name}" (length: {len(name)})')

    # Check for series with very long names
    long_names = []
    for index, row in df.iterrows():
        name = row['series_name']
        if len(name) > 100:
            long_names.append((name, len(name)))

    if long_names:
        print('\nSeries with very long names (>100 chars):')
        for name, length in long_names:
            print(f'  - "{name}" (length: {length})')
    else:
        print('\nNo series with names longer than 100 characters')

if __name__ == "__main__":
    check_series_names()