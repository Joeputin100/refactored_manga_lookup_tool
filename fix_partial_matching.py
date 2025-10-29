#!/usr/bin/env python3
"""
Fix partial series name matching in BigQuery cache
"""

def fix_partial_matching():
    """Add partial matching to BigQuery cache function"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the get_series_info_from_bigquery function
    if 'def get_series_info_from_bigquery(series_name: str):' in content:
        print("✅ Found get_series_info_from_bigquery function")

        # Replace the function with enhanced version that includes partial matching
        new_function = '''def get_series_info_from_bigquery(series_name: str):
    """Get series information from BigQuery cache with partial matching"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # First try exact case-insensitive match
        query = f"""SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) = LOWER(\"{series_name}\")"""

        print(f"🔍 BigQuery query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            print(f"✅ Found series in BigQuery (exact match): {row.series_name}")
            return {
                "corrected_series_name": row.series_name,
                "authors": row.authors if hasattr(row, 'authors') else [],
                "extant_volumes": row.total_volumes if hasattr(row, 'total_volumes') else 0,
                "summary": row.summary if hasattr(row, 'summary') else "",
                "cover_image_url": row.cover_image_url if hasattr(row, 'cover_image_url') else None,
                "genres": row.genres if hasattr(row, 'genres') else [],
                "publisher": row.publisher if hasattr(row, 'publisher') else "",
                "status": row.status if hasattr(row, 'status') else "",
                "alternative_titles": row.alternative_titles if hasattr(row, 'alternative_titles') else [],
                "spinoff_series": row.spinoff_series if hasattr(row, 'spinoff_series') else [],
                "adaptations": row.adaptations if hasattr(row, 'adaptations') else []
            }

        # If exact match fails, try partial matching for common patterns
        if row_count == 0:
            print(f"❌ No exact match found for: {series_name}, trying partial matching...")

            # Try partial matching for common patterns like "Vigilantes" -> "My Hero Academia: Vigilantes"
            partial_query = f"""SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.series_info` WHERE LOWER(series_name) LIKE LOWER(\"%{series_name}%\")"""

            print(f"🔍 BigQuery partial query: {partial_query}")
            partial_result = cache.client.query(partial_query).result()

            partial_count = 0
            best_match = None
            for row in partial_result:
                partial_count += 1
                print(f"✅ Found series in BigQuery (partial match): {row.series_name}")
                # Return the first partial match (usually the best one)
                if not best_match:
                    best_match = row

            if best_match:
                return {
                    "corrected_series_name": best_match.series_name,
                    "authors": best_match.authors if hasattr(best_match, 'authors') else [],
                    "extant_volumes": best_match.total_volumes if hasattr(best_match, 'total_volumes') else 0,
                    "summary": best_match.summary if hasattr(best_match, 'summary') else "",
                    "cover_image_url": best_match.cover_image_url if hasattr(best_match, 'cover_image_url') else None,
                    "genres": best_match.genres if hasattr(best_match, 'genres') else [],
                    "publisher": best_match.publisher if hasattr(best_match, 'publisher') else "",
                    "status": best_match.status if hasattr(best_match, 'status') else "",
                    "alternative_titles": best_match.alternative_titles if hasattr(best_match, 'alternative_titles') else [],
                    "spinoff_series": best_match.spinoff_series if hasattr(best_match, 'spinoff_series') else [],
                    "adaptations": best_match.adaptations if hasattr(best_match, 'adaptations') else []
                }
            else:
                print(f"❌ No series found in BigQuery for: {series_name}")

    except Exception as e:
        print(f"❌ BigQuery cache query failed: {e}")
    return None
'''

        # Replace the old function with the new one
        old_function_start = content.find('def get_series_info_from_bigquery(series_name: str):')
        old_function_end = content.find('def get_volume_info_from_bigquery', old_function_start)

        if old_function_start != -1 and old_function_end != -1:
            old_function = content[old_function_start:old_function_end]
            content = content.replace(old_function, new_function)
            print("✅ Successfully updated BigQuery cache function with partial matching")
        else:
            print("❌ Could not find function boundaries")
            return False
    else:
        print("❌ Could not find get_series_info_from_bigquery function")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Successfully added partial matching to BigQuery cache")
    return True

if __name__ == "__main__":
    fix_partial_matching()