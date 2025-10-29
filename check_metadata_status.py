#!/usr/bin/env python3
"""Check current metadata completion status"""

from bigquery_cache import BigQueryCache

def check_metadata_status():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return

    query = '''
    SELECT
        COUNT(*) as total_volumes,
        COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as missing_descriptions,
        COUNT(CASE WHEN isbn_13 IS NULL OR isbn_13 = '' THEN 1 END) as missing_isbns,
        COUNT(CASE WHEN copyright_year IS NULL THEN 1 END) as missing_copyright_years,
        COUNT(CASE WHEN publisher_name IS NULL OR publisher_name = '' THEN 1 END) as missing_publishers,
        COUNT(CASE WHEN cover_image_url IS NULL OR cover_image_url = '' THEN 1 END) as missing_cover_images
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    '''

    job = cache.client.query(query)
    result = list(job.result())[0]

    print(f'📊 Current Metadata Status:')
    print(f'   Total volumes: {result["total_volumes"]}')
    print(f'   Missing descriptions: {result["missing_descriptions"]}')
    print(f'   Missing ISBNs: {result["missing_isbns"]}')
    print(f'   Missing copyright years: {result["missing_copyright_years"]}')
    print(f'   Missing publishers: {result["missing_publishers"]}')
    print(f'   Missing cover images: {result["missing_cover_images"]}')

    # Calculate completion percentages
    total = result["total_volumes"]
    if total > 0:
        print(f'\n📈 Completion Rates:')
        print(f'   Descriptions: {100 - (result["missing_descriptions"] / total * 100):.1f}%')
        print(f'   ISBNs: {100 - (result["missing_isbns"] / total * 100):.1f}%')
        print(f'   Copyright years: {100 - (result["missing_copyright_years"] / total * 100):.1f}%')
        print(f'   Publishers: {100 - (result["missing_publishers"] / total * 100):.1f}%')
        print(f'   Cover images: {100 - (result["missing_cover_images"] / total * 100):.1f}%')

if __name__ == '__main__':
    check_metadata_status()