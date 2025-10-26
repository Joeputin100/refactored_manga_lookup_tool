#!/usr/bin/env python3
"""
Update cached series with comprehensive metadata
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import VertexAIAPI
from bigquery_cache import BigQueryCache

def update_series_comprehensive_data():
    """Update cached series with comprehensive metadata"""
    api = VertexAIAPI()
    cache = BigQueryCache()

    print('🚀 Updating cached series with comprehensive metadata...')

    # Series that need comprehensive data
    series_to_update = [
        'Attack on Titan',
        'Assassination Classroom',
        'A Polar Bear in Love',
        'Berserk',
        'One Piece',
        'Tokyo Ghoul',
        'Tokyo Ghoul: re',
        'Bakuman',
        'Hikaru no Go',
        'Tegami Bachi',
        'Naruto',
        'Boruto: Naruto Next Generation',
        'Dragon Ball Z',
        'Flowers of Evil',
        'Goodnight Punpun',
        'Happiness',
        'Tokyo Revengers',
        'To Your Eternity',
        'Haikyuu!',
        'Fairy Tail',
        'Cells at Work',
        'Akira',
        'Gigant',
        'Inuyasha',
        'Inuyashiki',
        'Gantz',
        'Alive',
        'Orange',
        'Welcome Back Alice',
        'Barefoot Gen',
        'Platinum End',
        'Death Note',
        'Magus of the Library',
        'Spy x Family',
        'Hunter x Hunter',
        'Samurai 8',
        'Thunder3',
        'Tokyo Alien Bros.',
        'Centaur',
        'Blue Note',
        'Children of Whales',
        'Bleach',
        'Crayon Shinchan',
        'Sho-ha Shoten',
        'O Parts Hunter',
    ]

    print(f'📊 Found {len(series_to_update)} series to update')

    updated_count = 0
    error_count = 0

    for series_name in series_to_update:
        try:
            print(f'\n📚 Updating: {series_name}')

            # Get comprehensive series info from Vertex AI
            series_info = api.get_comprehensive_series_info(series_name)

            if series_info:
                # Add the correct volume count from our predefined list
                volume_counts = {
                    'Attack on Titan': 34,
                    'Assassination Classroom': 21,
                    'A Polar Bear in Love': 5,
                    'Berserk': 41,
                    'One Piece': 105,
                    'Tokyo Ghoul': 14,
                    'Tokyo Ghoul: re': 16,
                    'Bakuman': 20,
                    'Hikaru no Go': 23,
                    'Tegami Bachi': 20,
                    'Naruto': 72,
                    'Boruto: Naruto Next Generation': 20,
                    'Dragon Ball Z': 26,
                    'Flowers of Evil': 11,
                    'Goodnight Punpun': 13,
                    'Happiness': 10,
                    'Tokyo Revengers': 31,
                    'To Your Eternity': 20,
                    'Haikyuu!': 45,
                    'Fairy Tail': 63,
                    'Cells at Work': 6,
                    'Akira': 6,
                    'Gigant': 10,
                    'Inuyasha': 56,
                    'Inuyashiki': 10,
                    'Gantz': 37,
                    'Alive': 21,
                    'Orange': 5,
                    'Welcome Back Alice': 10,
                    'Barefoot Gen': 10,
                    'Platinum End': 14,
                    'Death Note': 12,
                    'Magus of the Library': 7,
                    'Spy x Family': 12,
                    'Hunter x Hunter': 36,
                    'Samurai 8': 5,
                    'Thunder3': 10,
                    'Tokyo Alien Bros.': 8,
                    'Centaur': 6,
                    'Blue Note': 4,
                    'Children of Whales': 23,
                    'Bleach': 74,
                    'Crayon Shinchan': 50,
                    'Sho-ha Shoten': 8,
                    'O Parts Hunter': 19,
                }

                # Update with correct volume count
                series_info['extant_volumes'] = volume_counts.get(series_name, series_info.get('extant_volumes', 0))

                # Cache the comprehensive series info
                cache.cache_series_info(series_name, series_info, api_source="comprehensive_update")
                print(f'✅ Updated comprehensive data for: {series_name}')
                print(f'   - Genres: {series_info.get("genres", [])}')
                print(f'   - Publisher: {series_info.get("publisher", "")}')
                print(f'   - Status: {series_info.get("status", "")}')
                print(f'   - Alternative Titles: {series_info.get("alternative_titles", [])}')
                print(f'   - Adaptations: {series_info.get("adaptations", [])}')
                print(f'   - Volumes: {series_info.get("extant_volumes", 0)}')

                updated_count += 1

                # Add delay to avoid rate limiting
                import time
                time.sleep(3)

            else:
                print(f'❌ Failed to get comprehensive data for: {series_name}')
                error_count += 1

        except Exception as e:
            print(f'❌ Error updating {series_name}: {e}')
            error_count += 1

    print(f'\n🎯 Update complete:')
    print(f'   ✅ Successfully updated: {updated_count} series')
    print(f'   ❌ Errors: {error_count}')

if __name__ == "__main__":
    update_series_comprehensive_data()