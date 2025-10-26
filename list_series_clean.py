#!/usr/bin/env python3
"""
List all unique series in BigQuery cache with their metadata and total extant volumes
"""

from bigquery_cache import BigQueryCache

def list_unique_series():
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

        # Group by series name and keep the entry with highest volume count
        series_dict = {}
        for row in result:
            name = row.series_name
            volumes = row.total_volumes

            # If we haven't seen this series, or if this entry has more volumes
            if name not in series_dict or volumes > series_dict[name]['volumes']:
                series_dict[name] = {
                    'volumes': volumes,
                    'authors': row.authors if hasattr(row, 'authors') else [],
                    'publisher': row.publisher if hasattr(row, 'publisher') else 'Unknown',
                    'status': row.status if hasattr(row, 'status') else 'Unknown',
                    'genres': row.genres if hasattr(row, 'genres') else [],
                    'alternative_titles': row.alternative_titles if hasattr(row, 'alternative_titles') else [],
                    'has_cover': bool(row.cover_image_url) if hasattr(row, 'cover_image_url') else False
                }

        # Convert to sorted list
        series_list = [(name, data) for name, data in series_dict.items()]
        series_list.sort(key=lambda x: x[0])

        # Display results
        print("📚 All Unique Series in BigQuery Cache (Sorted Alphabetically)")
        print("=" * 80)

        for series_name, data in series_list:
            print(f"Series: {series_name}")
            print(f"  Volumes: {data['volumes']}")
            print(f"  Authors: {data['authors']}")
            print(f"  Publisher: {data['publisher']}")
            print(f"  Status: {data['status']}")
            print(f"  Genres: {data['genres']}")
            print(f"  Alternative Titles: {data['alternative_titles']}")
            print(f"  Has Cover: {'Yes' if data['has_cover'] else 'No'}")
            print("-" * 80)

        # Statistics
        total_series = len(series_list)
        total_volumes = sum(data['volumes'] for _, data in series_list)
        avg_volumes = total_volumes / total_series if total_series > 0 else 0
        max_volumes = max(data['volumes'] for _, data in series_list) if series_list else 0
        min_volumes = min(data['volumes'] for _, data in series_list) if series_list else 0

        print(f"\n📊 Statistics:")
        print(f"Total unique series: {total_series}")
        print(f"Total volumes across all series: {total_volumes}")
        print(f"Average volumes per series: {avg_volumes:.1f}")
        print(f"Max volumes in a series: {max_volumes}")
        print(f"Min volumes in a series: {min_volumes}")

    except Exception as e:
        print(f"❌ Error querying BigQuery: {e}")

if __name__ == "__main__":
    list_unique_series()