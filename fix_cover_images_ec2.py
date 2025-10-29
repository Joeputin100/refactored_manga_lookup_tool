#!/usr/bin/env python3
"""
EC2 Cover Image Fixing Script

Specifically designed for EC2 environment using the existing BigQuery cache
that works with the compute engine service account.

Strategy:
1. Google Books API (primary)
2. Gemini 2.5 Flash Lite web search (secondary)
3. DeepSeek web search (tertiary)

Removes MangaDex due to placeholder image issues.
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/home/ec2-user/refactored_manga_lookup_tool')

from bigquery_cache import BigQueryCache
from enhanced_cover_fetcher import EnhancedCoverFetcher

def fix_cover_images_ec2():
    cache = BigQueryCache()
    cover_fetcher = EnhancedCoverFetcher()

    print("🖼️  EC2 Cover Image Fixing Started...")
    print("🎯 Strategy: Google Books → Gemini Web Search → DeepSeek Web Search")
    print("⚠️  MangaDex removed due to placeholder image issues")

    if not cache.enabled:
        print("❌ BigQuery cache not available. Cannot proceed.")
        return

    # Get series with missing cover images, prioritize popular series
    query = """
    SELECT series_name
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE cover_image_url IS NULL OR cover_image_url = ''
    ORDER BY
        CASE
            WHEN series_name IN ('One Piece', 'Naruto', 'Attack on Titan', 'Bleach', 'Dragon Ball',
                                'My Hero Academia', 'Demon Slayer', 'Jujutsu Kaisen', 'Chainsaw Man',
                                'Spy x Family', 'Tokyo Revengers', 'Haikyuu', 'Hunter x Hunter') THEN 1
            WHEN total_volumes > 20 THEN 2
            WHEN publisher IS NOT NULL THEN 3
            ELSE 4
        END,
        series_name
    LIMIT 100
    """

    try:
        result = cache.client.query(query)
        series_without_covers = [row['series_name'] for row in result]

        print(f"📋 Found {len(series_without_covers)} series without cover images")
        print(f"🎯 Processing first 100 series (prioritizing popular manga)")

        fixed_count = 0
        failed_count = 0

        for i, series_name in enumerate(series_without_covers, 1):
            print(f"\n📚 [{i}/{len(series_without_covers)}] Processing: {series_name}")

            try:
                # Use enhanced fetcher with multi-source strategy
                cover_url = cover_fetcher.fetch_cover(series_name, 1)

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
                    failed_count += 1

            except Exception as e:
                print(f"❌ Error fixing cover for {series_name}: {e}")
                failed_count += 1

        print(f"\n🎯 Final Results:")
        print(f"   ✅ Fixed: {fixed_count} covers")
        print(f"   ❌ Failed: {failed_count} covers")
        if fixed_count + failed_count > 0:
            print(f"   📊 Success Rate: {fixed_count/(fixed_count+failed_count)*100:.1f}%")

        # Print detailed statistics
        cover_fetcher.print_stats()

        # Calculate remaining work
        remaining_query = """
        SELECT COUNT(*) as remaining
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE cover_image_url IS NULL OR cover_image_url = ''
        """

        remaining_result = cache.client.query(remaining_query)
        for row in remaining_result:
            remaining_count = row['remaining']
            print(f"\n📈 Remaining series without covers: {remaining_count}")

    except Exception as e:
        print(f"❌ Error querying series: {e}")


if __name__ == "__main__":
    import requests
    fix_cover_images_ec2()