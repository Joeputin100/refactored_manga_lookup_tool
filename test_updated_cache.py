#!/usr/bin/env python3
"""
Test updated cache data for a specific series
"""
import sys
import os
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def test_series_cache(series_name: str):
    """Test cache data for a specific series"""
    cache = BigQueryCache()

    print(f'🔍 Testing cache data for: {series_name}')

    info = cache.get_series_info(series_name)
    if info:
        print(f'✅ Found cached data:')
        print(json.dumps(info, indent=2))

        # Check for missing fields
        missing_fields = []
        expected_fields = ['genres', 'publisher', 'status', 'alternative_titles', 'adaptations', 'summary']
        for field in expected_fields:
            if not info.get(field):
                missing_fields.append(field)

        if missing_fields:
            print(f'⚠️  Missing fields: {missing_fields}')
        else:
            print(f'✅ All expected fields present')

        # Check volume count
        actual_volumes = info.get('extant_volumes', 0)
        expected_volumes = {
            'Attack on Titan': 34,
            'Assassination Classroom': 21,
            'A Polar Bear in Love': 5,
            'Berserk': 41
        }
        expected = expected_volumes.get(series_name, 0)
        if actual_volumes != expected:
            print(f'⚠️  Volume count mismatch: {actual_volumes} (expected: {expected})')
        else:
            print(f'✅ Volume count correct: {actual_volumes}')

    else:
        print(f'❌ No cached data found')

if __name__ == "__main__":
    test_series_cache("Attack on Titan")
    test_series_cache("Attack on titan")  # Test case insensitive