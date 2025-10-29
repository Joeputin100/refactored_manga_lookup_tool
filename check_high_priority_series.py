#!/usr/bin/env python3
"""
Check high-priority series for missing metadata gaps
Focus on 100% completion for critical series
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def check_high_priority_series():
    """Check high-priority series for missing metadata"""

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

    print("🔍 HIGH-PRIORITY SERIES METADATA GAP ANALYSIS")
    print("=" * 60)
    print("\n📋 Target: 100% metadata completion for all volumes")
    print("\n")

    all_missing_data = []

    for series_name in high_priority_series:
        print(f"📚 Series: {series_name}")
        print("-" * 40)

        # Get series info
        series_info = cache.get_series_info(series_name)
        if not series_info:
            print(f"   ❌ Series NOT found in database")
            all_missing_data.append(f"{series_name}: SERIES NOT FOUND")
            print()
            continue

        # Get volumes for this series
        volumes = []
        max_volumes_to_check = 200  # High limit for long series
        for volume_num in range(1, max_volumes_to_check + 1):
            volume_info = cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])
            else:
                # Stop when we hit a gap
                break

        if not volumes:
            print(f"   ❌ No volumes found for this series")
            all_missing_data.append(f"{series_name}: NO VOLUMES FOUND")
            print()
            continue

        print(f"   📊 Total volumes in database: {len(volumes)}")

        # Check metadata completeness
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

        # Print summary
        print(f"   📝 Missing descriptions: {len(missing_descriptions)}/{len(volumes)}")
        print(f"   📚 Missing ISBNs: {len(missing_isbns)}/{len(volumes)}")
        print(f"   📅 Missing copyright years: {len(missing_copyright)}/{len(volumes)}")
        print(f"   🏢 Missing publishers: {len(missing_publishers)}/{len(volumes)}")
        print(f"   🖼️ Missing cover images: {len(missing_covers)}/{len(volumes)}")
        print(f"   💰 Missing MSRP: {len(missing_msrp)}/{len(volumes)}")

        # Calculate completion percentage
        total_fields = len(volumes) * 6  # 6 metadata fields per volume
        missing_fields = (
            len(missing_descriptions) +
            len(missing_isbns) +
            len(missing_copyright) +
            len(missing_publishers) +
            len(missing_covers) +
            len(missing_msrp)
        )
        completion_rate = ((total_fields - missing_fields) / total_fields) * 100

        print(f"   📈 Overall completion: {completion_rate:.1f}%")

        # Collect missing data for manual fill file
        if missing_descriptions or missing_isbns or missing_copyright or missing_publishers or missing_covers or missing_msrp:
            series_missing = {
                'series': series_name,
                'total_volumes': len(volumes),
                'missing_descriptions': missing_descriptions,
                'missing_isbns': missing_isbns,
                'missing_copyright': missing_copyright,
                'missing_publishers': missing_publishers,
                'missing_covers': missing_covers,
                'missing_msrp': missing_msrp
            }
            all_missing_data.append(series_missing)

        print()

    return all_missing_data

def generate_manual_fill_file(missing_data):
    """Generate a text file for manual metadata filling"""

    filename = "manual_metadata_fill_instructions.txt"

    with open(filename, 'w') as f:
        f.write("MANUAL METADATA FILL INSTRUCTIONS\n")
        f.write("=" * 50 + "\n\n")
        f.write("HIGH-PRIORITY SERIES REQUIRING 100% COMPLETION\n")
        f.write("=" * 50 + "\n\n")

        for item in missing_data:
            if isinstance(item, str):
                # Series not found
                f.write(f"❌ {item}\n\n")
                continue

            series_name = item['series']
            total_volumes = item['total_volumes']

            f.write(f"📚 SERIES: {series_name}\n")
            f.write(f"📊 Total volumes: {total_volumes}\n")
            f.write("-" * 40 + "\n")

            # Missing descriptions
            if item['missing_descriptions']:
                f.write(f"📝 MISSING DESCRIPTIONS ({len(item['missing_descriptions'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_descriptions']))}\n")
                f.write("   ACTION: Add 2-3 sentence descriptions for each volume\n\n")

            # Missing ISBNs
            if item['missing_isbns']:
                f.write(f"📚 MISSING ISBNs ({len(item['missing_isbns'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_isbns']))}\n")
                f.write("   ACTION: Look up ISBN-13 numbers for each volume\n\n")

            # Missing copyright years
            if item['missing_copyright']:
                f.write(f"📅 MISSING COPYRIGHT YEARS ({len(item['missing_copyright'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_copyright']))}\n")
                f.write("   ACTION: Find publication/copyright years\n\n")

            # Missing publishers
            if item['missing_publishers']:
                f.write(f"🏢 MISSING PUBLISHERS ({len(item['missing_publishers'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_publishers']))}\n")
                f.write("   ACTION: Identify publisher for each volume\n\n")

            # Missing covers
            if item['missing_covers']:
                f.write(f"🖼️ MISSING COVER IMAGES ({len(item['missing_covers'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_covers']))}\n")
                f.write("   ACTION: Find cover image URLs or upload images\n\n")

            # Missing MSRP
            if item['missing_msrp']:
                f.write(f"💰 MISSING MSRP ({len(item['missing_msrp'])} volumes):\n")
                f.write(f"   Volumes: {', '.join(map(str, item['missing_msrp']))}\n")
                f.write("   ACTION: Find retail prices for each volume\n\n")

            f.write("\n" + "=" * 50 + "\n\n")

        f.write("\nINSTRUCTIONS FOR MANUAL FILLING:\n")
        f.write("=" * 40 + "\n")
        f.write("1. Use the enhanced_gemini_backfill.py script for automated filling\n")
        f.write("2. Or use manual_research_backfill.py for manual research method\n")
        f.write("3. For bulk updates, modify the manual_findings dictionary in the scripts\n")
        f.write("4. Run final_enhanced_backfill.py for complete processing\n")
        f.write("5. Check progress with check_difficult_series.py\n")

    print(f"✅ Manual fill instructions saved to: {filename}")
    return filename

if __name__ == "__main__":
    print("🔍 Checking High-Priority Series Metadata Gaps...\n")

    missing_data = check_high_priority_series()

    if missing_data:
        filename = generate_manual_fill_file(missing_data)
        print(f"\n📄 Manual fill file created: {filename}")
        print("\n🎯 NEXT STEPS:")
        print("1. Review the manual fill instructions file")
        print("2. Use the backfill scripts to fill missing metadata")
        print("3. Aim for 100% completion on high-priority series")
    else:
        print("\n🎉 All high-priority series have 100% metadata completion!")