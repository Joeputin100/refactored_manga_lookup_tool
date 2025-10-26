#!/usr/bin/env python3
"""
Fix volume issues:
- Remove duplicate volume entries
- Fix volume count display
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def find_duplicate_volumes():
    """Find and analyze duplicate volume entries"""
    cache = BigQueryCache()

    print('🔍 Finding duplicate volume entries...')

    # Get all series with volume data
    series_query = """
    SELECT DISTINCT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    ORDER BY series_name
    """
    series_job = cache.client.query(series_query)
    series_list = [row['series_name'] for row in series_job]

    print(f'📊 Found {len(series_list)} series with volume data')

    duplicate_series = []

    for series_name in series_list:
        # Get volumes for this series
        volume_query = f"""
        SELECT volume_number, book_title, COUNT(*) as count
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE series_name = '{series_name}'
        GROUP BY volume_number, book_title
        HAVING COUNT(*) > 1
        """
        volume_job = cache.client.query(volume_query)
        duplicates = [dict(row) for row in volume_job]

        if duplicates:
            print(f'\n📚 {series_name} has {len(duplicates)} duplicate volume entries:')
            for dup in duplicates:
                print(f'  Volume {dup["volume_number"]}: "{dup["book_title"]}" ({dup["count"]} entries)')
            duplicate_series.append(series_name)

    return duplicate_series

def remove_duplicate_volumes():
    """Remove duplicate volume entries"""
    cache = BigQueryCache()

    print('\n🔄 Removing duplicate volume entries...')

    # Strategy: Keep the most recent entry for each volume
    dedupe_query = """
    CREATE OR REPLACE TABLE `static-webbing-461904-c4.manga_lookup_cache.volume_info_clean` AS
    SELECT * EXCEPT(row_num)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY series_name, volume_number, book_title
                   ORDER BY last_updated DESC
               ) as row_num
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    )
    WHERE row_num = 1
    """

    try:
        dedupe_job = cache.client.query(dedupe_query)
        dedupe_job.result()
        print('✅ Created clean volume table without duplicates')

        # Count records in both tables
        count_original = cache.client.query("""
            SELECT COUNT(*) as count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        """).result()
        original_count = list(count_original)[0]['count']

        count_clean = cache.client.query("""
            SELECT COUNT(*) as count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info_clean`
        """).result()
        clean_count = list(count_clean)[0]['count']

        print(f'📊 Original table: {original_count} volumes')
        print(f'📊 Clean table: {clean_count} volumes')
        print(f'🗑️  Removed {original_count - clean_count} duplicate entries')

        # Replace the original table with the clean one
        replace_query = """
        DROP TABLE `static-webbing-461904-c4.manga_lookup_cache.volume_info`;
        CREATE TABLE `static-webbing-461904-c4.manga_lookup_cache.volume_info` AS
        SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info_clean`;
        DROP TABLE `static-webbing-461904-c4.manga_lookup_cache.volume_info_clean`;
        """

        replace_job = cache.client.query(replace_query)
        replace_job.result()
        print('✅ Replaced original volume table with deduplicated version')

    except Exception as e:
        print(f'❌ Error removing duplicates: {e}')

def fix_volume_counts():
    """Fix volume count display in series info"""
    cache = BigQueryCache()

    print('\n🔧 Fixing volume counts in series info...')

    # Get all series
    series_query = """
    SELECT DISTINCT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    ORDER BY series_name
    """
    series_job = cache.client.query(series_query)
    series_list = [row['series_name'] for row in series_job]

    print(f'📊 Found {len(series_list)} series to update')

    updated_count = 0

    for series_name in series_list:
        try:
            # Count actual volumes
            volume_query = f"""
            SELECT COUNT(*) as volume_count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """
            volume_job = cache.client.query(volume_query)
            volume_count = list(volume_job)[0]['volume_count']

            # Update series info with correct volume count
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
            SET total_volumes = {volume_count}
            WHERE series_name = '{series_name}'
            """
            update_job = cache.client.query(update_query)
            update_job.result()

            print(f'✅ {series_name}: {volume_count} volumes')
            updated_count += 1

        except Exception as e:
            print(f'❌ {series_name}: Error - {e}')

    print(f'\n🎯 Volume count update complete: {updated_count}/{len(series_list)} series updated')

def debug_volume_counts():
    """Debug volume count issues for specific series"""
    cache = BigQueryCache()

    print('\n🔍 Debugging volume counts for problematic series...')

    test_series = ['Assassination Classroom', 'A Polar Bear in Love', 'Berserk']

    for series_name in test_series:
        print(f'\n--- {series_name} ---')

        # Get series info
        series_info = cache.get_series_info(series_name)
        if series_info:
            print(f'  Series total_volumes: {series_info.get("total_volumes", "Not found")}')

            # Get actual volumes
            volume_query = f"""
            SELECT COUNT(*) as volume_count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """
            volume_job = cache.client.query(volume_query)
            volume_count = list(volume_job)[0]['volume_count']
            print(f'  Actual volumes in cache: {volume_count}')

            # List all volumes
            volumes_query = f"""
            SELECT volume_number, book_title
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            ORDER BY volume_number
            """
            volumes_job = cache.client.query(volumes_query)
            volumes = [dict(row) for row in volumes_job]

            print(f'  Volume details:')
            for vol in volumes:
                print(f'    Volume {vol["volume_number"]}: "{vol["book_title"]}"')

if __name__ == "__main__":
    # First, debug to see what we're dealing with
    duplicate_series = find_duplicate_volumes()

    if duplicate_series:
        remove_duplicate_volumes()
    else:
        print('\n✅ No duplicate volumes found!')

    # Fix volume counts
    fix_volume_counts()

    # Debug the results
    debug_volume_counts()