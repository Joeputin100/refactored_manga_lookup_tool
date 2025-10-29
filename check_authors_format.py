#!/usr/bin/env python3
"""
Check authors field format in BigQuery
"""

from bigquery_cache import BigQueryCache

def check_authors_format():
    cache = BigQueryCache()

    # Check authors field format
    query = '''
    SELECT
      series_name,
      authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE authors IS NOT NULL
    LIMIT 10
    '''

    result = cache.client.query(query)
    print('📋 Sample Authors Field Format:')
    print('=' * 40)
    for row in result:
        print(f"{row['series_name']}: '{row['authors']}'")

if __name__ == "__main__":
    check_authors_format()