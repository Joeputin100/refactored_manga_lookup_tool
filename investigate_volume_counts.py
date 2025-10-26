#!/usr/bin/env python3
"""
Investigate why some series show only 1 volume when they should have many
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def investigate_problematic_series():
    """Investigate series that should have more volumes"""
    cache = BigQueryCache()

    print('🔍 Investigating series with incorrect volume counts...')

    # Series that should have more volumes
    problematic_series = ['Assassination Classroom', 'A Polar Bear in Love', 'Berserk']

    for series_name in problematic_series:
        print(f'\n--- {series_name} ---')

        # Get series info
        series_info = cache.get_series_info(series_name)
        if series_info:
            print(f'  Series total_volumes: {series_info.get("total_volumes", "Not found")}')
            print(f'  All series fields: {list(series_info.keys())}')

        # Get actual volumes from volume table
        volume_query = f"""
        SELECT volume_number, book_title, isbn_13, publisher_name
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE series_name = '{series_name}'
        ORDER BY volume_number
        """
        volume_job = cache.client.query(volume_query)
        volumes = [dict(row) for row in volume_job]

        print(f'  Actual volumes in cache: {len(volumes)}')

        if volumes:
            print(f'  Volume details:')
            for vol in volumes:
                print(f'    Volume {vol["volume_number"]}: "{vol["book_title"]}"')
                print(f'      ISBN: {vol.get("isbn_13", "Unknown")}')
                print(f'      Publisher: {vol.get("publisher_name", "Unknown")}')
        else:
            print(f'  ❌ No volumes found in cache!')

def check_volume_data_sources():
    """Check if we're missing volume data from certain sources"""
    cache = BigQueryCache()

    print('\n🔍 Checking volume data sources...')

    # Check which series have volume data
    series_with_volumes_query = """
    SELECT DISTINCT series_name, COUNT(*) as volume_count
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    GROUP BY series_name
    ORDER BY volume_count DESC
    """
    series_job = cache.client.query(series_with_volumes_query)
    series_volumes = [dict(row) for row in series_job]

    print(f'\n📊 Series with volume data:')
    for series in series_volumes:
        print(f'  {series["series_name"]}: {series["volume_count"]} volumes')

def check_volume_api_sources():
    """Check which API sources provided volume data"""
    cache = BigQueryCache()

    print('\n🔍 Checking volume API sources...')

    api_sources_query = """
    SELECT DISTINCT api_source, COUNT(*) as count
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    GROUP BY api_source
    ORDER BY count DESC
    """
    api_job = cache.client.query(api_sources_query)
    api_sources = [dict(row) for row in api_job]

    print(f'\n📊 Volume data by API source:')
    for source in api_sources:
        print(f'  {source["api_source"]}: {source["count"]} volumes')

def check_volume_loading_issue():
    """Check if there's an issue with how volumes are being loaded"""
    cache = BigQueryCache()

    print('\n🔍 Checking volume loading patterns...')

    # Check if volumes are being loaded from multiple sources
    volume_sources_query = """
    SELECT series_name, volume_number, COUNT(*) as sources
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    GROUP BY series_name, volume_number
    HAVING COUNT(*) > 1
    """
    sources_job = cache.client.query(volume_sources_query)
    multi_source_volumes = [dict(row) for row in sources_job]

    if multi_source_volumes:
        print(f'\n📊 Volumes with multiple sources:')
        for vol in multi_source_volumes:
            print(f'  {vol["series_name"]} Volume {vol["volume_number"]}: {vol["sources"]} sources')
    else:
        print(f'\n✅ No volumes with multiple sources found')

if __name__ == "__main__":
    investigate_problematic_series()
    check_volume_data_sources()
    check_volume_api_sources()
    check_volume_loading_issue()