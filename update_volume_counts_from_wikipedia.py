#!/usr/bin/env python3
"""
Update volume counts from Wikipedia data for cached series
"""

import sys
from bigquery_cache import BigQueryCache
from wikipedia_complete_series_list import WIKIPEDIA_BEST_SELLING_MANGA_SERIES

def update_volume_counts():
    """Update series volume counts from Wikipedia data"""
    cache = BigQueryCache()

    # Wikipedia volume data (you would need to add actual volume counts here)
    # For now, we'll use a placeholder - in a real implementation,
    # this would come from scraping Wikipedia pages
    wikipedia_volume_data = {
        # 100+ million series
        "One Piece": 108,
        "Doraemon": 45,
        "Golgo 13": 203,
        "Case Closed / Detective Conan": 103,
        "Dragon Ball": 42,
        "Naruto": 72,
        "Demon Slayer: Kimetsu no Yaiba": 23,
        "Slam Dunk": 31,
        "KochiKame: Tokyo Beat Cops": 201,
        "Crayon Shin-chan": 50,
        "Attack on Titan": 34,
        "Oishinbo": 111,
        "Bleach": 74,
        "JoJo's Bizarre Adventure": 131,
        "Kingdom": 73,
        "Astro Boy": 23,
        "Baki the Grappler": 143,
        "Fist of the North Star": 27,
        "Hajime no Ippo": 138,
        "Jujutsu Kaisen": 26,
        "The Kindaichi Case Files": 87,
        "My Hero Academia": 39,
        "Touch": 26,

        # 50-99 million series
        "Captain Tsubasa": 37,
        "Sazae-san": 45,
        "Kinnikuman": 83,
        "Hunter × Hunter": 37,
        "Vagabond": 37,
        "Fullmetal Alchemist": 27,
        "Sangokushi": 60,
        "Tokyo Revengers": 31,
        "Gintama": 77,
        "Fairy Tail": 63,
        "Rurouni Kenshin": 28,
        "Berserk": 41,
        "Haikyu!!": 45,
        "Major": 78,
        "Boys Over Flowers": 37,
        "The Prince of Tennis": 42,
        "Nana": 21,
        "Paradise Kiss": 5,
        "Nodame Cantabile": 25,
        "Glass Mask": 49,
        "Basilisk: The Kouga Ninja Scrolls": 5,
        "Miyuki": 12,
        "Maison Ikkoku": 15,
        "Urusei Yatsura": 34,
        "Ranma ½": 38,
        "Inuyasha": 56,
        "Rumic World": 3,

        # Add more as needed
    }

    print("Updating volume counts from Wikipedia data...")

    # Get current cached series
    query = "SELECT DISTINCT series_name FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`"
    result = cache.client.query(query).result()
    cached_series = [row['series_name'] for row in result]

    updated_count = 0

    for series_name in cached_series:
        if series_name in wikipedia_volume_data:
            volume_count = wikipedia_volume_data[series_name]

            # Update the series_info table
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
            SET total_volumes = {volume_count}
            WHERE series_name = "{series_name}"
            """

            try:
                cache.client.query(update_query).result()
                print(f"✅ Updated {series_name}: {volume_count} volumes")
                updated_count += 1
            except Exception as e:
                print(f"❌ Failed to update {series_name}: {e}")

    print(f"\n✅ Updated volume counts for {updated_count} series")

    # Now check how many series still have only 1 volume
    print("\n=== Checking series with only 1 volume after update ===")

    query_single_vol = """
    SELECT series_name, COUNT(*) as volume_count
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    GROUP BY series_name
    HAVING COUNT(*) = 1
    ORDER BY series_name
    """

    result_single = cache.client.query(query_single_vol).result()
    single_volume_series = [(row['series_name'], row['volume_count']) for row in result_single]

    print(f"Series with only 1 volume: {len(single_volume_series)}")
    if single_volume_series:
        print("First 20 series:")
        for series, count in single_volume_series[:20]:
            print(f"  - {series}: {count} volumes")

if __name__ == "__main__":
    update_volume_counts()