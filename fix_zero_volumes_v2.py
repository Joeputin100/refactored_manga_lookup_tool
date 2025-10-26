#!/usr/bin/env python3
"""
Fix series with 0 extant volumes by querying DeepSeek for corrected information
and Google Books for cover images.
"""

import json
import time
from bigquery_cache import BigQueryCache
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState

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
        print(f"❌ Error getting specific series: {e}")
        return []

def query_deepseek_for_series_info(series_name, project_state):
    """Query DeepSeek API for comprehensive series information"""
    try:
        deepseek_api = DeepSeekAPI()
        google_api = GoogleBooksAPI()

        print(f"🔍 Querying DeepSeek for: {series_name}")

        # First, get corrected series name suggestions
        suggestions = deepseek_api.correct_series_name(series_name)
        if suggestions:
            corrected_name = suggestions[0]  # Use first suggestion
            print(f"✅ DeepSeek suggested: {corrected_name}")
        else:
            corrected_name = series_name
            print(f"⚠️ No suggestions from DeepSeek, using original: {series_name}")

        # Get comprehensive book info for volume 1
        book_data = deepseek_api.get_book_info(corrected_name, 1, project_state)

        if book_data:
            # Build comprehensive series info
            series_info = {
                "corrected_series_name": corrected_name,
                "authors": book_data.get("authors", []),
                "extant_volumes": book_data.get("number_of_extant_volumes", 0),
                "summary": book_data.get("description", ""),
                "spinoff_series": [],
                "alternate_editions": [],
                "genres": book_data.get("genres", []),
                "publisher": book_data.get("publisher_name", ""),
                "status": "Unknown",
                "alternative_titles": suggestions[1:] if len(suggestions) > 1 else [],
                "adaptations": [],
                "cover_image_url": book_data.get("cover_image_url", None)
            }

            # If no cover image, try Google Books
            if not series_info["cover_image_url"]:
                print(f"🔍 Searching Google Books for cover: {corrected_name}")
                cover_url = google_api.get_series_cover_url(corrected_name)
                if cover_url:
                    series_info["cover_image_url"] = cover_url
                    print(f"✅ Found Google Books cover for: {corrected_name}")
                else:
                    print(f"❌ No cover found for: {corrected_name}")

            print(f"✅ Successfully retrieved info for: {corrected_name}")
            print(f"   Volumes: {series_info['extant_volumes']}")
            print(f"   Authors: {series_info['authors']}")
            print(f"   Publisher: {series_info['publisher']}")

            return series_info
        else:
            print(f"❌ Failed to get book data for: {series_name}")
            return None

    except Exception as e:
        print(f"❌ Error querying DeepSeek for {series_name}: {e}")
        return None

def update_series_in_bigquery(series_name, series_info):
    """Update series information in BigQuery"""
    cache = BigQueryCache()
    if not cache.enabled:
        return False

    try:
        # Check if series exists
        check_query = f"""
        SELECT COUNT(*) as count
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE series_name = '{series_name}'
        """

        result = cache.client.query(check_query).result()
        for row in result:
            exists = row.count > 0

        if exists:
            # Update existing record
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
            SET
                total_volumes = {series_info['extant_volumes']},
                authors = {json.dumps(series_info['authors'])},
                publisher = '{series_info['publisher']}',
                status = '{series_info['status']}',
                genres = {json.dumps(series_info['genres'])},
                alternative_titles = {json.dumps(series_info['alternative_titles'])},
                cover_image_url = '{series_info['cover_image_url'] if series_info['cover_image_url'] else ''}',
                summary = '{series_info['summary'].replace("'", "''") if series_info['summary'] else ''}'
            WHERE series_name = '{series_name}'
            """
        else:
            # Insert new record
            update_query = f"""
            INSERT INTO `static-webbing-461904-c4.manga_lookup_cache.series_info`
            (series_name, total_volumes, authors, publisher, status, genres, alternative_titles, cover_image_url, summary)
            VALUES (
                '{series_name}',
                {series_info['extant_volumes']},
                {json.dumps(series_info['authors'])},
                '{series_info['publisher']}',
                '{series_info['status']}',
                {json.dumps(series_info['genres'])},
                {json.dumps(series_info['alternative_titles'])},
                '{series_info['cover_image_url'] if series_info['cover_image_url'] else ''}',
                '{series_info['summary'].replace("'", "''") if series_info['summary'] else ''}'
            )
            """

        cache.client.query(update_query).result()
        print(f"✅ Updated BigQuery for: {series_name}")
        return True

    except Exception as e:
        print(f"❌ Error updating BigQuery for {series_name}: {e}")
        return False

def main():
    print("🚀 Starting series metadata fix task...")

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

        # Query DeepSeek for corrected information
        series_info = query_deepseek_for_series_info(series_name, project_state)

        if series_info and series_info['extant_volumes'] > 0:
            # Update BigQuery
            if update_series_in_bigquery(series_name, series_info):
                successful_updates += 1
                print(f"✅ Successfully updated: {series_name}")
            else:
                failed_updates += 1
                print(f"❌ Failed to update BigQuery for: {series_name}")
        else:
            failed_updates += 1
            print(f"❌ No valid data retrieved for: {series_name}")

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