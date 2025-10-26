#!/usr/bin/env python3
"""
Fix incorrect volume counts for series with total_volumes = 1
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def fix_incorrect_volume_counts():
    """Fix series with incorrect volume count of 1"""
    try:
        bq = BigQueryCache()

        # First, get all series with volume count = 1
        query = """
        SELECT series_name, total_volumes
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE total_volumes = 1
        ORDER BY series_name
        """

        result = bq.client.query(query).result()

        series_to_fix = []
        for row in result:
            series_to_fix.append(row.series_name)

        print(f'Found {len(series_to_fix)} series with volume count = 1')
        print('=' * 50)

        # Correct volume counts for major series
        volume_corrections = {
            # Major series with known volume counts
            "One Piece": 112,
            "Naruto": 72,
            "Bleach": 74,
            "Attack on Titan": 34,
            "My Hero Academia": 42,
            "Demon Slayer: Kimetsu no Yaiba": 23,
            "Fairy Tail": 63,
            "Haikyuu!": 45,
            "Hunter x Hunter": 38,
            "Tokyo Ghoul": 30,
            "Death Note": 12,
            "Assassination Classroom": 21,
            "Bakuman": 20,
            "Goodnight Punpun": 13,
            "Inuyasha": 56,
            "Ranma 1/2": 38,
            "Nausicaa of the Valley of the Wind": 7,
            "Platinum End": 14,
            "Samurai 8": 5,
            "Inuyashiki": 10,
            "Gigant": 8,
            "Welcome Back Alice": 3,
            "Tokyo Alien Bros": 3,
            "Thunder3": 3,
            "Children of Whales": 23,
            "Centaur": 6,
            "A Polar Bear in Love": 3,
            "Alive": 21,
            "All You Need is Kill": 2,

            # Wikipedia series we already know
            "Golgo 13": 217,
            "Case Closed": 107,
            "Dragon Ball": 42,
            "Slam Dunk": 31,
            "KochiKame: Tokyo Beat Cops": 201,

            # Alternate editions that should have correct counts
            "Attack on Titan: Colossal Edition": 7,
            "Attack on Titan: No Regrets": 2,
            "Attack on Titan: Before the Fall": 17,
            "Boruto: Naruto Next Generation": 20,
            "Boruto: Two Blue Vortex": 4,
            "Spy x Family": 15,
            "Magus of the Library": 8,
            "Crayon Shinchan": 64,
            "Sho-ha Shoten": 11,
            "Otherworldly Izakaya Nobu": 20,
            "Blue Note": 10,
            "Tegami Bachi": 20
        }

        fixed_count = 0
        not_fixed_count = 0

        for series_name in series_to_fix:
            if series_name in volume_corrections:
                correct_volume = volume_corrections[series_name]

                # Update the series with correct volume count
                update_query = f"""
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
                SET total_volumes = {correct_volume}
                WHERE series_name = '{series_name}' AND total_volumes = 1
                """

                try:
                    bq.client.query(update_query).result()
                    print(f"✅ Fixed {series_name}: 1 → {correct_volume}")
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ Failed to fix {series_name}: {e}")
                    not_fixed_count += 1
            else:
                print(f"⚠️  No correction found for: {series_name}")
                not_fixed_count += 1

            # Rate limiting
            time.sleep(0.5)

        print(f"\n📊 Volume Count Fix Complete:")
        print(f"   ✅ Fixed: {fixed_count} series")
        print(f"   ⚠️  Not Fixed: {not_fixed_count} series")
        print(f"   📚 Total Processed: {len(series_to_fix)} series")

    except Exception as e:
        print(f"❌ Error fixing volume counts: {e}")

if __name__ == "__main__":
    fix_incorrect_volume_counts()