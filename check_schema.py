#!/usr/bin/env python3
"""
Check the schema of the BigQuery table to understand data types
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def check_schema():
    """Check the schema of the series_info table"""
    try:
        bq = BigQueryCache()

        # Get table schema
        table_ref = bq.client.dataset('manga_lookup_cache').table('series_info')
        table = bq.client.get_table(table_ref)

        print('Schema of series_info table:')
        print('=' * 50)
        for field in table.schema:
            print(f'{field.name}: {field.field_type}')

        # Also check some sample data
        query = """
        SELECT series_name, total_volumes
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        LIMIT 10
        """

        result = bq.client.query(query).result()
        print('\nSample data:')
        print('=' * 50)
        for row in result:
            print(f'{row.series_name}: {row.total_volumes} (type: {type(row.total_volumes)})')

    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_schema()