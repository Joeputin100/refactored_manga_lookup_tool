#!/usr/bin/env python3
"""
Load missing volumes for series that should have more volumes - CORRECTED VERSION
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import VertexAIAPI, ProjectState
from bigquery_cache import BigQueryCache

def load_missing_volumes():
    """Load missing volumes for series that should have more volumes"""
    api = VertexAIAPI()
    cache = BigQueryCache()
    project_state = ProjectState()

    print('🚀 Loading missing volumes...')

    # Focus on the most problematic series first
    series_to_load = [
        ('Assassination Classroom', 21),
        ('A Polar Bear in Love', 5),
        ('Berserk', 41),
        ('Attack on Titan', 34),
        ('One Piece', 105),
        ('Tokyo Ghoul', 14),
        ('Tokyo Ghoul: re', 16),
        ('Bakuman', 20),
        ('Hikaru no Go', 23),
        ('Tegami Bachi', 20),
        ('Naruto', 72),
        ('Boruto: Naruto Next Generation', 20),
        ('Dragon Ball Z', 26),
        ('Flowers of Evil', 11),
        ('Goodnight Punpun', 13),
        ('Happiness', 10),
        ('Tokyo Revengers', 31),
        ('To Your Eternity', 20),
        ('Haikyuu!', 45),
        ('Fairy Tail', 63),
        ('Cells at Work', 6),
        ('Akira', 6),
        ('Gigant', 10),
        ('Inuyasha', 56),
        ('Inuyashiki', 10),
        ('Gantz', 37),
        ('Alive', 21),
        ('Orange', 5),
        ('Welcome Back Alice', 10),
        ('Barefoot Gen', 10),
        ('Platinum End', 14),
        ('Death Note', 12),
        ('Magus of the Library', 7),
        ('Spy x Family', 12),
        ('Hunter x Hunter', 36),
        ('Samurai 8', 5),
        ('Thunder3', 10),
        ('Tokyo Alien Bros.', 8),
        ('Centaur', 6),
        ('Blue Note', 4),
        ('Children of Whales', 23),
        ('Bleach', 74),
        ('Crayon Shinchan', 50),
        ('Sho-ha Shoten', 8),
        ('O Parts Hunter', 19),
    ]

    print(f'📊 Found {len(series_to_load)} series to process')

    loaded_count = 0
    error_count = 0

    # Process only the first few series to test
    test_series = series_to_load[:5]  # Just test with first 5 series

    for series_name, total_volumes in test_series:
        try:
            print(f'\n📚 Processing: {series_name} ({total_volumes} volumes)')

            # Check how many volumes we already have
            existing_volumes_query = f"""
            SELECT COUNT(*) as count
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = '{series_name}'
            """
            existing_job = cache.client.query(existing_volumes_query)
            existing_count = list(existing_job)[0]['count']

            print(f'  📊 Already have {existing_count} volumes')

            if existing_count >= total_volumes:
                print(f'  ✅ Already have all volumes')
                continue

            # Load missing volumes
            volumes_to_load = total_volumes - existing_count
            print(f'  🔄 Loading {volumes_to_load} missing volumes...')

            # Load volumes using Vertex AI API
            for volume_num in range(1, total_volumes + 1):
                try:
                    # Check if this volume already exists
                    volume_check_query = f"""
                    SELECT COUNT(*) as count
                    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                    WHERE series_name = '{series_name}' AND volume_number = {volume_num}
                    """
                    volume_check_job = cache.client.query(volume_check_query)
                    volume_exists = list(volume_check_job)[0]['count'] > 0

                    if volume_exists:
                        print(f'    Volume {volume_num}: Already exists')
                        continue

                    print(f'    Volume {volume_num}: Loading...')

                    # Use Vertex AI to get volume info
                    book_info = api.get_book_info(
                        series_name=series_name,
                        volume_number=volume_num,
                        project_state=project_state
                    )

                    if book_info:
                        # Cache the volume info
                        cache.cache_volume_info(book_info)
                        print(f'    Volume {volume_num}: ✅ Loaded successfully')
                        loaded_count += 1

                        # Add small delay to avoid rate limiting
                        time.sleep(2)

                    else:
                        print(f'    Volume {volume_num}: ❌ Failed to load')
                        error_count += 1

                except Exception as e:
                    print(f'    Volume {volume_num}: ❌ Error - {e}')
                    error_count += 1

        except Exception as e:
            print(f'❌ Error processing {series_name}: {e}')
            error_count += 1

    print(f'\n🎯 Volume loading complete:')
    print(f'   ✅ Successfully loaded: {loaded_count} volumes')
    print(f'   ❌ Errors: {error_count}')

if __name__ == "__main__":
    load_missing_volumes()