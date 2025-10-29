#!/usr/bin/env python3
"""
Comprehensive analysis of ALL volumes for high-priority series
"""

import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def get_series_volume_counts():
    """Get expected volume counts for each series"""
    return {
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

def comprehensive_analysis():
    """Comprehensive analysis of all volumes for all series"""

    cache = BigQueryCache()
    series_volumes = get_series_volume_counts()

    print("🔍 COMPREHENSIVE HIGH-PRIORITY SERIES ANALYSIS")
    print("=" * 70)
    print(f"📅 Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_missing_data = {}
    total_volumes_checked = 0
    total_missing_fields = 0

    for series_name, expected_volumes in series_volumes.items():
        print(f"📚 Series: {series_name}")
        print("-" * 50)

        # Get series info
        series_info = cache.get_series_info(series_name)
        if not series_info:
            print(f"   ❌ Series NOT found in database")
            all_missing_data[series_name] = {"status": "NOT_FOUND", "volumes": 0}
            print()
            continue

        # Get ALL volumes for this series
        volumes = []
        missing_volumes = []

        for volume_num in range(1, expected_volumes + 1):
            volume_info = cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])
            else:
                missing_volumes.append(volume_num)

        total_volumes_checked += len(volumes)

        print(f"   📊 Volumes in database: {len(volumes)}/{expected_volumes}")

        if missing_volumes:
            print(f"   ❌ Missing volumes: {len(missing_volumes)}")
            if len(missing_volumes) <= 10:
                print(f"      Volumes: {', '.join(map(str, missing_volumes))}")
            else:
                print(f"      First 10 missing: {', '.join(map(str, missing_volumes[:10]))}...")

        # Check metadata completeness for existing volumes
        missing_descriptions = []
        missing_isbns = []
        missing_copyright = []
        missing_publishers = []
        missing_covers = []
        missing_msrp = []

        for volume in volumes:
            volume_number = volume.get('volume_number', 1)

            if not volume.get('description'):
                missing_descriptions.append(volume_number)

            if not volume.get('isbn_13'):
                missing_isbns.append(volume_number)

            if not volume.get('copyright_year'):
                missing_copyright.append(volume_number)

            if not volume.get('publisher_name'):
                missing_publishers.append(volume_number)

            if not volume.get('cover_image_url') and not volume.get('cover_image_data'):
                missing_covers.append(volume_number)

            if not volume.get('msrp_cost'):
                missing_msrp.append(volume_number)

        # Calculate missing fields
        series_missing_fields = (
            len(missing_descriptions) +
            len(missing_isbns) +
            len(missing_copyright) +
            len(missing_publishers) +
            len(missing_covers) +
            len(missing_msrp)
        )
        total_missing_fields += series_missing_fields

        # Print summary
        print(f"   📝 Missing descriptions: {len(missing_descriptions)}/{len(volumes)}")
        print(f"   📚 Missing ISBNs: {len(missing_isbns)}/{len(volumes)}")
        print(f"   📅 Missing copyright years: {len(missing_copyright)}/{len(volumes)}")
        print(f"   🏢 Missing publishers: {len(missing_publishers)}/{len(volumes)}")
        print(f"   🖼️ Missing cover images: {len(missing_covers)}/{len(volumes)}")
        print(f"   💰 Missing MSRP: {len(missing_msrp)}/{len(volumes)}")

        # Calculate completion percentage
        if volumes:
            total_fields = len(volumes) * 6  # 6 metadata fields per volume
            completion_rate = ((total_fields - series_missing_fields) / total_fields) * 100
            print(f"   📈 Overall completion: {completion_rate:.1f}%")

        # Store missing data
        all_missing_data[series_name] = {
            "status": "FOUND",
            "volumes_found": len(volumes),
            "volumes_expected": expected_volumes,
            "missing_volumes": missing_volumes,
            "missing_descriptions": missing_descriptions,
            "missing_isbns": missing_isbns,
            "missing_copyright": missing_copyright,
            "missing_publishers": missing_publishers,
            "missing_covers": missing_covers,
            "missing_msrp": missing_msrp,
            "completion_rate": completion_rate if volumes else 0
        }

        print()

    # Overall summary
    print("📊 OVERALL SUMMARY")
    print("=" * 50)
    print(f"📚 Total series analyzed: {len(series_volumes)}")
    print(f"📖 Total volumes checked: {total_volumes_checked}")
    print(f"❌ Total missing fields: {total_missing_fields}")
    print(f"📅 Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return all_missing_data

def generate_manual_fill_file(missing_data):
    """Generate comprehensive manual fill instructions"""

    filename = "comprehensive_manual_fill_instructions.txt"

    with open(filename, 'w') as f:
        f.write("COMPREHENSIVE MANUAL METADATA FILL INSTRUCTIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write("HIGH-PRIORITY SERIES - ALL VOLUMES ANALYSIS\n")
        f.write("=" * 70 + "\n\n")

        for series_name, data in missing_data.items():
            if data['status'] == "NOT_FOUND":
                f.write(f"❌ SERIES NOT FOUND: {series_name}\n")
                f.write("   ACTION: Import series data\n\n")
                continue

            f.write(f"📚 SERIES: {series_name}\n")
            f.write(f"📊 Volumes in database: {data['volumes_found']}/{data['volumes_expected']}\n")
            f.write(f"📈 Completion rate: {data['completion_rate']:.1f}%\n")
            f.write("-" * 50 + "\n")

            # Missing volumes
            if data['missing_volumes']:
                f.write(f"❌ MISSING VOLUMES ({len(data['missing_volumes'])}):\n")
                if len(data['missing_volumes']) <= 20:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_volumes']))}\n")
                else:
                    f.write(f"   First 20 volumes: {', '.join(map(str, data['missing_volumes'][:20]))}...\n")
                f.write("   ACTION: Import missing volumes\n\n")

            # Missing descriptions
            if data['missing_descriptions']:
                f.write(f"📝 MISSING DESCRIPTIONS ({len(data['missing_descriptions'])} volumes):\n")
                if len(data['missing_descriptions']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_descriptions']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_descriptions'][:10]))}...\n")
                f.write("   ACTION: Add 2-3 sentence descriptions\n\n")

            # Missing ISBNs
            if data['missing_isbns']:
                f.write(f"📚 MISSING ISBNs ({len(data['missing_isbns'])} volumes):\n")
                if len(data['missing_isbns']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_isbns']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_isbns'][:10]))}...\n")
                f.write("   ACTION: Look up ISBN-13 numbers\n\n")

            # Missing copyright years
            if data['missing_copyright']:
                f.write(f"📅 MISSING COPYRIGHT YEARS ({len(data['missing_copyright'])} volumes):\n")
                if len(data['missing_copyright']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_copyright']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_copyright'][:10]))}...\n")
                f.write("   ACTION: Find publication/copyright years\n\n")

            # Missing publishers
            if data['missing_publishers']:
                f.write(f"🏢 MISSING PUBLISHERS ({len(data['missing_publishers'])} volumes):\n")
                if len(data['missing_publishers']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_publishers']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_publishers'][:10]))}...\n")
                f.write("   ACTION: Identify publishers\n\n")

            # Missing covers
            if data['missing_covers']:
                f.write(f"🖼️ MISSING COVER IMAGES ({len(data['missing_covers'])} volumes):\n")
                if len(data['missing_covers']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_covers']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_covers'][:10]))}...\n")
                f.write("   ACTION: Find cover image URLs\n\n")

            # Missing MSRP
            if data['missing_msrp']:
                f.write(f"💰 MISSING MSRP ({len(data['missing_msrp'])} volumes):\n")
                if len(data['missing_msrp']) <= 10:
                    f.write(f"   Volumes: {', '.join(map(str, data['missing_msrp']))}\n")
                else:
                    f.write(f"   First 10 volumes: {', '.join(map(str, data['missing_msrp'][:10]))}...\n")
                f.write("   ACTION: Find retail prices\n\n")

            f.write("\n" + "=" * 70 + "\n\n")

        f.write("\nPRIORITY ACTIONS:\n")
        f.write("=" * 40 + "\n")
        f.write("1. Import missing volumes for incomplete series\n")
        f.write("2. Use enhanced backfill scripts for metadata completion\n")
        f.write("3. Focus on series with lowest completion rates first\n")

    print(f"✅ Comprehensive manual fill instructions saved to: {filename}")
    return filename

if __name__ == "__main__":
    print("🔍 Starting Comprehensive High-Priority Series Analysis...\n")

    missing_data = comprehensive_analysis()

    if missing_data:
        filename = generate_manual_fill_file(missing_data)
        print(f"\n📄 Comprehensive analysis complete: {filename}")
    else:
        print("\n❌ No data found for analysis")