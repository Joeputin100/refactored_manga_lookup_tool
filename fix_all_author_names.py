#!/usr/bin/env python3
"""
Fix all author names to inverted comma separated format
"""

import sys
from bigquery_cache import BigQueryCache

def fix_all_author_names():
    """Fix all author names to inverted comma separated format"""
    cache = BigQueryCache()

    print("=== Fixing All Author Names to Inverted Comma Format ===\n")

    # Get all series with authors
    query = """
    SELECT series_name, authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE authors IS NOT NULL AND ARRAY_LENGTH(authors) > 0
    """

    result = cache.client.query(query).result()
    total_series = sum(1 for _ in result)

    print(f"Found {total_series} series with authors to process")

    # Reset cursor to process again
    result = cache.client.query(query).result()

    fixed_count = 0
    error_count = 0

    for row in result:
        series_name = row['series_name']
        authors = row['authors']

        # Convert each author from "First Last" to "Last, First"
        fixed_authors = []
        needs_fix = False

        for author in authors:
            if ' ' in author and ', ' not in author:
                parts = author.split(' ', 1)
                if len(parts) == 2:
                    fixed_author = f"{parts[1]}, {parts[0]}"
                    fixed_authors.append(fixed_author)
                    needs_fix = True
                else:
                    fixed_authors.append(author)
            else:
                fixed_authors.append(author)

        # Update the series with fixed authors
        if needs_fix:
            authors_str = ', '.join([f'"{a}"' for a in fixed_authors])
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
            SET authors = [{authors_str}]
            WHERE series_name = "{series_name}"
            """

            try:
                cache.client.query(update_query).result()
                print(f"✅ Fixed author format for: {series_name}")
                print(f"   Before: {authors}")
                print(f"   After: {fixed_authors}")
                fixed_count += 1
            except Exception as e:
                print(f"❌ Failed to fix authors for {series_name}: {e}")
                error_count += 1

    print(f"\n=== Author Name Fix Complete ===")
    print(f"✅ Fixed: {fixed_count} series")
    print(f"❌ Errors: {error_count} series")

    # Verify the fix
    print(f"\n=== Verification ===")
    verification_query = """
    SELECT series_name, authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE authors IS NOT NULL AND ARRAY_LENGTH(authors) > 0
    LIMIT 10
    """

    verification_result = cache.client.query(verification_query).result()
    print("Sample of author names after fix:")
    for row in verification_result:
        print(f"  - {row['series_name']}: {row['authors']}")

if __name__ == "__main__":
    fix_all_author_names()