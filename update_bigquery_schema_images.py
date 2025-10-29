#!/usr/bin/env python3
"""
Update BigQuery schema to support binary image data storage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache
import google.cloud.bigquery as bigquery

def update_schema_for_images():
    """Update BigQuery schema to add binary image storage fields"""

    cache = BigQueryCache()
    client = cache.client

    print("🔧 Updating BigQuery Schema for Image Storage")
    print("=" * 50)

    # Get current table
    table_ref = cache.volumes_table_id
    table = client.get_table(table_ref)

    print(f"📊 Current table: {table_ref}")
    print(f"📋 Current schema has {len(table.schema)} fields")

    # Check if we already have the image fields
    current_fields = {field.name for field in table.schema}
    new_fields_needed = []

    if 'cover_image_data' not in current_fields:
        new_fields_needed.append(bigquery.SchemaField("cover_image_data", "BYTES", mode="NULLABLE"))

    if 'cover_image_mime_type' not in current_fields:
        new_fields_needed.append(bigquery.SchemaField("cover_image_mime_type", "STRING", mode="NULLABLE"))

    if 'cover_image_size' not in current_fields:
        new_fields_needed.append(bigquery.SchemaField("cover_image_size", "INTEGER", mode="NULLABLE"))

    if 'cover_image_source' not in current_fields:
        new_fields_needed.append(bigquery.SchemaField("cover_image_source", "STRING", mode="NULLABLE"))

    if not new_fields_needed:
        print("✅ Schema already has all required image fields")
        return True

    print(f"📝 Adding {len(new_fields_needed)} new fields:")
    for field in new_fields_needed:
        print(f"   ➕ {field.name} ({field.field_type})")

    # Update the schema
    try:
        new_schema = table.schema[:] + new_fields_needed
        table.schema = new_schema

        client.update_table(table, ["schema"])

        print("✅ Schema updated successfully!")
        print("\n📋 New schema fields:")
        for field in new_schema:
            print(f"   {field.name}: {field.field_type}")

        return True

    except Exception as e:
        print(f"❌ Failed to update schema: {e}")
        return False

def test_schema_update():
    """Test that the schema update worked"""

    cache = BigQueryCache()
    client = cache.client

    print("\n🧪 Testing Schema Update")
    print("=" * 30)

    table_ref = cache.volumes_table_id
    table = client.get_table(table_ref)

    current_fields = {field.name: field.field_type for field in table.schema}

    required_fields = {
        'cover_image_data': 'BYTES',
        'cover_image_mime_type': 'STRING',
        'cover_image_size': 'INTEGER',
        'cover_image_source': 'STRING'
    }

    print("📋 Current schema fields:")
    for field_name, field_type in current_fields.items():
        status = "✅" if field_name in required_fields else "  "
        print(f"   {status} {field_name}: {field_type}")

    # Check if all required fields are present
    missing_fields = []
    for field_name, expected_type in required_fields.items():
        if field_name not in current_fields:
            missing_fields.append(field_name)
        elif current_fields[field_name] != expected_type:
            print(f"⚠️  Field {field_name} has type {current_fields[field_name]} instead of {expected_type}")

    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    else:
        print("✅ All required image fields are present and correct!")
        return True

if __name__ == "__main__":
    # Update the schema
    success = update_schema_for_images()

    if success:
        # Test the update
        test_schema_update()

    print("\n🎯 Next steps:")
    print("1. Update BigQueryCache class to handle image data")
    print("2. Create enhanced backfill with image caching")
    print("3. Update existing scripts to use new schema")