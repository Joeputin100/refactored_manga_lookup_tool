#!/usr/bin/env python3
"""
Fix author names in BigQuery cache to use proper inverted comma separated format
"""

import json
from bigquery_cache import BigQueryCache

def invert_author_name(name):
    """Convert "First Last" to "Last, First" format"""
    if not name or not isinstance(name, str):
        return name

    # Handle common patterns
    parts = name.strip().split()
    if len(parts) >= 2:
        # If it's already in inverted format, leave it
        if ',' in name:
            return name
        # Convert "First Last" to "Last, First"
        last_name = parts[-1]
        first_names = ' '.join(parts[:-1])
        return f"{last_name}, {first_names}"

    # Single name - leave as is
    return name

def fix_series_authors():
    """Fix author names in series_info table"""
    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not enabled")
        return 0

    try:
        # Get all series with authors
        query = '''
        SELECT series_name, authors
        FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
        WHERE ARRAY_LENGTH(authors) > 0
        '''
        result = cache.client.query(query)

        updated_count = 0
        for row in result:
            original_authors = row['authors']
            if not original_authors:
                continue

            # Convert each author name
            fixed_authors = [invert_author_name(author) for author in original_authors]

            # Update if changes were made
            if fixed_authors != original_authors:
                # Create update statement
                update_query = f'''
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
                SET authors = {json.dumps(fixed_authors)}
                WHERE series_name = "{row['series_name']}"
                '''
                cache.client.query(update_query)
                print(f"✅ Updated {row['series_name']}: {original_authors} -> {fixed_authors}")
                updated_count += 1

        return updated_count

    except Exception as e:
        print(f"❌ Error fixing series authors: {e}")
        return 0

def fix_volume_authors():
    """Fix author names in volume_info table"""
    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not enabled")
        return 0

    try:
        # Get all volumes with authors
        query = '''
        SELECT series_name, volume_number, authors
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE ARRAY_LENGTH(authors) > 0
        '''
        result = cache.client.query(query)

        updated_count = 0
        for row in result:
            original_authors = row['authors']
            if not original_authors:
                continue

            # Convert each author name
            fixed_authors = [invert_author_name(author) for author in original_authors]

            # Update if changes were made
            if fixed_authors != original_authors:
                # Create update statement
                update_query = f'''
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                SET authors = {json.dumps(fixed_authors)}
                WHERE series_name = "{row['series_name']}" AND volume_number = {row['volume_number']}
                '''
                cache.client.query(update_query)
                print(f"✅ Updated {row['series_name']} Vol {row['volume_number']}: {original_authors} -> {fixed_authors}")
                updated_count += 1

        return updated_count

    except Exception as e:
        print(f"❌ Error fixing volume authors: {e}")
        return 0

if __name__ == "__main__":
    print("🔄 Fixing author names to inverted comma separated format...")

    series_updated = fix_series_authors()
    volume_updated = fix_volume_authors()

    print(f"\n🎯 Summary:")
    print(f"   ✅ Updated {series_updated} series")
    print(f"   ✅ Updated {volume_updated} volumes")
    print("\n✅ Author format fix completed")