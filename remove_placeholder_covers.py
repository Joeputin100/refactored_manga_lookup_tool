#!/usr/bin/env python3
"""
Remove placeholder/mangadex cover images from the database
"""

from bigquery_cache import BigQueryCache

def remove_placeholder_covers():
    cache = BigQueryCache()
    if not cache.enabled:
        print('❌ BigQuery cache not enabled')
        return 0

    print("🗑️ Removing placeholder/mangadex cover images...")

    # Update series with placeholder covers to NULL
    query = '''
    UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
    SET cover_image_url = NULL
    WHERE cover_image_url LIKE '%placeholder%' OR cover_image_url LIKE '%mangadex%'
    '''

    try:
        # First count how many will be affected
        count_query = '''
        SELECT COUNT(*) as affected_count
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE cover_image_url LIKE '%placeholder%' OR cover_image_url LIKE '%mangadex%'
        '''
        count_result = cache.client.query(count_query)
        affected_count = list(count_result)[0]['affected_count']

        if affected_count > 0:
            # Execute the update
            result = cache.client.query(query)
            print(f"✅ Removed placeholder covers from {affected_count} series")
        else:
            print("✅ No placeholder covers found to remove")

        return affected_count
    except Exception as e:
        print(f"❌ Error removing placeholder covers: {e}")
        return 0

if __name__ == "__main__":
    removed_count = remove_placeholder_covers()
    print(f"\n🎯 Summary: Removed {removed_count} placeholder cover images")