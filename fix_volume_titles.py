#!/usr/bin/env python3
"""
Fix volume titles to ensure series name and volume number are included
"""

from bigquery_cache import BigQueryCache

def process_volume_title(title, series_name, series_number):
    """
    Process volume title according to requirements:
    - If volume title doesn't contain series title (case insensitive), prepend it
    - If volume number is not in volume title, append it
    """
    if not title or not series_name:
        return title

    processed_title = title

    # Check if series name is in title (case insensitive)
    if series_name.lower() not in title.lower():
        processed_title = f"{series_name} {title}"

    # Check if volume number is in title
    if series_number and str(series_number) not in processed_title:
        processed_title = f"{processed_title} Volume {series_number}"

    return processed_title

def fix_volume_titles():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return 0

    print("📝 Fixing volume titles...")

    # Get all volumes that need title fixes
    query = '''
    SELECT series_name, volume_number, book_title
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE (
        LOWER(book_title) NOT LIKE LOWER(CONCAT('%', series_name, '%'))
        OR book_title NOT LIKE CONCAT('%', CAST(volume_number AS STRING), '%')
    )
    '''

    try:
        result = cache.client.query(query)
        volumes_to_fix = list(result)
        print(f"📊 Found {len(volumes_to_fix)} volumes needing title fixes")

        updated_count = 0
        for row in volumes_to_fix:
            series_name = row['series_name']
            volume_number = row['volume_number']
            original_title = row['book_title']

            # Process the title
            new_title = process_volume_title(original_title, series_name, volume_number)

            if new_title != original_title:
                # Update the title
                update_query = f'''
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                SET book_title = "{new_title}"
                WHERE series_name = "{series_name}" AND volume_number = {volume_number}
                '''
                cache.client.query(update_query)
                print(f"✅ Updated {series_name} Vol {volume_number}: {original_title} -> {new_title}")
                updated_count += 1

        return updated_count

    except Exception as e:
        print(f"❌ Error fixing volume titles: {e}")
        return 0

if __name__ == "__main__":
    updated_count = fix_volume_titles()
    print(f"\n🎯 Summary: Updated {updated_count} volume titles")