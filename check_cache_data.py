#!/usr/bin/env python3
"""
Check BigQuery cache data
"""

from bigquery_cache import BigQueryCache

def main():
    cache = BigQueryCache()
    print('✅ BigQuery cache initialized')

    # Check series_info table data
    print('\n📊 Checking series_info table data:')
    try:
        # Use a simpler query
        query = """SELECT series_name FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`"""
        result = cache.client.query(query).result()
        series_count = 0
        for row in result:
            print(f'   Found series: {row.series_name}')
            series_count += 1
            if series_count >= 5:  # Limit manually
                break

        if series_count == 0:
            print('   ❌ No series found in cache!')
        else:
            print(f'   ✅ Found {series_count} series in cache')

    except Exception as e:
        print(f'   ❌ Error querying series table: {e}')

if __name__ == "__main__":
    main()