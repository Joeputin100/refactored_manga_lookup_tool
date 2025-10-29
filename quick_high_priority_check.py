#!/usr/bin/env python3
"""
Quick check of high-priority series for missing metadata
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def quick_check():
    """Quick check of high-priority series"""

    high_priority_series = [
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

    cache = BigQueryCache()

    print("🔍 QUICK HIGH-PRIORITY SERIES CHECK")
    print("=" * 50)

    for series_name in high_priority_series:
        print(f"\n📚 {series_name}")

        # Check if series exists
        series_info = cache.get_series_info(series_name)
        if not series_info:
            print(f"   ❌ Series NOT found")
            continue

        # Check first 5 volumes
        volumes = []
        for volume_num in range(1, 6):
            volume_info = cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])

        if not volumes:
            print(f"   ❌ No volumes found")
            continue

        print(f"   ✅ Found {len(volumes)} volumes")

        # Quick metadata check
        missing_fields = []
        for volume in volumes:
            vol_num = volume.get('volume_number', 1)
            if not volume.get('description'):
                missing_fields.append(f"Vol {vol_num}: description")
            if not volume.get('isbn_13'):
                missing_fields.append(f"Vol {vol_num}: ISBN")
            if not volume.get('copyright_year'):
                missing_fields.append(f"Vol {vol_num}: copyright")
            if not volume.get('publisher_name'):
                missing_fields.append(f"Vol {vol_num}: publisher")
            if not volume.get('cover_image_url'):
                missing_fields.append(f"Vol {vol_num}: cover")

        if missing_fields:
            print(f"   ⚠️  Missing fields:")
            for field in missing_fields[:5]:  # Show first 5
                print(f"      - {field}")
            if len(missing_fields) > 5:
                print(f"      ... and {len(missing_fields) - 5} more")
        else:
            print(f"   ✅ All metadata complete for checked volumes")

if __name__ == "__main__":
    quick_check()