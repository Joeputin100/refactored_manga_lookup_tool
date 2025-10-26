#!/usr/bin/env python3
"""
List all series in BigQuery cache with metadata and total extant volumes
"""

from bigquery_cache import BigQueryCache

def list_all_series():
    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not available")
        return

    try:
        # Get all series with basic info
        query = """
        SELECT
            series_name,
            total_volumes,
            authors,
            publisher,
            status,
            genres,
            alternative_titles,
            cover_image_url
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        ORDER BY series_name
        """

        result = cache.client.query(query).result()

        series_list = []
        for row in result:
            series_list.append({
                'name': row.series_name,
                'volumes': row.total_volumes,
                'authors': row.authors if hasattr(row, 'authors') else [],
                'publisher': row.publisher if hasattr(row, 'publisher') else 'Unknown',
                'status': row.status if hasattr(row, 'status') else 'Unknown',
                'genres': row.genres if hasattr(row, 'genres') else [],
                'alternative_titles': row.alternative_titles if hasattr(row, 'alternative_titles') else [],
                'has_cover': bool(row.cover_image_url) if hasattr(row, 'cover_image_url') else False
            })

        # Display results
        print("📚 All Series in BigQuery Cache")
        print("=" * 80)

        for series in series_list:
            print(f"Series: {series['name']}")
            print(f"  Volumes: {series['volumes']}")
            print(f"  Authors: {series['authors']}")
            print(f"  Publisher: {series['publisher']}")
            print(f"  Status: {series['status']}")
            print(f"  Genres: {series['genres']}")
            print(f"  Alternative Titles: {series['alternative_titles']}")
            print(f"  Has Cover: {'Yes' if series['has_cover'] else 'No'}")
            print("-" * 80)

        # Statistics
        total_series = len(series_list)
        total_volumes = sum(series['volumes'] for series in series_list)
        avg_volumes = total_volumes / total_series if total_series > 0 else 0
        max_volumes = max(series['volumes'] for series in series_list) if series_list else 0
        min_volumes = min(series['volumes'] for series in series_list) if series_list else 0

        print(f"\n📊 Statistics:")
        print(f"Total series: {total_series}")
        print(f"Total volumes across all series: {total_volumes}")
        print(f"Average volumes per series: {avg_volumes:.1f}")
        print(f"Max volumes in a series: {max_volumes}")
        print(f"Min volumes in a series: {min_volumes}")

    except Exception as e:
        print(f"❌ Error querying BigQuery: {e}")

if __name__ == "__main__":
    list_all_series()