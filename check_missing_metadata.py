#!/usr/bin/env python3
"""
Check missing metadata across all volumes in the database
"""

from bigquery_cache import BigQueryCache

def main():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return

    print('🔍 Checking Missing Metadata Across All Volumes...')
    print('=' * 50)

    # Count total volumes
    total_query = '''
    SELECT COUNT(*) as total_volumes
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    '''
    total_result = cache.client.query(total_query)
    total_volumes = list(total_result)[0]['total_volumes']
    print(f'📊 Total volumes in database: {total_volumes}')

    # Check missing descriptions
    desc_query = '''
    SELECT COUNT(*) as missing_descriptions
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE description IS NULL OR description = ''
    '''
    desc_result = cache.client.query(desc_query)
    missing_desc = list(desc_result)[0]['missing_descriptions']
    print(f'📝 Volumes missing descriptions: {missing_desc} ({missing_desc/total_volumes*100:.1f}%)')

    # Check missing MSRP
    msrp_query = '''
    SELECT COUNT(*) as missing_msrp
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE msrp_cost IS NULL OR msrp_cost = 0
    '''
    msrp_result = cache.client.query(msrp_query)
    missing_msrp = list(msrp_result)[0]['missing_msrp']
    print(f'💰 Volumes missing MSRP: {missing_msrp} ({missing_msrp/total_volumes*100:.1f}%)')

    # Check missing ISBNs
    isbn_query = '''
    SELECT COUNT(*) as missing_isbn
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE isbn_13 IS NULL OR isbn_13 = ''
    '''
    isbn_result = cache.client.query(isbn_query)
    missing_isbn = list(isbn_result)[0]['missing_isbn']
    print(f'📚 Volumes missing ISBN: {missing_isbn} ({missing_isbn/total_volumes*100:.1f}%)')

    # Check missing copyright years
    copyright_query = '''
    SELECT COUNT(*) as missing_copyright
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE copyright_year IS NULL OR copyright_year = 0
    '''
    copyright_result = cache.client.query(copyright_query)
    missing_copyright = list(copyright_result)[0]['missing_copyright']
    print(f'📅 Volumes missing copyright year: {missing_copyright} ({missing_copyright/total_volumes*100:.1f}%)')

    # Check missing publishers
    publisher_query = '''
    SELECT COUNT(*) as missing_publisher
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE publisher_name IS NULL OR publisher_name = ''
    '''
    publisher_result = cache.client.query(publisher_query)
    missing_publisher = list(publisher_result)[0]['missing_publisher']
    print(f'🏢 Volumes missing publisher: {missing_publisher} ({missing_publisher/total_volumes*100:.1f}%)')

    # Check missing cover images
    cover_query = '''
    SELECT COUNT(*) as missing_cover
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE cover_image_url IS NULL OR cover_image_url = ''
    '''
    cover_result = cache.client.query(cover_query)
    missing_cover = list(cover_result)[0]['missing_cover']
    print(f'🖼️ Volumes missing cover images: {missing_cover} ({missing_cover/total_volumes*100:.1f}%)')

    print()
    print('📋 Summary of Missing Metadata:')
    print(f'   - Missing descriptions: {missing_desc}')
    print(f'   - Missing MSRP: {missing_msrp}')
    print(f'   - Missing ISBN: {missing_isbn}')
    print(f'   - Missing copyright year: {missing_copyright}')
    print(f'   - Missing publisher: {missing_publisher}')
    print(f'   - Missing cover images: {missing_cover}')

if __name__ == "__main__":
    main()