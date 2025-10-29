#!/usr/bin/env python3
"""
Check series names for encoding issues and invisible characters
"""

import sys
sys.path.append('.')
from bigquery_cache import BigQueryCache

def check_series_encoding():
    cache = BigQueryCache()
    print('Checking series names for encoding issues:')
    print('==========================================')

    # Check One Piece specifically with detailed analysis
    query = "SELECT series_name FROM static-webbing-461904-c4.manga_lookup_cache.volume_info WHERE series_name LIKE '%One Piece%' GROUP BY series_name"
    df = cache.client.query(query).to_dataframe()
    print('\nOne Piece series name analysis:')
    for index, row in df.iterrows():
        name = row['series_name']
        print(f'  - Name: "{name}"')
        print(f'    Length: {len(name)}')
        print(f'    ASCII only: {name.isascii()}')
        print(f'    Printable: {name.isprintable()}')
        print(f'    Encoded bytes: {name.encode("utf-8")}')
        print(f'    Character codes: {[ord(c) for c in name]}')

    # Check for any series with non-printable characters
    query = "SELECT series_name FROM static-webbing-461904-c4.manga_lookup_cache.volume_info GROUP BY series_name"
    df = cache.client.query(query).to_dataframe()

    problematic_names = []
    for index, row in df.iterrows():
        name = row['series_name']
        if not name.isprintable():
            problematic_names.append(name)

    if problematic_names:
        print('\nSeries with non-printable characters:')
        for name in problematic_names:
            print(f'  - "{name}" (non-printable)')
    else:
        print('\nNo series with non-printable characters')

if __name__ == "__main__":
    check_series_encoding()