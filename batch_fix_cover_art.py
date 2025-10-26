#!/usr/bin/env python3
"""
Batch fix missing cover art for series
"""

import sys
from bigquery_cache import BigQueryCache
from manga_lookup import GoogleBooksAPI

def batch_fix_cover_art():
    """Batch process missing cover art"""
    cache = BigQueryCache()
    google_books_api = GoogleBooksAPI()

    print("=== Batch Fixing Missing Cover Art ===")

    # Get series with missing cover art
    query = """
    SELECT DISTINCT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE cover_image_url IS NULL OR cover_image_url = ""
    ORDER BY series_name
    """

    result = cache.client.query(query).result()
    series_with_missing_covers = [row['series_name'] for row in result]

    print(f"Found {len(series_with_missing_covers)} series with missing cover art")

    fixed_count = 0

    for series_name in series_with_missing_covers[:20]:  # Process first 20 for now
        print(f"\n🔍 Processing: {series_name}")

        # Try to get cover art for the series
        cover_url = google_books_api.get_series_cover_url(series_name)

        if cover_url:
            print(f"✅ Found cover art for {series_name}")

            # Update all volumes for this series with the cover URL
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            SET cover_image_url = "{cover_url}"
            WHERE series_name = "{series_name}"
            AND (cover_image_url IS NULL OR cover_image_url = "")
            """

            try:
                cache.client.query(update_query).result()
                print(f"✅ Updated cover art for {series_name}")
                fixed_count += 1
            except Exception as e:
                print(f"❌ Failed to update {series_name}: {e}")
        else:
            print(f"❌ Could not find cover art for {series_name}")

    print(f"\n✅ Fixed cover art for {fixed_count} series")

    # Check remaining missing cover art
    result_after = cache.client.query(query).result()
    remaining_count = sum(1 for _ in result_after)
    print(f"Remaining series with missing cover art: {remaining_count}")

if __name__ == "__main__":
    batch_fix_cover_art()