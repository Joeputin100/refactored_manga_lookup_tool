#!/usr/bin/env python3
"""
Update BigQuery schema to accommodate all new fields
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
from google.cloud import bigquery

def check_and_update_schema():
    """Check current schema and update if needed"""
    cache = BigQueryCache()

    print('🔍 Checking current BigQuery schema...')

    try:
        # Get current table schema
        table_ref = cache.client.dataset(cache.dataset_id).table('series_info')
        table = cache.client.get_table(table_ref)

        print('Current schema fields:')
        current_fields = {field.name for field in table.schema}
        for field in table.schema:
            print(f'  {field.name}: {field.field_type}')

        # Define new fields we want to add
        new_fields = [
            bigquery.SchemaField('genres', 'STRING', mode='REPEATED'),
            bigquery.SchemaField('publisher', 'STRING'),
            bigquery.SchemaField('status', 'STRING'),
            bigquery.SchemaField('alternative_titles', 'STRING', mode='REPEATED'),
            bigquery.SchemaField('adaptations', 'STRING', mode='REPEATED'),
        ]

        # Check which fields are missing
        missing_fields = []
        for field in new_fields:
            if field.name not in current_fields:
                missing_fields.append(field)
                print(f'❌ Missing field: {field.name}')

        if missing_fields:
            print(f'\\n🔄 Adding {len(missing_fields)} missing fields to schema...')

            # Update schema
            new_schema = table.schema[:] + missing_fields
            table.schema = new_schema

            # Update the table
            table = cache.client.update_table(table, ["schema"])
            print('✅ Schema updated successfully!')

            # Verify the update
            table = cache.client.get_table(table_ref)
            print('\\nUpdated schema:')
            for field in table.schema:
                print(f'  {field.name}: {field.field_type}')
        else:
            print('\\n✅ Schema already has all required fields!')

    except Exception as e:
        print(f'❌ Error updating schema: {e}')

def create_new_table_with_full_schema():
    """Create a new table with the complete schema if needed"""
    cache = BigQueryCache()

    print('\\n🔄 Creating new table with complete schema...')

    # Define complete schema
    full_schema = [
        bigquery.SchemaField('series_name', 'STRING', mode='REQUIRED'),
        bigquery.SchemaField('corrected_series_name', 'STRING'),
        bigquery.SchemaField('authors', 'STRING', mode='REPEATED'),
        bigquery.SchemaField('total_volumes', 'INTEGER'),
        bigquery.SchemaField('summary', 'STRING'),
        bigquery.SchemaField('spinoff_series', 'STRING', mode='REPEATED'),
        bigquery.SchemaField('alternate_editions', 'STRING', mode='REPEATED'),
        bigquery.SchemaField('cover_image_url', 'STRING'),
        bigquery.SchemaField('last_updated', 'TIMESTAMP'),
        bigquery.SchemaField('api_source', 'STRING'),
        # New fields
        bigquery.SchemaField('genres', 'STRING', mode='REPEATED'),
        bigquery.SchemaField('publisher', 'STRING'),
        bigquery.SchemaField('status', 'STRING'),
        bigquery.SchemaField('alternative_titles', 'STRING', mode='REPEATED'),
        bigquery.SchemaField('adaptations', 'STRING', mode='REPEATED'),
    ]

    try:
        # Create new table
        new_table_id = 'series_info_complete'
        table_ref = cache.client.dataset(cache.dataset_id).table(new_table_id)
        table = bigquery.Table(table_ref, schema=full_schema)
        table = cache.client.create_table(table)

        print(f'✅ New table {new_table_id} created with complete schema!')

        # Copy data from old table to new table
        copy_query = f"""
        INSERT INTO `static-webbing-461904-c4.manga_lookup_cache.{new_table_id}`
        SELECT
            series_name,
            corrected_series_name,
            authors,
            total_volumes,
            summary,
            spinoff_series,
            alternate_editions,
            cover_image_url,
            last_updated,
            api_source,
            [],  -- genres
            '',  -- publisher
            '',  -- status
            [],  -- alternative_titles
            []   -- adaptations
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        """

        query_job = cache.client.query(copy_query)
        query_job.result()

        print(f'✅ Data copied to new table!')

        # Count records
        count_query = f"""
        SELECT COUNT(*) as count
        FROM `static-webbing-461904-c4.manga_lookup_cache.{new_table_id}`
        """
        count_job = cache.client.query(count_query)
        count_result = list(count_job)[0]['count']

        print(f'📊 New table has {count_result} records')

    except Exception as e:
        print(f'❌ Error creating new table: {e}')

if __name__ == "__main__":
    check_and_update_schema()
    create_new_table_with_full_schema()