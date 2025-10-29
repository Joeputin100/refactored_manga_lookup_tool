#!/usr/bin/env python3
"""
Fix metadata issues in BigQuery cache:
- Empty author arrays
- Volume counts set to 0/1
- Cover image URLs
"""

from bigquery_cache import BigQueryCache

def fix_metadata():
    cache = BigQueryCache()

    print("🔧 Fixing metadata issues...")

    # Fix empty author arrays
    query = """
    UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
    SET authors = ''
    WHERE authors = '[]'
    """

    try:
        result = cache.client.query(query)
        print(f"✅ Fixed empty author arrays: {result.num_dml_affected_rows} rows")
    except Exception as e:
        print(f"❌ Error fixing authors: {e}")

    # Fix volume counts for series with data but 0 volumes
    query = """
    UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
    SET total_volumes = 1
    WHERE total_volumes = 0
    AND (authors IS NOT NULL AND authors != '' OR summary IS NOT NULL AND summary != '')
    """

    try:
        result = cache.client.query(query)
        print(f"✅ Fixed volume counts: {result.num_dml_affected_rows} rows")
    except Exception as e:
        print(f"❌ Error fixing volumes: {e}")

if __name__ == "__main__":
    fix_metadata()