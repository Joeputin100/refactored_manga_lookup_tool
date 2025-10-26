#!/usr/bin/env python3
"""
Check Wikipedia imported series in BigQuery
"""
from bigquery_cache import BigQueryCache

def main():
    bq = BigQueryCache()

    # Query for Wikipedia imported series
    query = '''
    SELECT DISTINCT series_name, corrected_name, api_source
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE api_source LIKE "%wikipedia%"
    '''

    result = bq.client.query(query)
    wikipedia_series = list(result)

    print(f'Wikipedia imported series: {len(wikipedia_series)}')
    print("=" * 50)

    for series in wikipedia_series:
        name = series.get('corrected_name') or series.get('series_name')
        print(f"  - {name}")

    # Also check total series count
    total_query = 'SELECT COUNT(DISTINCT series_name) as total FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`'
    total_result = bq.client.query(total_query)
    total_count = list(total_result)[0]['total']

    print(f"\nTotal series in cache: {total_count}")

if __name__ == "__main__":
    main()