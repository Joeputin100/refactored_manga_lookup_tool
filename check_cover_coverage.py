#!/usr/bin/env python3
"""
Check cover image coverage in BigQuery database
"""
import sys
sys.path.append(".")

from bigquery_cache import BigQueryCache

def check_cover_coverage():
    """Check cover image coverage statistics"""

    cache = BigQueryCache()

    if not cache.enabled:
        print("❌ BigQuery cache not enabled")
        return

    print("=== COVER IMAGE COVERAGE ANALYSIS ===\n")

    try:
        # Get a sample of volumes to analyze
        print("📊 Analyzing cover image coverage...")

        # Get some popular series to check coverage
        test_series = ["Fairy Tail", "One Piece", "Naruto", "Attack on Titan", "My Hero Academia"]

        total_volumes = 0
        volumes_with_covers = 0
        cover_sources = {
            "Google Books": 0,
            "Wikipedia": 0,
            "MyAnimeList": 0,
            "MangaDex": 0,
            "Other": 0
        }

        recent_covers = []

        for series in test_series:
            try:
                # Check first 5 volumes for each series
                volumes = cache.get_volumes_for_series(series, [1, 2, 3, 4, 5])
                if volumes:
                    for volume in volumes:
                        if volume:  # Skip None values
                            total_volumes += 1
                            cover_url = volume.get('cover_image_url')

                            if cover_url and cover_url != "":
                                volumes_with_covers += 1

                                # Determine source
                                if "wikipedia" in cover_url or "wikimedia" in cover_url:
                                    cover_sources["Wikipedia"] += 1
                                elif "google" in cover_url:
                                    cover_sources["Google Books"] += 1
                                elif "mal" in cover_url:
                                    cover_sources["MyAnimeList"] += 1
                                elif "mangadex" in cover_url:
                                    cover_sources["MangaDex"] += 1
                                else:
                                    cover_sources["Other"] += 1

                                # Store recent covers
                                if len(recent_covers) < 10:
                                    recent_covers.append({
                                        "series": series,
                                        "volume": volume.get('volume_number'),
                                        "url": cover_url
                                    })
            except Exception as e:
                print(f"❌ Error checking series {series}: {e}")

        print(f"📊 COVER IMAGE STATISTICS (Sample Analysis):")
        print(f"   Total volumes analyzed: {total_volumes:,}")
        print(f"   Volumes with cover images: {volumes_with_covers:,}")

        if total_volumes > 0:
            coverage_pct = volumes_with_covers / total_volumes * 100
            print(f"   Coverage: {coverage_pct:.1f}%")
        else:
            print(f"   Coverage: N/A")

        print(f"\n📊 COVER SOURCE BREAKDOWN:")
        for source, count in cover_sources.items():
            print(f"   {source}: {count:,}")

        print(f"\n🔄 RECENT COVER UPDATES:")
        for i, cover in enumerate(recent_covers, 1):
            series = cover["series"]
            volume = cover["volume"]
            url = cover["url"]
            source = "Unknown"

            if "wikipedia" in url or "wikimedia" in url:
                source = "Wikipedia"
            elif "google" in url:
                source = "Google Books"
            elif "mal" in url:
                source = "MyAnimeList"
            elif "mangadex" in url:
                source = "MangaDex"

            print(f"   {i}. {series} Vol {volume} - {source}")

    except Exception as e:
        print(f"❌ Error analyzing coverage: {e}")
        return

    # Note: For comprehensive analysis, we would need direct SQL access
    print(f"\n💡 Note: This is a sample analysis. For comprehensive coverage statistics,")
    print(f"   direct BigQuery SQL access would be needed.")

if __name__ == "__main__":
    check_cover_coverage()