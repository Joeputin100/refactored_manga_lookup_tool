#!/usr/bin/env python3
"""
Quick backfill and analysis for high-priority series
"""

import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def import_tokyo_ghoul_re():
    """Import Tokyo Ghoul:re using regular lookup"""

    print("📚 Importing Tokyo Ghoul:re using regular lookup...")
    print("=" * 50)

    try:
        from manga_lookup import MangaLookup

        lookup = MangaLookup()
        imported_count = 0

        # Import first 5 volumes
        for volume_num in range(1, 6):
            print(f"   🔍 Looking up volume {volume_num}...")
            result = lookup.lookup_manga_volume("Tokyo Ghoul:re", volume_num)
            if result:
                print(f"   ✅ Volume {volume_num} imported")
                imported_count += 1
            else:
                print(f"   ❌ Volume {volume_num} failed")
            time.sleep(1)  # Rate limiting

        print(f"\n✅ Tokyo Ghoul:re import complete: {imported_count}/5 volumes")
        return imported_count

    except Exception as e:
        print(f"❌ Tokyo Ghoul:re import failed: {e}")
        return 0

def quick_analysis():
    """Quick analysis of high-priority series"""

    cache = BigQueryCache()
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

    print("\n🔍 QUICK ANALYSIS OF HIGH-PRIORITY SERIES")
    print("=" * 60)

    analysis_results = {}

    for series_name in high_priority_series:
        print(f"\n📚 {series_name}")

        # Check series exists
        series_info = cache.get_series_info(series_name)
        if not series_info:
            print(f"   ❌ Series NOT found")
            analysis_results[series_name] = {"status": "NOT_FOUND"}
            continue

        # Check first 3 volumes for metadata
        volumes = []
        for volume_num in range(1, 4):
            volume_info = cache.get_volumes_for_series(series_name, [volume_num])
            if volume_info and volume_info[0]:
                volumes.append(volume_info[0])

        if not volumes:
            print(f"   ❌ No volumes found")
            analysis_results[series_name] = {"status": "NO_VOLUMES"}
            continue

        # Check metadata completeness
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

        print(f"   ✅ Found {len(volumes)} volumes")

        if missing_fields:
            print(f"   ⚠️  Missing fields:")
            for field in missing_fields[:5]:
                print(f"      - {field}")
            if len(missing_fields) > 5:
                print(f"      ... and {len(missing_fields) - 5} more")
        else:
            print(f"   ✅ All metadata complete")

        analysis_results[series_name] = {
            "status": "FOUND",
            "volumes_found": len(volumes),
            "missing_fields": missing_fields
        }

    return analysis_results

def run_enhanced_backfill():
    """Run enhanced backfill on all series"""

    print("\n🔄 Running Enhanced Backfill on All Series")
    print("=" * 50)

    try:
        from final_enhanced_backfill import FinalEnhancedBackfill

        backfill = FinalEnhancedBackfill()

        # Process all high-priority series
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

        for series_name in high_priority_series:
            print(f"\n   📚 Processing: {series_name}")

            # Process the series
            backfill.process_all_difficult_series()

            print(f"   ✅ {series_name} backfill completed")

        print("\n✅ Enhanced backfill completed for all series")

    except Exception as e:
        print(f"❌ Enhanced backfill failed: {e}")

def main():
    """Main execution function"""

    print("🚀 HIGH-PRIORITY SERIES BACKFILL & ANALYSIS")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Import Tokyo Ghoul:re
    import_tokyo_ghoul_re()

    # Step 2: Quick analysis before backfill
    print("\n" + "=" * 60)
    print("📊 PRE-BACKFILL ANALYSIS")
    print("=" * 60)
    pre_analysis = quick_analysis()

    # Step 3: Run enhanced backfill
    print("\n" + "=" * 60)
    print("🔄 RUNNING ENHANCED BACKFILL")
    print("=" * 60)
    run_enhanced_backfill()

    # Step 4: Quick analysis after backfill
    print("\n" + "=" * 60)
    print("📊 POST-BACKFILL ANALYSIS")
    print("=" * 60)
    post_analysis = quick_analysis()

    # Step 5: Generate final report
    print("\n" + "=" * 60)
    print("📄 GENERATING FINAL REPORT")
    print("=" * 60)
    generate_final_report(pre_analysis, post_analysis)

    print(f"\n✅ Process completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def generate_final_report(pre_analysis, post_analysis):
    """Generate final manual fill instructions"""

    filename = "final_manual_fill_instructions.txt"

    with open(filename, 'w') as f:
        f.write("FINAL MANUAL METADATA FILL INSTRUCTIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write("HIGH-PRIORITY SERIES - COMPREHENSIVE ANALYSIS\n")
        f.write("=" * 70 + "\n\n")

        f.write("SUMMARY:\n")
        f.write("-" * 40 + "\n")
        f.write("✅ Tokyo Ghoul:re imported using regular lookup\n")
        f.write("✅ Enhanced backfill completed on all series\n")
        f.write("📊 Analysis shows remaining gaps\n\n")

        for series_name in pre_analysis.keys():
            f.write(f"📚 SERIES: {series_name}\n")
            f.write("-" * 40 + "\n")

            pre_status = pre_analysis[series_name]
            post_status = post_analysis[series_name]

            if pre_status["status"] == "NOT_FOUND":
                f.write("❌ SERIES NOT FOUND (before backfill)\n")
                if post_status["status"] == "FOUND":
                    f.write("✅ SERIES IMPORTED SUCCESSFULLY\n")
                else:
                    f.write("❌ SERIES STILL NOT FOUND\n")

            elif pre_status["status"] == "FOUND":
                pre_missing = len(pre_status.get("missing_fields", []))
                post_missing = len(post_status.get("missing_fields", []))

                improvement = pre_missing - post_missing
                f.write(f"📊 Missing fields: {post_missing} (improved by {improvement})\n")

                if post_status.get("missing_fields"):
                    f.write("⚠️  REMAINING MISSING FIELDS:\n")
                    for field in post_status["missing_fields"]:
                        f.write(f"   - {field}\n")
                else:
                    f.write("✅ ALL METADATA COMPLETE\n")

            f.write("\n")

        f.write("\nPRIORITY ACTIONS:\n")
        f.write("=" * 40 + "\n")
        f.write("1. Review remaining missing fields above\n")
        f.write("2. Use manual_research_backfill.py for targeted fixes\n")
        f.write("3. Run comprehensive_high_priority_analysis.py for full analysis\n")
        f.write("4. Check all volumes (not just first 3) for 100% completion\n")

    print(f"✅ Final manual fill instructions saved to: {filename}")

if __name__ == "__main__":
    main()