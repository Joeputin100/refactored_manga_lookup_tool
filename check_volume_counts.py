#!/usr/bin/env python3
"""
Check for series with incorrect volume counts (total_volumes = "1")
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def check_volume_counts():
    """Check for series with total_volumes = '1'"""
    try:
        bq = BigQueryCache()

        query = """
        SELECT series_name, total_volumes, authors, publisher, genres, status
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE total_volumes = 1
        ORDER BY series_name
        """

        result = bq.client.query(query).result()

        print('Series with total_volumes = "1":')
        print('=' * 50)
        count = 0
        for row in result:
            count += 1
            print(f'{count}. {row.series_name}')
            print(f'   Volumes: {row.total_volumes}')
            print(f'   Authors: {row.authors}')
            print(f'   Publisher: {row.publisher}')
            print(f'   Genres: {row.genres}')
            print(f'   Status: {row.status}')
            print()

        print(f'Total series with volume count = 1: {count}')
        return count

    except Exception as e:
        print(f"❌ Error checking volume counts: {e}")
        return 0

if __name__ == "__main__":
    check_volume_counts()