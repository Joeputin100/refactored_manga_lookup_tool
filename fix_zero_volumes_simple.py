#!/usr/bin/env python3
"""
Simple script to fix series with 0 extant volumes by querying DeepSeek for volume counts only.
"""

import json
import time
from bigquery_cache import BigQueryCache
from manga_lookup import DeepSeekAPI, ProjectState

def get_series_with_zero_volumes():
    """Get all series with 0 volumes from BigQuery"""
    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not available")
        return []

    try:
        query = """
        SELECT series_name
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE total_volumes = 0
        ORDER BY series_name
        """

        result = cache.client.query(query).result()
        zero_volume_series = [row.series_name for row in result]
        return zero_volume_series
    except Exception as e:
        print(f"❌ Error querying zero volume series: {e}")
        return []

def get_specific_series():
    """Get specific series by index (23 and 81)"""
    cache = BigQueryCache()
    if not cache.enabled:
        return []

    try:
        query = """
        SELECT series_name
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        ORDER BY series_name
        """

        result = cache.client.query(query).result()
        all_series = [row.series_name for row in result]

        # Get unique series names
        unique_series = list(set(all_series))
        unique_series.sort()

        # Get series at positions 23 and 81 (0-indexed)
        specific_series = []
        if len(unique_series) > 23:
            specific_series.append(unique_series[23])
        if len(unique_series) > 81:
            specific_series.append(unique_series[81])

        return specific_series
    except Exception as e:
        print(f"��� Error getting specific series: {e}")
        return []

def query_deepseek_for_volume_count(series_name, project_state):
    """Query DeepSeek API for volume count only"""
    try:
        deepseek_api = DeepSeekAPI()

        print(f"🔍 Querying DeepSeek for: {series_name}")

        # Get comprehensive book info for volume 1
        book_data = deepseek_api.get_book_info(series_name, 1, project_state)

        if book_data:
            volume_count = book_data.get("number_of_extant_volumes", 0)
            authors = book_data.get("authors", [])
            publisher = book_data.get("publisher_name", "")

            print(f"✅ Retrieved info for: {series_name}")
            print(f"   Volumes: {volume_count}")
            print(f"   Authors: {authors}")
            print(f"   Publisher: {publisher}")

            return volume_count
        else:
            print(f"❌ Failed to get book data for: {series_name}")
            return 0

    except Exception as e:
        print(f"❌ Error querying DeepSeek for {series_name}: {e}")
        return 0

def update_volume_count_in_bigquery(series_name, volume_count):
    """Update only the volume count in BigQuery"""
    cache = BigQueryCache()
    if not cache.enabled:
        return False

    try:
        # Simple update query
        update_query = f"""
        UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
        SET total_volumes = {volume_count}
        WHERE series_name = '{series_name}'
        """

        cache.client.query(update_query).result()
        print(f"✅ Updated volume count for: {series_name} to {volume_count}")
        return True

    except Exception as e:
        print(f"❌ Error updating BigQuery for {series_name}: {e}")
        return False

def main():
    print("🚀 Starting series volume count fix task...")

    # Initialize project state
    try:
        project_state = ProjectState()
        print("✅ ProjectState initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ProjectState: {e}")
        return

    # Get series to fix
    zero_volume_series = get_series_with_zero_volumes()
    specific_series = get_specific_series()

    all_series_to_fix = list(set(zero_volume_series + specific_series))
    all_series_to_fix.sort()

    print(f"📋 Series to fix ({len(all_series_to_fix)}):")
    for i, series in enumerate(all_series_to_fix, 1):
        print(f"  {i}. {series}")

    # Process each series
    successful_updates = 0
    failed_updates = 0

    for series_name in all_series_to_fix:
        print(f"\n{'='*60}")
        print(f"Processing: {series_name}")
        print(f"{'='*60}")

        # Query DeepSeek for volume count
        volume_count = query_deepseek_for_volume_count(series_name, project_state)

        if volume_count > 0:
            # Update BigQuery
            if update_volume_count_in_bigquery(series_name, volume_count):
                successful_updates += 1
                print(f"✅ Successfully updated: {series_name}")
            else:
                failed_updates += 1
                print(f"❌ Failed to update BigQuery for: {series_name}")
        else:
            failed_updates += 1
            print(f"❌ No valid volume count retrieved for: {series_name}")

        # Rate limiting
        print("⏰ Waiting 5 seconds before next query...")
        time.sleep(5)

    # Summary
    print(f"\n{'='*60}")
    print("📊 TASK COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful updates: {successful_updates}")
    print(f"❌ Failed updates: {failed_updates}")
    print(f"📋 Total series processed: {len(all_series_to_fix)}")

if __name__ == "__main__":
    main()