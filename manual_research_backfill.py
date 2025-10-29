#!/usr/bin/env python3
"""
Enhanced backfill using manual research method with image caching
Leverages the successful approach of using Google Search AI Mode and Google Image Search
"""

import sys
import os
import json
import base64
import requests
from typing import Dict, List, Optional
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

class ManualResearchBackfill:
    """Enhanced backfill using manual research approach with image caching"""

    def __init__(self):
        self.cache = BigQueryCache()

    def fetch_and_cache_image(self, image_url: str) -> Optional[Dict]:
        """Fetch image and prepare for binary storage in BigQuery"""
        try:
            print(f"   🖼️ Fetching image from: {image_url}")

            # Add headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()

            # Get image info
            content_type = response.headers.get('content-type', 'image/jpeg')
            image_size = len(response.content)

            # Convert image to base64 for BigQuery BYTES storage
            image_data = base64.b64encode(response.content).decode('utf-8')

            print(f"   ✅ Image fetched: {image_size} bytes, type: {content_type}")

            return {
                'cover_image_data': image_data,
                'cover_image_mime_type': content_type,
                'cover_image_size': image_size,
                'cover_image_source': 'manual_research'
            }

        except Exception as e:
            print(f"   ❌ Failed to fetch image: {e}")
            return None

    def get_manual_research_data(self, series_name: str) -> Dict:
        """Get manual research findings for a series"""

        # Manual research findings database
        manual_findings = {
            "750 Rider": {
                "description": "750 Rider is a Japanese shōnen manga series written and illustrated by Isami Ishii, published in Weekly Shōnen Champion from 1975 to 1985. The story follows high school student Mitsu Hayakawa and his friends, focusing on their interactions and his love for riding his Honda Dream CB750 FOUR motorcycle. The series was a major success, with over 20 million copies in circulation by 2014.",
                "cover_image_url": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/750_Rider_Volume_1.jpg/220px-750_Rider_Volume_1.jpg",
                "publisher": "Akita Shoten",
                "copyright_year": "1975"
            },
            "A Certain Magical Index": {
                "description": "A Certain Magical Index is a manga series based on the light novel of the same name, telling the story of Touma Kamijou, a boy in Academy City with a supernatural curse who gets involved with a girl named Index. The manga is written by Kazuma Kamachi and illustrated by Chuya Kogino, and has been adapted into anime series and a film. It has been published by Yen Press in North America and is available in both paperback and digital formats.",
                "cover_image_url": "https://i5.walmartimages.com/seo/A-Certain-Magical-Index-Light-Novel-A-Certain-Magical-Index-Vol-1-Light-Novel-Book-1-Paperback-9780316339124_b64cbfda-0b56-4547-8b16-f02baa436b85.1dc3383d1f525980e1d5da1b9b3c2500.jpeg",
                "publisher": "Yen Press",
                "copyright_year": "2004"
            },
            "Cat's Eye": {
                "description": "Cat's Eye is a popular Japanese manga series created by Tsukasa Hojo, which ran from 1981 to 1985. It tells the story of three sisters who are art thieves by night in their quest to find their missing father. The story centers on the three Kisugi sisters—Rui, Hitomi, and Ai—who operate the 'Cat's Eye' café during the day. By night, they become the infamous phantom art thief 'Cat's Eye,' exclusively stealing works by their long-lost artist father, Michael Heinz.",
                "cover_image_url": "https://m.media-amazon.com/images/I/81V5S6R7J9L._AC_UF1000,1000_QL80_.jpg",
                "publisher": "Shueisha",
                "copyright_year": "1981"
            },
            "Chainsaw Man": {
                "description": "Chainsaw Man is a dark fantasy and action manga series written and illustrated by Tatsuki Fujimoto, serialized by Shueisha. The story is known for its blend of brutal violence, dark humor, and deep emotional themes, exploring characters driven by often-simple, yet relatable, desires. The manga is split into two distinct parts: Part 1 (Public Safety Saga) ran in Weekly Shōnen Jump from December 2018 to December 2020, and Part 2 (Academy Saga) began in July 2022 and is currently ongoing.",
                "cover_image_url": "https://m.media-amazon.com/images/I/81ef7pP4TLL._AC_UF1000,1000_QL80_.jpg",
                "publisher": "Shueisha",
                "copyright_year": "2018"
            },
            "Don't Call It Mystery": {
                "description": "Don't Call It Mystery (Japanese: ミステリと言う勿れ, Hepburn: Misuteri to Iu Nakare) is a Japanese manga series written and illustrated by Yumi Tamura. The manga is a popular, award-winning psychological mystery known for its dialogue-driven plots and observant protagonist. The story centers on Totonou Kunou, a solitary college student with a distinctive curly hairstyle. Despite his preference for a quiet life, his keen intellect and sharp observational skills constantly draw him into complex mysteries.",
                "cover_image_url": "https://m.media-amazon.com/images/I/81Y8N+67WVL._AC_UF1000,1000_QL80_.jpg",
                "publisher": "Shogakukan",
                "copyright_year": "2017"
            }
        }

        return manual_findings.get(series_name, {})

    def update_volume_with_manual_research(self, series_name: str, volume_number: int):
        """Update a volume using manual research findings"""

        print(f"   📖 Processing volume {volume_number}")

        # Get current volume info
        volumes = self.cache.get_volumes_for_series(series_name, [volume_number])
        if not volumes or not volumes[0]:
            print(f"   ❌ Volume {volume_number} not found for {series_name}")
            return

        volume = volumes[0]

        # Get manual research findings
        findings = self.get_manual_research_data(series_name)
        if not findings:
            print(f"   ❌ No manual research data for {series_name}")
            return

        # Prepare update data
        update_data = {}
        image_data = None

        # Add manual findings
        if findings.get('description') and not volume.get('description'):
            update_data['description'] = findings['description']

        if findings.get('publisher') and not volume.get('publisher_name'):
            update_data['publisher_name'] = findings['publisher']

        if findings.get('copyright_year') and not volume.get('copyright_year'):
            update_data['copyright_year'] = findings['copyright_year']

        # Fetch and cache cover image
        if findings.get('cover_image_url') and not volume.get('cover_image_data'):
            image_info = self.fetch_and_cache_image(findings['cover_image_url'])
            if image_info:
                update_data.update(image_info)
                # Also keep the URL for reference
                update_data['cover_image_url'] = findings['cover_image_url']

        if update_data:
            # Update the volume in cache
            volume_info = {
                'book_title': volume.get('book_title', ''),
                'isbn_13': volume.get('isbn_13'),
                'publisher_name': update_data.get('publisher_name', volume.get('publisher_name')),
                'copyright_year': update_data.get('copyright_year', volume.get('copyright_year')),
                'description': update_data.get('description', volume.get('description')),
                'msrp_cost': volume.get('msrp_cost'),
                'cover_image_url': update_data.get('cover_image_url', volume.get('cover_image_url')),
                'cover_image_data': update_data.get('cover_image_data'),
                'cover_image_mime_type': update_data.get('cover_image_mime_type'),
                'cover_image_size': update_data.get('cover_image_size'),
                'cover_image_source': update_data.get('cover_image_source')
            }

            self.cache.cache_volume_info(
                series_name=series_name,
                volume_number=volume_number,
                volume_info=volume_info,
                api_source='manual_research'
            )
            print(f"   ✅ Updated volume {volume_number} with manual research data")
        else:
            print(f"   ⚠️ No updates needed for volume {volume_number}")

    def process_difficult_series(self):
        """Process all difficult series using manual research method"""

        difficult_series = [
            "750 Rider",
            "A Certain Magical Index",
            "Cat's Eye",
            "Chainsaw Man",
            "Don't Call It Mystery"
        ]

        print("🚀 Processing Difficult Series with Manual Research Method")
        print("=" * 60)

        for series_name in difficult_series:
            print(f"\n📚 Processing: {series_name}")

            # Get volumes for this series
            volumes = []
            for volume_num in range(1, 11):  # Check first 10 volumes
                volume_info = self.cache.get_volumes_for_series(series_name, [volume_num])
                if volume_info and volume_info[0]:
                    volumes.append(volume_info[0])

            if not volumes:
                print(f"   ❌ No volumes found for {series_name}")
                continue

            print(f"   📚 Found {len(volumes)} volumes")

            # Process each volume
            for volume in volumes:
                volume_number = volume.get('volume_number', 1)
                self.update_volume_with_manual_research(series_name, volume_number)

        print("\n✅ Completed processing difficult series with manual research method")

    def check_image_storage_status(self):
        """Check which volumes have binary image data stored"""

        print("\n🔍 Checking Image Storage Status")
        print("=" * 40)

        difficult_series = [
            "750 Rider",
            "A Certain Magical Index",
            "Cat's Eye",
            "Chainsaw Man",
            "Don't Call It Mystery"
        ]

        for series_name in difficult_series:
            print(f"\n📚 Series: {series_name}")

            # Get volumes for this series
            volumes = []
            for volume_num in range(1, 11):
                volume_info = self.cache.get_volumes_for_series(series_name, [volume_num])
                if volume_info and volume_info[0]:
                    volumes.append(volume_info[0])

            if not volumes:
                print(f"   ❌ No volumes found")
                continue

            for volume in volumes:
                volume_number = volume.get('volume_number', 1)
                has_image_data = bool(volume.get('cover_image_data'))
                has_image_url = bool(volume.get('cover_image_url'))

                status = "✅ Binary" if has_image_data else "🔗 URL" if has_image_url else "❌ Missing"
                print(f"   Volume {volume_number}: {status}")

if __name__ == "__main__":
    backfill = ManualResearchBackfill()

    # Process the difficult series
    backfill.process_difficult_series()

    # Check the results
    backfill.check_image_storage_status()