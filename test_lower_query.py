#!/usr/bin/env python3
"""
Test LOWER() function in BigQuery
"""

from bigquery_cache import BigQueryCache

def test_lower_query():
    cache = BigQueryCache()

    # Test the LOWER() function query
    query = """SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) = LOWER("Attack on titan")"""

    print(f'Testing query: {query}')
    try:
        result = cache.client.query(query).result()
        row_count = 0
        for row in result:
            row_count += 1
            print(f'✅ Found with LOWER(): {row.series_name}')

        if row_count == 0:
            print('❌ No results with LOWER()')
        else:
            print(f'✅ Success! Found {row_count} rows with LOWER()')
    except Exception as e:
        print(f'❌ Query failed: {e}')

if __name__ == "__main__":
    test_lower_query()