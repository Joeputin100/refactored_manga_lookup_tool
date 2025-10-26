#!/usr/bin/env python3
"""
Check field names in BigQuery cache
"""
from bigquery_cache import BigQueryCache

def check_fields():
    cache = BigQueryCache()
    print('✅ BigQuery cache initialized')

    # Get one row to check field names
    query = 'SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE series_name = "Attack on Titan" LIMIT 1'
    result = cache.client.query(query).result()

    for row in result:
        print('📋 Available fields:')
        for attr in dir(row):
            if not attr.startswith('_'):
                value = getattr(row, attr)
                print(f'   {attr}: {type(value).__name__} = {value}')
        break

if __name__ == "__main__":
    check_fields()