#!/usr/bin/env python3
"""
Targeted backfill for high-priority series only
"""

import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

class TargetedHighPriorityBackfill:
    """Targeted backfill for high-priority series"""

    def __init__(self):
        self.cache = BigQueryCache()
        self.high_priority_series = [
            "One Piece",
            "Dragon Ball Z",
            "Tokyo Ghoul",
            "Tokyo Ghoul:re",
            "Bleach",
            "Naruto",
            "Bakuman",
            "Assassination Classroom",
            "Hunter x Hunter"
        ]
        self.series_volumes = {
            "One Piece": 107,
            "Dragon Ball Z": 42,
            "Tokyo Ghoul": 14,
            "Tokyo Ghoul:re": 16,
            "Bleach": 74,
            "Naruto": 72,
            "Bakuman": 20,
            "Assassination Classroom": 21,
            "Hunter x Hunter": 37
        }

    def fetch_and_cache_image(self, image_url: str) -> dict:
        """Fetch image and prepare for binary storage"""
        try:
            import requests
            import base64

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get('content-type', 'image/jpeg')
            image_size = len(response.content)

            if image_size < 1000:
                return {}

            image_data = base64.b64encode(response.content).decode('utf-8')

            return {
                'cover_image_data': image_data,
                'cover_image_mime_type': content_type,
                'cover_image_size': image_size,
                'cover_image_source': 'manual_research'
            }

        except Exception as e:
            print(f"   ❌ Failed to fetch image: {e}")
            return {}

    def get_high_priority_metadata(self, series_name: str) -> dict:
        """Get metadata for high-priority series"""

        metadata_db = {
            "One Piece": {
                "description": "One Piece follows the adventures of Monkey D. Luffy, a young man whose body gained the properties of rubber after unintentionally eating a Devil Fruit. With his diverse crew of pirates, named the Straw Hat Pirates, Luffy explores the Grand Line in search of the world's ultimate treasure known as 'One Piece' in order to become the next Pirate King.",
                "publisher": "Shueisha",
                "copyright_year": "1997"
            },
            "Dragon Ball Z": {
                "description": "Dragon Ball Z continues the adventures of Goku, who, along with his companions, defends the Earth against an assortment of villains ranging from intergalactic space fighters and conquerors, unnaturally powerful androids and nearly indestructible magical creatures.",
                "publisher": "Shueisha",
                "copyright_year": "1984"
            },
            "Tokyo Ghoul": {
                "description": "Tokyo Ghoul is set in an alternate reality where ghouls, creatures that look like normal people but can only survive by eating human flesh, live among the human population in secrecy, hiding their true nature in order to evade pursuit from the authorities.",
                "publisher": "Shueisha",
                "copyright_year": "2011"
            },
            "Tokyo Ghoul:re": {
                "description": "Tokyo Ghoul:re is the sequel to Tokyo Ghoul, continuing the story in a world where humans and ghouls coexist. The series follows Haise Sasaki, an investigator who leads the CCG's special squad, Quinx Squad, as they hunt ghouls while dealing with his own mysterious past.",
                "publisher": "Shueisha",
                "copyright_year": "2014"
            },
            "Bleach": {
                "description": "Bleach follows the adventures of Ichigo Kurosaki, a high school student with the ability to see ghosts, and Rukia Kuchiki, a Soul Reaper who transfers her powers to Ichigo after encountering a particularly powerful evil spirit.",
                "publisher": "Shueisha",
                "copyright_year": "2001"
            },
            "Naruto": {
                "description": "Naruto Uzumaki, a young ninja who seeks recognition from his peers and dreams of becoming the Hokage, the leader of his village. The story is told in two parts – the first set in Naruto's pre-teen years, and the second in his teens.",
                "publisher": "Shueisha",
                "copyright_year": "1999"
            },
            "Bakuman": {
                "description": "Bakuman follows the story of Moritaka Mashiro and Akito Takagi, two ninth-grade boys who wish to become manga artists. Mashiro is an average student, while Takagi is the school's top student and something of a loudmouth.",
                "publisher": "Shueisha",
                "copyright_year": "2008"
            },
            "Assassination Classroom": {
                "description": "Assassination Classroom follows the daily life of an extremely powerful octopus-like being working as a junior high homeroom teacher, and his students dedicated to the task of assassinating him to prevent Earth from being destroyed.",
                "publisher": "Shueisha",
                "copyright_year": "2012"
            },
            "Hunter x Hunter": {
                "description": "Hunter x Hunter follows a young boy named Gon Freecss, who discovers that his father, who he was told was dead, is actually a world-renowned Hunter, a licensed professional who specializes in fantastical pursuits such as locating rare or unidentified animal species.",
                "publisher": "Shueisha",
                "copyright_year": "1998"
            }
        }

        return metadata_db.get(series_name, {})

    def process_series_volumes(self, series_name: str):
        """Process all volumes for a series"""

        print(f"\n📚 Processing: {series_name}")
        print("-" * 40)

        # Get metadata for this series
        metadata = self.get_high_priority_metadata(series_name)
        if not metadata:
            print(f"   ❌ No metadata found for {series_name}")
            return

        # Get expected volume count
        expected_volumes = self.series_volumes.get(series_name, 0)

        # Process each volume
        processed_count = 0
        for volume_num in range(1, expected_volumes + 1):
            print(f"   📖 Volume {volume_num}", end="")

            # Get current volume info
            volumes = self.cache.get_volumes_for_series(series_name, [volume_num])
            if not volumes or not volumes[0]:
                print(" - ❌ Not found")
                continue

            volume = volumes[0]

            # Prepare update data
            update_data = {}

            # Add metadata if missing
            if metadata.get('description') and not volume.get('description'):
                update_data['description'] = metadata['description']

            if metadata.get('publisher') and not volume.get('publisher_name'):
                update_data['publisher_name'] = metadata['publisher']

            if metadata.get('copyright_year') and not volume.get('copyright_year'):
                update_data['copyright_year'] = metadata['copyright_year']

            # Update if we have changes
            if update_data:
                volume_info = {
                    'book_title': volume.get('book_title', ''),
                    'isbn_13': volume.get('isbn_13'),
                    'publisher_name': update_data.get('publisher_name', volume.get('publisher_name')),
                    'copyright_year': update_data.get('copyright_year', volume.get('copyright_year')),
                    'description': update_data.get('description', volume.get('description')),
                    'msrp_cost': volume.get('msrp_cost'),
                    'cover_image_url': volume.get('cover_image_url')
                }

                self.cache.cache_volume_info(
                    series_name=series_name,
                    volume_number=volume_num,
                    volume_info=volume_info,
                    api_source='high_priority_backfill'
                )

                print(" - ✅ Updated")
                processed_count += 1
            else:
                print(" - ✅ Complete")

        print(f"   📊 Processed: {processed_count}/{expected_volumes} volumes")

    def run_backfill(self):
        """Run backfill on all high-priority series"""

        print("🚀 TARGETED HIGH-PRIORITY SERIES BACKFILL")
        print("=" * 60)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        total_processed = 0
        total_volumes = sum(self.series_volumes.values())

        for series_name in self.high_priority_series:
            self.process_series_volumes(series_name)
            total_processed += self.series_volumes.get(series_name, 0)

        print(f"\n✅ Backfill completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total volumes processed: {total_processed}")

    def generate_manual_fill_report(self):
        """Generate manual fill report"""

        filename = "targeted_manual_fill_report.txt"

        with open(filename, 'w') as f:
            f.write("TARGETED HIGH-PRIORITY SERIES MANUAL FILL REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write("SERIES STATUS:\n")
            f.write("-" * 40 + "\n")

            for series_name in self.high_priority_series:
                f.write(f"📚 {series_name}\n")

                # Check series status
                series_info = self.cache.get_series_info(series_name)
                if not series_info:
                    f.write("   ❌ SERIES NOT FOUND\n\n")
                    continue

                # Check volumes
                expected = self.series_volumes.get(series_name, 0)
                found_volumes = 0
                for volume_num in range(1, expected + 1):
                    volumes = self.cache.get_volumes_for_series(series_name, [volume_num])
                    if volumes and volumes[0]:
                        found_volumes += 1

                f.write(f"   📊 Volumes: {found_volumes}/{expected}\n")

                # Check metadata completeness for first 3 volumes
                missing_fields = []
                for volume_num in range(1, 4):
                    volumes = self.cache.get_volumes_for_series(series_name, [volume_num])
                    if volumes and volumes[0]:
                        volume = volumes[0]
                        if not volume.get('description'):
                            missing_fields.append(f"Vol {volume_num}: description")
                        if not volume.get('isbn_13'):
                            missing_fields.append(f"Vol {volume_num}: ISBN")
                        if not volume.get('cover_image_url'):
                            missing_fields.append(f"Vol {volume_num}: cover")

                if missing_fields:
                    f.write("   ⚠️  Missing fields:\n")
                    for field in missing_fields:
                        f.write(f"      - {field}\n")
                else:
                    f.write("   ✅ Metadata complete\n")

                f.write("\n")

            f.write("\nPRIORITY ACTIONS:\n")
            f.write("=" * 40 + "\n")
            f.write("1. Import missing series (Tokyo Ghoul:re)\n")
            f.write("2. Add missing cover images\n")
            f.write("3. Fill missing ISBNs and descriptions\n")
            f.write("4. Verify all volumes exist for each series\n")

        print(f"✅ Manual fill report saved to: {filename}")

if __name__ == "__main__":
    backfill = TargetedHighPriorityBackfill()

    # Run backfill
    backfill.run_backfill()

    # Generate report
    backfill.generate_manual_fill_report()

    print("\n🎯 TARGETED BACKFILL COMPLETE")