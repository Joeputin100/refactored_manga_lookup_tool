#!/usr/bin/env python3
"""
Simple fix for incorrect volume counts using BigQuery cache API
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def fix_volume_counts_simple():
    """Fix series with incorrect volume count of 1 using cache API"""
    try:
        bq = BigQueryCache()

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

            # Alternate editions
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

        print(f"Fixing volume counts for {len(volume_corrections)} series...")
        print("=" * 50)

        for series_name, correct_volume in volume_corrections.items():
            try:
                # Get current series info
                query = f"""
                SELECT *
                FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
                WHERE series_name = '{series_name}'
                """

                result = bq.client.query(query).result()
                series_data = None
                for row in result:
                    series_data = dict(row)
                    break

                if series_data:
                    # Update the volume count
                    series_data['total_volumes'] = correct_volume

                    # Use the cache API to update
                    bq.cache_series_info(series_name, series_data)
                    print(f"✅ Fixed {series_name}: {series_data.get('total_volumes', 'unknown')} → {correct_volume}")
                    fixed_count += 1
                else:
                    print(f"⚠️  Series not found: {series_name}")
                    not_fixed_count += 1

            except Exception as e:
                print(f"❌ Failed to fix {series_name}: {e}")
                not_fixed_count += 1

            # Rate limiting
            time.sleep(1)

        print(f"\n📊 Volume Count Fix Complete:")
        print(f"   ✅ Fixed: {fixed_count} series")
        print(f"   ⚠️  Not Fixed: {not_fixed_count} series")
        print(f"   📚 Total Processed: {len(volume_corrections)} series")

    except Exception as e:
        print(f"❌ Error fixing volume counts: {e}")

if __name__ == "__main__":
    fix_volume_counts_simple()