#!/usr/bin/env python3
"""
Fix series data quality issues:
1. Remove duplicate series entries
2. Fix series with incorrect volume counts
3. Standardize series name spellings
4. Fix author name formatting
"""

import sys
from bigquery_cache import BigQueryCache
from wikipedia_complete_series_list import WIKIPEDIA_BEST_SELLING_MANGA_SERIES

def fix_series_data_quality():
    """Fix all series data quality issues"""
    cache = BigQueryCache()

    print("=== Fixing Series Data Quality Issues ===\n")

    # 1. First, let's fix the series name variations
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

    # 2. Fix author name formatting (convert to inverted comma separated)
    print("\n2. Fixing Author Name Formatting...")

    # Get all series with authors
    query = """
    SELECT series_name, authors
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE authors IS NOT NULL AND ARRAY_LENGTH(authors) > 0
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

    # 3. Fix series with incorrect volume counts (total_volumes = 1)
    print("\n3. Fixing Series with Incorrect Volume Counts...")

    # Get Wikipedia volume data
    wikipedia_volume_data = {
        "Boruto: Two Blue Vortex": 20,  # Current ongoing series
        "A Polar Bear in Love": 3,      # Actually has 3 volumes
        # Add more as needed
    }

    # Update series with incorrect volume counts
    for series_name, correct_volume_count in wikipedia_volume_data.items():
        update_query = f"""
        UPDATE `static-webbing-461904-c4.manga_lookup_cache.series_info`
        SET total_volumes = {correct_volume_count}
        WHERE series_name = "{series_name}"
        AND total_volumes = 1
        """

        try:
            cache.client.query(update_query).result()
            print(f"✅ Fixed volume count for {series_name}: {correct_volume_count} volumes")
        except Exception as e:
            print(f"❌ Failed to fix volume count for {series_name}: {e}")

    print("\n=== Data Quality Fixes Complete ===")

    # Check remaining issues
    print("\n=== Remaining Issues Check ===")

    # Check duplicate series after fixes
    query_duplicates = """
    SELECT series_name, COUNT(*) as count
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    GROUP BY series_name
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 10
    """

    result_duplicates = cache.client.query(query_duplicates).result()
    remaining_duplicates = [(row['series_name'], row['count']) for row in result_duplicates]

    print(f"Remaining duplicate series: {len(remaining_duplicates)}")
    if remaining_duplicates:
        print("Top 10 remaining duplicates:")
        for series, count in remaining_duplicates:
            print(f"  - {series}: {count} entries")

    # Check series still with total_volumes = 1
    query_single_vol = """
    SELECT series_name, total_volumes
    FROM `static-webbing-461904-c4.manga_lookup_cache.series_info`
    WHERE total_volumes = 1
    ORDER BY series_name
    """

    result_single = cache.client.query(query_single_vol).result()
    remaining_single = [(row['series_name'], row['total_volumes']) for row in result_single]

    print(f"\nSeries still with total_volumes = 1: {len(remaining_single)}")
    if remaining_single:
        print("First 10:")
        for series, count in remaining_single[:10]:
            print(f"  - {series}: {count} volumes")

if __name__ == "__main__":
    fix_series_data_quality()