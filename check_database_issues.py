#!/usr/bin/env python3
"""
Check database for missing cover images, descriptions, prices, and unknown authors
"""

from bigquery_cache import BigQueryCache

def main():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return

    print("🔍 Checking Database Issues...")
    print("=" * 50)

    # Check for placeholder cover images
    query = '''
    SELECT series_name, cover_image_url
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE cover_image_url LIKE '%placeholder%' OR cover_image_url LIKE '%mangadex%'
    '''
    result = cache.client.query(query)
    placeholder_covers = list(result)
    print(f'📊 Found {len(placeholder_covers)} series with placeholder/mangadex cover images:')
    for row in placeholder_covers:
        print(f'  - {row["series_name"]}: {row["cover_image_url"]}')

    # Check for unknown authors
    query = '''
    SELECT series_name, authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE series_name IN ("Attack on Titan", "One Piece")
    '''
    result = cache.client.query(query)
    print(f'\n👥 Author status:')
    for row in result:
        authors = row['authors']
        if not authors or 'unknown' in str(authors).lower():
            author_status = '❌ Unknown'
        else:
            author_status = '✅ Known'
        print(f'  - {row["series_name"]}: {author_status} - {authors}')

    # Check Attack on Titan volumes
    query = '''
    SELECT volume_number, book_title, description, msrp_cost
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name = "Attack on Titan" AND volume_number BETWEEN 1 AND 5
    ORDER BY volume_number
    '''
    result = cache.client.query(query)
    aot_volumes = list(result)
    print(f'\n📚 Attack on Titan Volumes 1-5:')
    for row in aot_volumes:
        desc_status = '❌' if not row['description'] else '✅'
        price_status = '❌' if not row['msrp_cost'] else '✅'
        print(f'  Vol {row["volume_number"]}: {desc_status} Desc, {price_status} Price')

    # Check One Piece volumes
    query = '''
    SELECT volume_number, book_title, description, msrp_cost
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name = "One Piece" AND volume_number BETWEEN 1 AND 5
    ORDER BY volume_number
    '''
    result = cache.client.query(query)
    op_volumes = list(result)
    print(f'\n📚 One Piece Volumes 1-5:')
    for row in op_volumes:
        desc_status = '❌' if not row['description'] else '✅'
        price_status = '❌' if not row['msrp_cost'] else '✅'
        print(f'  Vol {row["volume_number"]}: {desc_status} Desc, {price_status} Price')

    # Check volume title issues
    print(f'\n📝 Volume Title Analysis:')

    # Check for volumes where series name not in title
    query = '''
    SELECT series_name, volume_number, book_title
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name IN ("Attack on Titan", "One Piece")
    AND volume_number BETWEEN 1 AND 5
    AND LOWER(book_title) NOT LIKE LOWER(CONCAT('%', series_name, '%'))
    '''
    result = cache.client.query(query)
    missing_series_in_title = list(result)
    print(f'  Volumes missing series name in title: {len(missing_series_in_title)}')
    for row in missing_series_in_title:
        print(f'    - {row["series_name"]} Vol {row["volume_number"]}: {row["book_title"]}')

    # Check for volumes where volume number not in title
    query = '''
    SELECT series_name, volume_number, book_title
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE series_name IN ("Attack on Titan", "One Piece")
    AND volume_number BETWEEN 1 AND 5
    AND book_title NOT LIKE CONCAT('%', CAST(volume_number AS STRING), '%')
    '''
    result = cache.client.query(query)
    missing_volume_in_title = list(result)
    print(f'  Volumes missing volume number in title: {len(missing_volume_in_title)}')
    for row in missing_volume_in_title:
        print(f'    - {row["series_name"]} Vol {row["volume_number"]}: {row["book_title"]}')

if __name__ == "__main__":
    main()