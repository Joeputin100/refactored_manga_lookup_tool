#!/usr/bin/env python3
"""
Debug cover image extraction from BigQuery cache
"""
from bigquery_cache import BigQueryCache

def debug_cover():
    cache = BigQueryCache()
    print('✅ BigQuery cache initialized')

    # Test the exact query from get_series_info_from_bigquery
    series_name = "Attack on titan"
    query = f'''SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) = LOWER("{series_name}")'''

    print(f'🔍 Query: {query}')
    result = cache.client.query(query).result()

    row_count = 0
    for row in result:
        row_count += 1
        print(f'✅ Found series in BigQuery: {row.series_name}')

        # Check cover_image_url field
        if hasattr(row, 'cover_image_url'):
            cover_url = row.cover_image_url
            print(f'🖼️  Cover URL from row.cover_image_url: {cover_url}')
            print(f'📊 URL Type: {type(cover_url)}')
            print(f'📏 URL Length: {len(str(cover_url)) if cover_url else 0}')
        else:
            print('❌ No cover_image_url field found')

        # Check what fields are available
        print('📋 Available fields:')
        for attr in ['series_name', 'cover_image_url', 'authors', 'extant_volumes']:
            if hasattr(row, attr):
                value = getattr(row, attr)
                print(f'   {attr}: {value}')
            else:
                print(f'   {attr}: ❌ NOT FOUND')

        break

    if row_count == 0:
        print(f'❌ No series found in BigQuery for: {series_name}')

if __name__ == "__main__":
    debug_cover()