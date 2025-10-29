#!/usr/bin/env python3
"""
Check the current status of the difficult series that were manually researched
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def check_series_status():
    """Check the status of specific difficult series"""

    difficult_series = [
        "750 Rider",
        "A Certain Magical Index",
        "Cat's Eye",
        "Chainsaw Man",
        "Don't Call It Mystery"
    ]

    cache = BigQueryCache()

    print("🔍 Checking Status of Difficult Series")
    print("=" * 50)

    for series_name in difficult_series:
        print(f"\n📚 Series: {series_name}")

        # Get series info
        series_info = cache.get_series_info(series_name)
        if series_info:
            print(f"   ✅ Series found in database")
            print(f"   📊 Total volumes: {series_info.get('total_volumes', 'Unknown')}")
        else:
            print(f"   ❌ Series NOT found in database")
            continue

        # Get volumes for this series - try to get first 10 volumes
        volumes = []
        for volume_num in range(1, 11):
            volume_info = cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])

        if volumes:
            print(f"   📚 Volumes in database: {len(volumes)}")

            # Check metadata completeness
            missing_descriptions = 0
            missing_isbns = 0
            missing_copyright = 0
            missing_publishers = 0
            missing_covers = 0

            for volume in volumes:
                if not volume.get('description'):
                    missing_descriptions += 1
                if not volume.get('isbn'):
                    missing_isbns += 1
                if not volume.get('copyright_year'):
                    missing_copyright += 1
                if not volume.get('publisher'):
                    missing_publishers += 1
                if not volume.get('cover_image_url'):
                    missing_covers += 1

            print(f"   📝 Missing descriptions: {missing_descriptions}/{len(volumes)}")
            print(f"   📚 Missing ISBNs: {missing_isbns}/{len(volumes)}")
            print(f"   📅 Missing copyright years: {missing_copyright}/{len(volumes)}")
            print(f"   🏢 Missing publishers: {missing_publishers}/{len(volumes)}")
            print(f"   🖼️ Missing cover images: {missing_covers}/{len(volumes)}")

            # Show sample volume data
            if volumes:
                sample = volumes[0]
                print(f"   📖 Sample volume data:")
                print(f"      - Title: {sample.get('title', 'N/A')}")
                print(f"      - Volume: {sample.get('volume_number', 'N/A')}")
                print(f"      - ISBN: {sample.get('isbn', 'N/A')}")
                print(f"      - Publisher: {sample.get('publisher', 'N/A')}")
                print(f"      - Cover: {'✅' if sample.get('cover_image_url') else '❌'}")
        else:
            print(f"   ❌ No volumes found for this series")

if __name__ == "__main__":
    check_series_status()