#!/usr/bin/env python3
"""
Fix cover image fetching for series cards
"""

from bigquery_cache import BigQueryCache
from mangadex_cover_fetcher import MangaDexCoverFetcher

def fix_cover_images():
    cache = BigQueryCache()
    cover_fetcher = MangaDexCoverFetcher()

    print("🖼️  Fixing cover image URLs...")

    # Get series with missing cover images
    query = """
    SELECT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE cover_image_url IS NULL OR cover_image_url = ''
    """

    try:
        result = cache.client.query(query)
        series_without_covers = [row['series_name'] for row in result]

        print(f"📋 Found {len(series_without_covers)} series without cover images")

        fixed_count = 0

        for series_name in series_without_covers[:20]:  # Limit to first 20
            print(f"🔍 Searching for cover: {series_name}")

            try:
                # Try to get cover from MangaDex
                manga_data = cover_fetcher.search_manga(series_name)
                if manga_data:
                    cover_url = cover_fetcher.get_cover_url(manga_data)
                    if cover_url:
                        # Update the series with new cover URL
                        update_query = f"""
                        UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
                        SET cover_image_url = '{cover_url}'
                        WHERE series_name = '{series_name}'
                        """

                        update_result = cache.client.query(update_query)
                        print(f"✅ Fixed cover for {series_name}")
                        fixed_count += 1
                    else:
                        print(f"❌ No cover found for {series_name}")
                else:
                    print(f"❌ No MangaDex data for {series_name}")

            except Exception as e:
                print(f"❌ Error fixing cover for {series_name}: {e}")

        print(f"🎯 Fixed {fixed_count} cover images")

    except Exception as e:
        print(f"❌ Error querying series: {e}")

if __name__ == "__main__":
    fix_cover_images()