#!/usr/bin/env python3
"""
Check metadata completion for series table
"""

from bigquery_cache import BigQueryCache
import pandas as pd

def check_metadata_completion():
    cache = BigQueryCache()

    # Get all series data
    query = '''
    SELECT
      series_name,
      authors,
      publisher,
      genres,
      status,
      total_volumes,
      summary,
      cover_image_url
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    '''

    result = cache.client.query(query)
    df = pd.DataFrame([dict(row) for row in result])

    print('📊 Series Metadata Completion Report')
    print('=' * 50)

    # Check completion for each field
    total_series = len(df)
    print(f'Total Series: {total_series}')
    print()

    fields = ['authors', 'publisher', 'genres', 'status', 'total_volumes', 'summary', 'cover_image_url']

    for field in fields:
        non_null = df[field].notna().sum()
        if field == 'genres':
            # For genres, check if it's not empty string
            non_empty = df[field].apply(lambda x: bool(x) if isinstance(x, str) else False).sum()
            completion = (non_empty / total_series) * 100
            print(f'{field:15}: {non_empty}/{total_series} ({completion:.1f}%) - Non-empty strings')
        else:
            completion = (non_null / total_series) * 100
            print(f'{field:15}: {non_null}/{total_series} ({completion:.1f}%)')

    print()
    print('📋 Series with missing cover images (first 10):')
    missing_covers = df[df['cover_image_url'].isna()]['series_name'].head(10).tolist()
    for series in missing_covers:
        print(f'  - {series}')

    print()
    print('📋 Series with missing authors (first 10):')
    missing_authors = df[df['authors'].isna()]['series_name'].head(10).tolist()
    for series in missing_authors:
        print(f'  - {series}')

    print()
    print('📋 Series with missing publishers (first 10):')
    missing_publishers = df[df['publisher'].isna()]['series_name'].head(10).tolist()
    for series in missing_publishers:
        print(f'  - {series}')

    print()
    print('📋 Series with missing volumes (first 10):')
    missing_volumes = df[df['total_volumes'] == 0]['series_name'].head(10).tolist()
    for series in missing_volumes:
        print(f'  - {series}')

if __name__ == "__main__":
    check_metadata_completion()