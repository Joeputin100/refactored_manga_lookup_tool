#!/usr/bin/env python3
"""
Quick fix for alternate edition series that failed BigQuery schema validation
"""

import sys
import os
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
from alternate_edition_mapper import AlternateEditionMapper


def fix_alternate_editions():
    """Fix alternate edition series that failed due to schema validation"""
    print("🔧 Fixing Alternate Edition Series")
    print("=" * 50)

    cache = BigQueryCache()
    mapper = AlternateEditionMapper()

    if not cache.enabled:
        print("❌ BigQuery cache not available")
        return

    # List of problematic series that failed due to volume descriptions
    problematic_series = [
        "Attack on Titan: Colossal Edition",
        "Boruto: Two Blue Vortex",
        "My Hero Academia",
        "To Your Eternity",
        "Spy x Family",
        "Magus of the Library",
        "Blue Note",
        "Crayon Shinchan",
        "Sho-ha Shoten",
        "Otherworldly Izakaya Nobu"
    ]

    fixed_count = 0

    for series_name in problematic_series:
        print(f"\n📚 Fixing: {series_name}")

        # Get current cached info
        current_info = cache.get_series_info(series_name)
        if not current_info:
            print(f"  ❌ No cached info found")
            continue

        # Get volume mapping info
        volume_info = mapper.get_volume_info_for_series(series_name)

        # Update the volume count to use string format
        if volume_info['total_volumes']:
            current_info['extant_volumes'] = str(volume_info['total_volumes'])
            current_info['is_alternate_edition'] = volume_info['is_alternate_edition']
            current_info['standard_series_name'] = volume_info['standard_series_name']
            current_info['volume_mapping'] = volume_info['volume_mapping']

            # Try to cache again with string volume count
            try:
                cache.cache_series_info(series_name, current_info)
                print(f"  ✅ Fixed: Volume count set to '{current_info['extant_volumes']}'")
                fixed_count += 1
            except Exception as e:
                print(f"  ❌ Cache failed: {e}")
        else:
            print(f"  ⚠️ No volume mapping available")

    print(f"\n🎉 Fixed {fixed_count}/{len(problematic_series)} problematic series")


def test_alternate_edition_mapping():
    """Test the alternate edition mapping"""
    print("\n🧪 Testing Alternate Edition Mapping")
    print("=" * 50)

    mapper = AlternateEditionMapper()

    test_series = [
        "Attack on Titan: Colossal Edition",
        "Boruto: Two Blue Vortex",
        "My Hero Academia"
    ]

    for series in test_series:
        info = mapper.get_volume_info_for_series(series)
        print(f"\n📚 {series}")
        print(f"   Alternate Edition: {info['is_alternate_edition']}")
        print(f"   Standard Series: {info['standard_series_name']}")
        print(f"   Total Volumes: {info['total_volumes']}")
        print(f"   Description: {info['description']}")

        if info['volume_mapping']:
            print(f"   Sample Mapping: {dict(list(info['volume_mapping'].items())[:3])}...")


def main():
    """Main function"""
    print("🎯 Alternate Edition Fixer")
    print("=" * 50)

    # Test mapping first
    test_alternate_edition_mapping()

    # Fix problematic series
    fix_alternate_editions()


if __name__ == "__main__":
    main()