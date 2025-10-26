#!/usr/bin/env python3
"""
Debug BigQuery cache lookup
"""
from bigquery_cache import BigQueryCache

print("🔍 Debugging BigQuery Cache Lookup")
print("=" * 50)

cache = BigQueryCache()

if not cache.enabled:
    print("❌ BigQuery cache not enabled")
    exit(1)

print("✅ BigQuery cache is enabled")

# Test direct query
print("\n🔍 Testing direct query for 'Attack on Titan'...")

try:
    query = f"""
        SELECT * FROM `{cache.series_table_id}`
        WHERE LOWER(series_name) = LOWER(@series_name)
        ORDER BY last_updated DESC
        LIMIT 1
    """

    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("series_name", "STRING", "Attack on Titan")
        ]
    )
    query_job = cache.client.query(query, job_config=job_config)
    results = list(query_job)

    print(f"📊 Query returned {len(results)} results")

    if results:
        row = results[0]
        print(f"✅ Found cached data:")
        print(f"   series_name: {row.get('series_name')}")
        print(f"   corrected_name: {row.get('corrected_name')}")
        print(f"   authors: {list(row.get('authors', []))}")
        print(f"   total_volumes: {row.get('total_volumes')}")
        print(f"   summary: {row.get('summary', '')[:100]}...")
        print(f"   last_updated: {row.get('last_updated')}")
    else:
        print("❌ No results found in cache")

        # Let's check what's actually in the table
        print("\n🔍 Checking what's in the series table...")
        count_query = f"SELECT COUNT(*) as count FROM `{cache.series_table_id}`"
        count_job = cache.client.query(count_query)
        count_result = list(count_job)
        print(f"📊 Total rows in series table: {count_result[0]['count']}")

        # Show first few rows
        sample_query = f"SELECT series_name, corrected_name, total_volumes FROM `{cache.series_table_id}` LIMIT 5"
        sample_job = cache.client.query(sample_query)
        sample_results = list(sample_job)

        print("📊 Sample rows:")
        for i, row in enumerate(sample_results):
            print(f"   {i+1}. {row.get('series_name')} -> {row.get('corrected_name')} ({row.get('total_volumes')} vols)")

except Exception as e:
    print(f"❌ Query failed: {e}")

print("\n✅ Debug completed")