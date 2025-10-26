#!/usr/bin/env python3
"""
Check cover image status in BigQuery cache
"""

from bigquery_cache import BigQueryCache

def check_cover_image():
    cache = BigQueryCache()

    # Check if cover_image_url exists in the cache
    query = 'SELECT series_name, cover_image_url FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE series_name = "Attack on Titan"'

    print('📊 Cover image status in BigQuery cache:')
    try:
        result = cache.client.query(query).result()
        for row in result:
            print(f'   Series: {row.series_name}')
            print(f'   Cover URL: {row.cover_image_url if hasattr(row, "cover_image_url") else "❌ No cover_image_url field"}')

            # Check if the URL is valid
            if hasattr(row, 'cover_image_url') and row.cover_image_url:
                print(f'   Cover URL exists: {row.cover_image_url}')
            else:
                print('   ❌ No cover image URL in cache')
    except Exception as e:
        print(f'❌ Error querying cover image: {e}')

if __name__ == "__main__":
    check_cover_image()