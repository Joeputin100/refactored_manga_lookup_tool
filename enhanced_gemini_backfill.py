#!/usr/bin/env python3
"""
Enhanced backfill script using Gemini API for image caching and metadata completion
Leverages manual research findings for difficult series
"""

import sys
import os
import json
import base64
import requests
from typing import Dict, List, Optional
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

class EnhancedGeminiBackfill:
    """Enhanced backfill using Gemini API with image caching capabilities"""

    def __init__(self):
        self.cache = BigQueryCache()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

    def fetch_image_as_base64(self, image_url: str) -> Optional[str]:
        """Fetch image and convert to base64 for storage"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Convert image to base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            return image_data
        except Exception as e:
            print(f"❌ Failed to fetch image from {image_url}: {e}")
            return None

    def query_gemini_for_metadata(self, series_name: str, volume_number: int, image_url: str = None) -> Dict:
        """Query Gemini API for enhanced metadata"""

        # Prepare the prompt
        prompt = f"""
        Provide comprehensive metadata for manga volume {volume_number} of "{series_name}".

        Please provide:
        1. ISBN (if available)
        2. Publisher
        3. Copyright year
        4. Detailed description (2-3 sentences)
        5. MSRP (if available)

        Format as JSON with keys: isbn, publisher, copyright_year, description, msrp
        """

        # Prepare request payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        if image_url:
            image_data = self.fetch_image_as_base64(image_url)
            if image_data:
                payload["contents"][0]["parts"].append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_data
                    }
                })

        try:
            response = requests.post(
                f"{self.base_url}?key={self.gemini_api_key}",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            text_content = result['candidates'][0]['content']['parts'][0]['text']

            # Extract JSON from response
            json_start = text_content.find('{')
            json_end = text_content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text_content[json_start:json_end]
                metadata = json.loads(json_str)
                return metadata
            else:
                print(f"❌ Could not extract JSON from Gemini response")
                return {}

        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return {}

    def update_volume_metadata(self, series_name: str, volume_number: int, metadata: Dict, image_data: str = None):
        """Update volume metadata in BigQuery"""

        # Get current volume info
        volumes = self.cache.get_volumes_for_series(series_name, [volume_number])
        if not volumes or not volumes[0]:
            print(f"❌ Volume {volume_number} not found for {series_name}")
            return

        volume = volumes[0]

        # Prepare update data
        update_data = {}

        if metadata.get('isbn') and not volume.get('isbn'):
            update_data['isbn'] = metadata['isbn']

        if metadata.get('publisher') and not volume.get('publisher'):
            update_data['publisher'] = metadata['publisher']

        if metadata.get('copyright_year') and not volume.get('copyright_year'):
            update_data['copyright_year'] = metadata['copyright_year']

        if metadata.get('description') and not volume.get('description'):
            update_data['description'] = metadata['description']

        if metadata.get('msrp') and not volume.get('msrp'):
            update_data['msrp'] = metadata['msrp']

        # If we have image data, we'll store the URL but note that we can't store the actual image data
        # in the current schema. For now, we'll just use the URL.

        if update_data:
            # Update the volume in cache
            volume_info = {
                'title': volume.get('title', ''),
                'isbn': update_data.get('isbn', volume.get('isbn')),
                'publisher': update_data.get('publisher', volume.get('publisher')),
                'copyright_year': update_data.get('copyright_year', volume.get('copyright_year')),
                'description': update_data.get('description', volume.get('description')),
                'msrp': update_data.get('msrp', volume.get('msrp')),
                'cover_image_url': update_data.get('cover_image_url', volume.get('cover_image_url'))
            }
            self.cache.cache_volume_info(
                series_name=series_name,
                volume_number=volume_number,
                volume_info=volume_info,
                api_source='manual_research'
            )
            print(f"✅ Updated volume {volume_number} of {series_name}")
        else:
            print(f"⚠️ No updates needed for volume {volume_number} of {series_name}")

    def process_difficult_series(self):
        """Process the difficult series with manual research findings"""

        # Manual research findings
        manual_findings = {
            "750 Rider": {
                "description": "750 Rider is a Japanese shōnen manga series written and illustrated by Isami Ishii, published in Weekly Shōnen Champion from 1975 to 1985. The story follows high school student Mitsu Hayakawa and his friends, focusing on their interactions and his love for riding his Honda Dream CB750 FOUR motorcycle. The series was a major success, with over 20 million copies in circulation by 2014.",
                "publisher": "Akita Shoten",
                "copyright_year": "1975"
            },
            "A Certain Magical Index": {
                "description": "A Certain Magical Index is a manga series based on the light novel of the same name, telling the story of Touma Kamijou, a boy in Academy City with a supernatural curse who gets involved with a girl named Index. The manga is written by Kazuma Kamachi and illustrated by Chuya Kogino, and has been adapted into anime series and a film. It has been published by Yen Press in North America and is available in both paperback and digital formats.",
                "publisher": "Yen Press",
                "copyright_year": "2004"
            },
            "Cat's Eye": {
                "description": "Cat's Eye is a popular Japanese manga series created by Tsukasa Hojo, which ran from 1981 to 1985. It tells the story of three sisters who are art thieves by night in their quest to find their missing father. The story centers on the three Kisugi sisters—Rui, Hitomi, and Ai—who operate the 'Cat's Eye' café during the day. By night, they become the infamous phantom art thief 'Cat's Eye,' exclusively stealing works by their long-lost artist father, Michael Heinz.",
                "publisher": "Shueisha",
                "copyright_year": "1981"
            },
            "Chainsaw Man": {
                "description": "Chainsaw Man is a dark fantasy and action manga series written and illustrated by Tatsuki Fujimoto, serialized by Shueisha. The story is known for its blend of brutal violence, dark humor, and deep emotional themes, exploring characters driven by often-simple, yet relatable, desires. The manga is split into two distinct parts: Part 1 (Public Safety Saga) ran in Weekly Shōnen Jump from December 2018 to December 2020, and Part 2 (Academy Saga) began in July 2022 and is currently ongoing.",
                "publisher": "Shueisha",
                "copyright_year": "2018"
            },
            "Don't Call It Mystery": {
                "description": "Don't Call It Mystery (Japanese: ミステリと言う勿れ, Hepburn: Misuteri to Iu Nakare) is a Japanese manga series written and illustrated by Yumi Tamura. The manga is a popular, award-winning psychological mystery known for its dialogue-driven plots and observant protagonist. The story centers on Totonou Kunou, a solitary college student with a distinctive curly hairstyle. Despite his preference for a quiet life, his keen intellect and sharp observational skills constantly draw him into complex mysteries.",
                "publisher": "Shogakukan",
                "copyright_year": "2017"
            }
        }

        print("🚀 Processing Difficult Series with Manual Research Findings")
        print("=" * 60)

        for series_name, findings in manual_findings.items():
            print(f"\n📚 Processing: {series_name}")

            # Get volumes for this series
            volumes = []
            for volume_num in range(1, 11):
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
                print(f"   📖 Processing volume {volume_number}")

                # Prepare metadata update
                metadata = {}

                # Add manual findings
                if findings.get('description') and not volume.get('description'):
                    metadata['description'] = findings['description']

                if findings.get('publisher') and not volume.get('publisher'):
                    metadata['publisher'] = findings['publisher']

                if findings.get('copyright_year') and not volume.get('copyright_year'):
                    metadata['copyright_year'] = findings['copyright_year']

                # Update volume metadata
                self.update_volume_metadata(series_name, volume_number, metadata)

        print("\n✅ Completed processing difficult series")

if __name__ == "__main__":
    backfill = EnhancedGeminiBackfill()
    backfill.process_difficult_series()