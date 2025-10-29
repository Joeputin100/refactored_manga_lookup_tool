#!/usr/bin/env python3
"""Backfill missing metadata using Vertex AI API"""

from bigquery_cache import BigQueryCache
from manga_lookup import VertexAIAPI
import time

def backfill_metadata():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return

    print('🔍 Finding volumes with missing metadata...')

    # Query for volumes missing any metadata
    query = '''
    SELECT series_name, volume_number, book_title
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE description IS NULL OR description = ''
       OR isbn_13 IS NULL OR isbn_13 = ''
       OR copyright_year IS NULL
       OR publisher_name IS NULL OR publisher_name = ''
    LIMIT 20  # Process in batches
    '''

    job = cache.client.query(query)
    volumes = list(job.result())

    print(f'📚 Found {len(volumes)} volumes with missing metadata')

    vertex_api = VertexAIAPI()
    processed = 0

    for vol in volumes:
        series_name = vol['series_name']
        volume_number = vol['volume_number']

        print(f'🔍 Processing: {series_name} Vol {volume_number}')

        # Try to get comprehensive metadata from Vertex AI
        try:
            result = vertex_api.get_book_info(series_name, volume_number)

            if result:
                updates = []
                params = []

                # Build update query dynamically based on what we found
                if 'description' in result and result['description']:
                    updates.append('description = @description')
                    params.append({'name': 'description', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': result['description']}})

                if 'isbn_13' in result and result['isbn_13']:
                    updates.append('isbn_13 = @isbn_13')
                    params.append({'name': 'isbn_13', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': result['isbn_13']}})

                if 'copyright_year' in result and result['copyright_year']:
                    updates.append('copyright_year = @copyright_year')
                    params.append({'name': 'copyright_year', 'parameterType': {'type': 'INT64'}, 'parameterValue': {'value': result['copyright_year']}})

                if 'publisher_name' in result and result['publisher_name']:
                    updates.append('publisher_name = @publisher_name')
                    params.append({'name': 'publisher_name', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': result['publisher_name']}})

                if updates:
                    update_query = f'''
                    UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                    SET {', '.join(updates)}
                    WHERE series_name = @series_name AND volume_number = @volume_number
                    '''

                    params.extend([
                        {'name': 'series_name', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': series_name}},
                        {'name': 'volume_number', 'parameterType': {'type': 'INT64'}, 'parameterValue': {'value': volume_number}}
                    ])

                    job_config = {
                        'query': {
                            'parameterMode': 'NAMED',
                            'queryParameters': params
                        }
                    }

                    update_job = cache.client.query(update_query, job_config=job_config)
                    update_job.result()  # Wait for completion

                    print(f'✅ Updated metadata for {series_name} Vol {volume_number}')
                    processed += 1
                else:
                    print(f'❌ No metadata found for {series_name} Vol {volume_number}')
            else:
                print(f'❌ No result from Vertex AI for {series_name} Vol {volume_number}')

        except Exception as e:
            print(f'⚠️ Error processing {series_name}: {e}')

        # Add small delay to avoid rate limiting
        time.sleep(2)

    print(f'🎯 Processed {processed} volumes')

if __name__ == '__main__':
    backfill_metadata()