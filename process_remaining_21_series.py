#!/usr/bin/env python3
"""
Process the remaining 21 difficult series using enhanced cover fetcher with web search
"""

from bigquery_cache import BigQueryCache
from enhanced_cover_fetcher_with_websearch import EnhancedCoverFetcherWithWebSearch

def process_remaining_series():
    cache = BigQueryCache()
    cover_fetcher = EnhancedCoverFetcherWithWebSearch()

    print("🖼️  Processing Remaining 21 Difficult Series...")
    print("🎯 Strategy: Google Books → Gemini Web Search → DeepSeek Web Search")

    if not cache.enabled:
        print("❌ BigQuery cache not available. Cannot proceed.")
        return

    # The 21 remaining series (from our query)
    remaining_series = [
        "750 Rider",
        "A Certain Magical Index",
        "Cat's Eye",
        "Chainsaw Man",
        "Don't Call It Mystery",
        "Fisherman Sanpei",
        "Frieren: Beyond Journey's End",
        "Goodnight Punpun",
        "JoJo's Bizarre Adventure",
        "Kuroko's Basketball",
        "Oishinbo",
        "Salary Man Kintaro",
        "Shizukanaru Don – Yakuza Side Story",
        "Shonan Bakusozoku",
        "Shōnen Ashibe",
        "The Silent Service",
        "Tokyo Daigaku Monogatari",
        "Tsuribaka Nisshi"
    ]

    print(f"📋 Processing {len(remaining_series)} difficult series")

    fixed_count = 0
    failed_count = 0

    for i, series_name in enumerate(remaining_series, 1):
        print(f"\n📚 [{i}/{len(remaining_series)}] Processing: {series_name}")

        try:
            # Use enhanced fetcher with multi-source web search strategy
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
                print(f"   📸 Cover URL: {cover_url}")
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


if __name__ == "__main__":
    process_remaining_series()