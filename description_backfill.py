#!/usr/bin/env python3
"""Backfill missing descriptions using Google Books API"""

from bigquery_cache import BigQueryCache
from manga_lookup import GoogleBooksAPI

def backfill_descriptions():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return

    print('🔍 Finding volumes with missing descriptions...')

    # Query for volumes missing descriptions
    query = '''
    SELECT series_name, volume_number, book_title
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE description IS NULL OR description = ''
    '''

    job = cache.client.query(query)
    volumes = list(job.result())

    print(f'📚 Found {len(volumes)} volumes with missing descriptions')

    books_api = GoogleBooksAPI()
    processed = 0

    for vol in volumes:
        series_name = vol['series_name']
        volume_number = vol['volume_number']

        print(f'🔍 Processing: {series_name} Vol {volume_number}')

        # Try to get description from Google Books
        try:
            result = books_api.search_volume(series_name, volume_number)
            if result and 'description' in result and result['description']:
                description = result['description']

                # Update the database
                update_query = '''
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                SET description = @description
                WHERE series_name = @series_name AND volume_number = @volume_number
                '''

                job_config = {
                    'query': {
                        'parameterMode': 'NAMED',
                        'queryParameters': [
                            {'name': 'description', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': description}},
                            {'name': 'series_name', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': series_name}},
                            {'name': 'volume_number', 'parameterType': {'type': 'INT64'}, 'parameterValue': {'value': volume_number}}
                        ]
                    }
                }

                update_job = cache.client.query(update_query, job_config=job_config)
                update_job.result()  # Wait for completion

                print(f'✅ Updated description for {series_name} Vol {volume_number}')
                processed += 1
            else:
                print(f'❌ No description found for {series_name} Vol {volume_number}')
        except Exception as e:
            print(f'⚠️ Error processing {series_name}: {e}')

    print(f'🎯 Processed {processed} descriptions')

if __name__ == '__main__':
    backfill_descriptions()