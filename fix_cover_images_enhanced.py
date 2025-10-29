#!/usr/bin/env python3
"""
Enhanced Cover Image Fixing Script

Uses the new multi-source strategy:
1. Google Books API (primary)
2. Gemini 2.5 Flash Lite web search (secondary)
3. DeepSeek web search (tertiary)

Removes MangaDex due to placeholder image issues.
"""

from bigquery_cache import BigQueryCache
from enhanced_cover_fetcher import EnhancedCoverFetcher

def fix_cover_images_enhanced():
    cache = BigQueryCache()
    cover_fetcher = EnhancedCoverFetcher()

    print("🖼️  Enhanced Cover Image Fixing Started...")
    print("🎯 Strategy: Google Books → Gemini Web Search → DeepSeek Web Search")
    print("⚠️  MangaDex removed due to placeholder image issues")

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


def validate_existing_covers():
    """Validate that existing cover URLs are still accessible"""
    cache = BigQueryCache()

    print("🔍 Validating existing cover URLs...")

    query = """
    SELECT series_name, cover_image_url
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE cover_image_url IS NOT NULL AND cover_image_url != ''
    LIMIT 50
    """

    try:
        result = cache.client.query(query)

        broken_count = 0
        total_checked = 0

        for row in result:
            total_checked += 1
            series_name = row['series_name']
            cover_url = row['cover_image_url']

            # Quick validation
            try:
                response = requests.head(cover_url, timeout=5, allow_redirects=True)
                if response.status_code != 200:
                    print(f"❌ Broken cover for {series_name}: {cover_url}")
                    broken_count += 1
            except Exception:
                print(f"❌ Inaccessible cover for {series_name}: {cover_url}")
                broken_count += 1

        print(f"\n📊 Cover Validation Results:")
        print(f"   ✅ Checked: {total_checked} covers")
        print(f"   ❌ Broken: {broken_count} covers")
        print(f"   📈 Health Rate: {(total_checked-broken_count)/total_checked*100:.1f}%")

    except Exception as e:
        print(f"❌ Error validating covers: {e}")


if __name__ == "__main__":
    import requests
    fix_cover_images_enhanced()

    # Optional: Validate existing covers
    # validate_existing_covers()