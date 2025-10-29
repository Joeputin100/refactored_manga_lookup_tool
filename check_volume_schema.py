#!/usr/bin/env python3
"""
Check volume_info table schema
"""

from bigquery_cache import BigQueryCache

def check_schema():
    cache = BigQueryCache()

    print("🔍 Checking volume_info table schema...")

    query = """
    SELECT column_name, data_type
    FROM `static-webbing-461904-c4.manga_lookup_cache`.INFORMATION_SCHEMA.COLUMNS
    WHERE table_name = 'volume_info'
    ORDER BY ordinal_position
    """

    result = cache.client.query(query)
    print("📋 Volume Table Schema:")
    print("-" * 40)
    for row in result:
        print(f"  {row['column_name']}: {row['data_type']}")

    print("\n📋 Sample Volume Data:")
    print("-" * 40)
    query = "SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info` LIMIT 1"
    result = cache.client.query(query)
    for row in result:
        for key, value in dict(row).items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    check_schema()