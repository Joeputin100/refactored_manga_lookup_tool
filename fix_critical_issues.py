#!/usr/bin/env python3
"""
Fix critical data quality issues - simplified version
"""

import sys
from bigquery_cache import BigQueryCache

def fix_critical_issues():
    """Fix only the most critical data quality issues"""
    cache = BigQueryCache()

    print("=== Fixing Critical Data Quality Issues ===\n")

    # 1. Fix series name variations (most critical)
    print("1. Fixing Series Name Variations...")

    # Standardize Haikyu!! variations
    haikyu_fix_query = """
    UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
    SET series_name = 'Haikyu!!'
    WHERE series_name IN ('Haikyuu!', 'Haikyuu!!', 'Haikyu!!')
    """

    try:
        cache.client.query(haikyu_fix_query).result()
        print("✅ Fixed Haikyu!! variations")
    except Exception as e:
        print(f"❌ Failed to fix Haikyu!! variations: {e}")

    # Standardize Crayon Shin-chan variations
    crayon_fix_query = """
    UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
    SET series_name = 'Crayon Shin-chan'
    WHERE series_name = 'Crayon Shinchan'
    """

    try:
        cache.client.query(crayon_fix_query).result()
        print("✅ Fixed Crayon Shin-chan variations")
    except Exception as e:
        print(f"❌ Failed to fix Crayon Shin-chan variations: {e}")

    # 2. Fix author name formatting for a few series first
    print("\n2. Fixing Author Name Formatting (Sample)...")

    # Get a sample of series with authors
    query = """
    SELECT series_name, authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE authors IS NOT NULL AND ARRAY_LENGTH(authors) > 0
    LIMIT 10
    """

    result = cache.client.query(query).result()

    for row in result:
        series_name = row['series_name']
        authors = row['authors']

        # Convert each author from "First Last" to "Last, First"
        fixed_authors = []
        for author in authors:
            if ' ' in author:
                parts = author.split(' ', 1)
                if len(parts) == 2:
                    fixed_author = f"{parts[1]}, {parts[0]}"
                    fixed_authors.append(fixed_author)
                else:
                    fixed_authors.append(author)
            else:
                fixed_authors.append(author)

        # Update the series with fixed authors
        if fixed_authors != authors:
            authors_str = ', '.join([f'"{a}"' for a in fixed_authors])
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
            SET authors = [{authors_str}]
            WHERE series_name = "{series_name}"
            """

            try:
                cache.client.query(update_query).result()
                print(f"✅ Fixed author format for: {series_name}")
            except Exception as e:
                print(f"❌ Failed to fix authors for {series_name}: {e}")

    print("\n=== Critical Fixes Complete ===")

if __name__ == "__main__":
    fix_critical_issues()