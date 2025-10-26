#!/usr/bin/env python3
from bigquery_cache import BigQueryCache
from mangadex_cover_fetcher import MangaDexCoverFetcher
import time

# Initialize APIs
cache = BigQueryCache()
cover_fetcher = MangaDexCoverFetcher()

# Additional series to add
additional_series = [
    {'title': 'Black Jack', 'author': 'Osamu Tezuka', 'publisher': 'Akita Shoten', 'volumes': 25, 'copies_sold': 176000000},
    {'title': 'Bleach', 'author': 'Tite Kubo', 'publisher': 'Shueisha', 'volumes': 74, 'copies_sold': 130000000},
    {'title': "JoJo's Bizarre Adventure", 'author': 'Hirohiko Araki', 'publisher': 'Shueisha', 'volumes': 131, 'copies_sold': 120000000},
    {'title': 'Astro Boy', 'author': 'Osamu Tezuka', 'publisher': 'Kobunsha', 'volumes': 23, 'copies_sold': 100000000},
    {'title': 'Fist of the North Star', 'author': 'Buronson', 'publisher': 'Shueisha', 'volumes': 27, 'copies_sold': 100000000},
    {'title': 'Oishinbo', 'author': 'Tetsu Kariya', 'publisher': 'Shogakukan', 'volumes': 111, 'copies_sold': 135000000},
    {'title': 'Hunter × Hunter', 'author': 'Yoshihiro Togashi', 'publisher': 'Shueisha', 'volumes': 37, 'copies_sold': 84000000},
    {'title': 'Fullmetal Alchemist', 'author': 'Hiromu Arakawa', 'publisher': 'Square Enix', 'volumes': 27, 'copies_sold': 80000000},
    {'title': 'My Hero Academia', 'author': 'Kohei Horikoshi', 'publisher': 'Shueisha', 'volumes': 40, 'copies_sold': 85000000},
    {'title': 'Attack on Titan', 'author': 'Hajime Isayama', 'publisher': 'Kodansha', 'volumes': 34, 'copies_sold': 120000000},
    {'title': 'Doraemon', 'author': 'Fujiko F. Fujio', 'publisher': 'Shogakukan', 'volumes': 45, 'copies_sold': 170000000},
    {'title': 'Crayon Shin-chan', 'author': 'Yoshito Usui', 'publisher': 'Futabasha', 'volumes': 50, 'copies_sold': 148000000},
    {'title': 'Hajime no Ippo', 'author': 'George Morikawa', 'publisher': 'Kodansha', 'volumes': 138, 'copies_sold': 100000000},
    {'title': 'Kingdom', 'author': 'Yasuhisa Hara', 'publisher': 'Shueisha', 'volumes': 70, 'copies_sold': 100000000},
    {'title': 'The Prince of Tennis', 'author': 'Takeshi Konomi', 'publisher': 'Shueisha', 'volumes': 42, 'copies_sold': 60000000},
    {'title': 'Nana', 'author': 'Ai Yazawa', 'publisher': 'Shueisha', 'volumes': 21, 'copies_sold': 50000000},
    {'title': 'Fairy Tail', 'author': 'Hiro Mashima', 'publisher': 'Kodansha', 'volumes': 63, 'copies_sold': 72000000},
    {'title': 'Death Note', 'author': 'Tsugumi Ohba', 'publisher': 'Shueisha', 'volumes': 12, 'copies_sold': 30000000},
    {'title': 'Tokyo Ghoul', 'author': 'Sui Ishida', 'publisher': 'Shueisha', 'volumes': 14, 'copies_sold': 47000000},
    {'title': 'One-Punch Man', 'author': 'ONE', 'publisher': 'Shueisha', 'volumes': 28, 'copies_sold': 30000000},
    {'title': 'Mob Psycho 100', 'author': 'ONE', 'publisher': 'Shogakukan', 'volumes': 16, 'copies_sold': 30000000},
    {'title': 'Haikyuu!!', 'author': 'Haruichi Furudate', 'publisher': 'Shueisha', 'volumes': 45, 'copies_sold': 60000000}
]

print('🎯 Adding additional best-selling manga series')
print('=' * 50)

added_count = 0
skipped_count = 0

for series in additional_series:
    title = series['title']

    # Check if already exists
    if cache.get_series_info(title):
        print(f'Skipping {title} - already in cache')
        skipped_count += 1
        continue

    # Get cover image
    cover_url = None
    if cover_fetcher:
        manga_data = cover_fetcher.search_manga(title)
        if manga_data:
            cover_url = cover_fetcher.get_cover_url(manga_data)

    # Prepare series data
    series_info = {
        'corrected_series_name': title,
        'authors': [series['author']],
        'total_volumes': series['volumes'],
        'summary': f'Best-selling manga series with {series["copies_sold"]:,} copies sold',
        'spinoff_series': [],
        'alternate_editions': [],
        'cover_image_url': cover_url,
        'genres': ['Manga'],
        'publisher': series['publisher'],
        'status': 'Completed',
        'alternative_titles': [],
        'adaptations': []
    }

    # Add to cache
    cache.cache_series_info(title, series_info, api_source='wikipedia')
    print(f'Added {title} to cache')
    added_count += 1

    # Rate limiting
    time.sleep(2)

print(f'\nImport Complete:')
print(f'   Added: {added_count} new series')
print(f'   Skipped: {skipped_count} existing series')
print(f'   Total in cache: {added_count + skipped_count} series')