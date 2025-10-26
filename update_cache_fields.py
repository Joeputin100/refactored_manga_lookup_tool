#!/usr/bin/env python3
"""
Update existing cached series with missing fields using Vertex AI
"""

import sys
import os
import time
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manga_lookup import VertexAIAPI, ProjectState
from bigquery_cache import BigQueryCache


def get_cached_series_list():
    """Get list of all series in the cache"""
    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not enabled")
        return []

    try:
        # Get all series names from the cache
        query = """
        SELECT DISTINCT series_name
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        """
        query_job = cache.client.query(query)
        series_list = [row['series_name'] for row in query_job]
        print(f"📊 Found {len(series_list)} series in cache")
        return series_list
    except Exception as e:
        print(f"❌ Error getting series list: {e}")
        return []


def update_series_with_missing_fields(series_name):
    """Update a single series with missing fields using Vertex AI"""
    try:
        print(f"\n🔄 Updating: {series_name}")

        # Initialize Vertex AI API
        vertex_api = VertexAIAPI()
        if not vertex_api:
            print(f"❌ Vertex AI API not available for {series_name}")
            return False

        # Get comprehensive series info with new fields
        project_state = ProjectState()
        series_info = vertex_api.get_comprehensive_series_info(series_name, project_state)

        if series_info:
            print(f"✅ Updated fields for {series_name}")
            print(f"   - Genres: {series_info.get('genres', [])}")
            print(f"   - Publisher: {series_info.get('publisher', '')}")
            print(f"   - Status: {series_info.get('status', '')}")
            print(f"   - Alternative titles: {series_info.get('alternative_titles', [])}")
            print(f"   - Adaptations: {series_info.get('adaptations', [])}")
            return True
        else:
            print(f"❌ Failed to get updated info for {series_name}")
            return False

    except Exception as e:
        print(f"❌ Error updating {series_name}: {e}")
        return False


def main():
    """Main function to update all cached series"""
    print("🚀 Starting cache field update process...")

    # Get list of series to update
    series_list = get_cached_series_list()

    if not series_list:
        print("❌ No series found to update")
        return

    print(f"\n📋 Series to update ({len(series_list)}):")
    for i, series in enumerate(series_list, 1):
        print(f"  {i}. {series}")

    # Batch the updates - 11 series per batch (5 batches for 55 series)
    batch_size = 11
    batches = [series_list[i:i + batch_size] for i in range(0, len(series_list), batch_size)]

    print(f"\n📦 Processing in {len(batches)} batches...")

    success_count = 0
    failed_count = 0

    for batch_num, batch in enumerate(batches, 1):
        print(f"\n--- Batch {batch_num}/{len(batches)} ---")

        for series_name in batch:
            if update_series_with_missing_fields(series_name):
                success_count += 1
            else:
                failed_count += 1

            # Add a small delay between API calls to avoid rate limiting
            time.sleep(2)

        # Add a longer delay between batches
        if batch_num < len(batches):
            print(f"\n⏳ Waiting 10 seconds before next batch...")
            time.sleep(10)

    print(f"\n🎯 Update Summary:")
    print(f"   ✅ Successfully updated: {success_count}")
    print(f"   ❌ Failed to update: {failed_count}")
    print(f"   📊 Total processed: {success_count + failed_count}")


if __name__ == "__main__":
    main()