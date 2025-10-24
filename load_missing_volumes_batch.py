#!/usr/bin/env python3
"""
Load missing volumes for all series using batch processing for efficiency
"""
import sys
import os
import time
import concurrent.futures
from typing import List, Tuple

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import DeepSeekAPI, VertexAIAPI, ProjectState
from bigquery_cache import BigQueryCache

def load_volume_batch(series_name: str, volume_numbers: List[int]) -> Tuple[int, int]:
    """Load a batch of volumes for a series - prioritize DeepSeek with Vertex AI fallback"""
    # Initialize APIs
    deepseek_api = None
    vertex_api = None

    try:
        deepseek_api = DeepSeekAPI()
        print(f'  ✅ DeepSeek API initialized')
    except Exception as e:
        print(f'  ❌ DeepSeek API initialization failed: {e}')

    try:
        vertex_api = VertexAIAPI()
        print(f'  ✅ Vertex AI API initialized')
    except Exception as e:
        print(f'  ❌ Vertex AI API initialization failed: {e}')

    if not deepseek_api and not vertex_api:
        print(f'  ❌ No APIs available')
        return 0, len(volume_numbers)

    cache = BigQueryCache()
    project_state = ProjectState()

    loaded = 0
    errors = 0

    for volume_num in volume_numbers:
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
                print(f'  Volume {volume_num}: Already exists')
                continue

            print(f'  Volume {volume_num}: Loading...')

            # Try DeepSeek API first (priority)
            book_info = None
            if deepseek_api:
                try:
                    print(f'  Volume {volume_num}: Trying DeepSeek API...')
                    book_info = deepseek_api.get_book_info(
                        series_name=series_name,
                        volume_number=volume_num,
                        project_state=project_state
                    )
                    if book_info:
                        print(f'  Volume {volume_num}: ✅ Loaded via DeepSeek')
                    else:
                        print(f'  Volume {volume_num}: ❌ DeepSeek returned None')
                except Exception as e:
                    print(f'  Volume {volume_num}: ❌ DeepSeek failed - {e}')

            # Fallback to Vertex AI if DeepSeek failed or unavailable
            if not book_info and vertex_api:
                try:
                    book_info = vertex_api.get_book_info(
                        series_name=series_name,
                        volume_number=volume_num,
                        project_state=project_state
                    )
                    if book_info:
                        print(f'  Volume {volume_num}: ✅ Loaded via Vertex AI (fallback)')
                except Exception as e:
                    print(f'  Volume {volume_num}: ❌ Vertex AI failed - {e}')

            if book_info:
                # Cache the volume info
                cache.cache_volume_info(series_name, volume_num, book_info)
                loaded += 1

                # Add small delay to avoid rate limiting
                time.sleep(1)

            else:
                print(f'  Volume {volume_num}: ❌ Failed to load (both APIs)')
                errors += 1

        except Exception as e:
            print(f'  Volume {volume_num}: ❌ Error - {e}')
            errors += 1

    return loaded, errors

def load_missing_volumes_batch():
    """Load missing volumes using batch processing"""
    cache = BigQueryCache()

    print('🚀 Loading missing volumes with batch processing...')

    # All series with their expected volume counts
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

    total_loaded = 0
    total_errors = 0

    # Process series in batches of 3 to avoid overwhelming the API
    batch_size = 3
    for i in range(0, len(series_to_load), batch_size):
        batch = series_to_load[i:i + batch_size]
        print(f'\n--- Processing Batch {i//batch_size + 1} ---')

        for series_name, total_volumes in batch:
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

                # Create list of volume numbers to load
                volumes_needed = []
                for volume_num in range(1, total_volumes + 1):
                    # Check if this volume already exists
                    volume_check_query = f"""
                    SELECT COUNT(*) as count
                    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                    WHERE series_name = '{series_name}' AND volume_number = {volume_num}
                    """
                    volume_check_job = cache.client.query(volume_check_query)
                    volume_exists = list(volume_check_job)[0]['count'] > 0

                    if not volume_exists:
                        volumes_needed.append(volume_num)

                # Load volumes in smaller batches
                volume_batch_size = 5
                for j in range(0, len(volumes_needed), volume_batch_size):
                    volume_batch = volumes_needed[j:j + volume_batch_size]
                    print(f'  Processing volumes {volume_batch[0]}-{volume_batch[-1]}...')

                    loaded, errors = load_volume_batch(series_name, volume_batch)
                    total_loaded += loaded
                    total_errors += errors

                    print(f'  Batch complete: {loaded} loaded, {errors} errors')

                    # Add delay between batches
                    if j + volume_batch_size < len(volumes_needed):
                        print(f'  ⏳ Waiting 5 seconds before next batch...')
                        time.sleep(5)

            except Exception as e:
                print(f'❌ Error processing {series_name}: {e}')
                total_errors += 1

        # Add delay between series batches
        if i + batch_size < len(series_to_load):
            print(f'\n⏳ Waiting 10 seconds before next series batch...')
            time.sleep(10)

    print(f'\n🎯 Volume loading complete:')
    print(f'   ✅ Successfully loaded: {total_loaded} volumes')
    print(f'   ❌ Errors: {total_errors}')

if __name__ == "__main__":
    load_missing_volumes_batch()