#!/usr/bin/env python3
"""
Reimplement series range caching feature - Fixed version
"""

def reimplement_series_range_caching():
    """Add series range caching to the Streamlit app"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the get_volume_info_from_bigquery function
    volume_function_start = 'def get_volume_info_from_bigquery(series_name: str, volume_number: int):'
    volume_function_end = 'def generate_marc_filename(books: list) -> str:'

    start_pos = content.find(volume_function_start)
    end_pos = content.find(volume_function_end, start_pos)

    if start_pos == -1 or end_pos == -1:
        print("❌ Could not find volume info function boundaries")
        return False

    # Create the enhanced function with series range caching
    enhanced_functions = '''def get_volume_info_from_bigquery(series_name: str, volume_number: int):
    """Get volume information from BigQuery cache"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Query for volume info
        query = f"""SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info` WHERE LOWER(series_name) = LOWER(\"{series_name}\") AND volume_number = {volume_number}"""

        print(f"🔍 BigQuery volume query: {query}")
        result = cache.client.query(query).result()

        row_count = 0
        for row in result:
            row_count += 1
            print(f"✅ Found volume in BigQuery: {row.series_name} Vol {row.volume_number}")
            return {
                "series_name": row.series_name,
                "volume_number": row.volume_number,
                "book_title": row.book_title if hasattr(row, 'book_title') else f"{row.series_name} Vol. {row.volume_number}",
                "authors": row.authors if hasattr(row, 'authors') else [],
                "msrp_cost": float(row.msrp_cost) if hasattr(row, 'msrp_cost') and row.msrp_cost else None,
                "isbn_13": row.isbn_13 if hasattr(row, 'isbn_13') else None,
                "publisher_name": row.publisher_name if hasattr(row, 'publisher_name') else None,
                "copyright_year": int(row.copyright_year) if hasattr(row, 'copyright_year') and row.copyright_year else None,
                "description": row.description if hasattr(row, 'description') else None,
                "physical_description": row.physical_description if hasattr(row, 'physical_description') else None,
                "genres": row.genres if hasattr(row, 'genres') else [],
                "cover_image_url": row.cover_image_url if hasattr(row, 'cover_image_url') else None
            }

        if row_count == 0:
            print(f"❌ No volume found in BigQuery for: {series_name} Vol {volume_number}")

    except Exception as e:
        print(f"❌ BigQuery volume query failed: {e}")
    return None

def get_volume_range_from_bigquery(series_name: str, volume_numbers: list):
    """Get multiple volume information from BigQuery cache in a single request"""
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        if not volume_numbers:
            return []

        # Create IN clause for volume numbers
        volume_list = ", ".join(str(v) for v in volume_numbers)

        # Query for multiple volumes in a single request
        query = f"""SELECT * FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                   WHERE LOWER(series_name) = LOWER(\"{series_name}\")
                   AND volume_number IN ({volume_list})"""

        print(f"🔍 BigQuery volume range query: {query}")
        result = cache.client.query(query).result()

        volumes = []
        row_count = 0
        for row in result:
            row_count += 1
            print(f"✅ Found volume in BigQuery: {row.series_name} Vol {row.volume_number}")
            volumes.append({
                "series_name": row.series_name,
                "volume_number": row.volume_number,
                "book_title": row.book_title if hasattr(row, 'book_title') else f"{row.series_name} Vol. {row.volume_number}",
                "authors": row.authors if hasattr(row, 'authors') else [],
                "msrp_cost": float(row.msrp_cost) if hasattr(row, 'msrp_cost') and row.msrp_cost else None,
                "isbn_13": row.isbn_13 if hasattr(row, 'isbn_13') else None,
                "publisher_name": row.publisher_name if hasattr(row, 'publisher_name') else None,
                "copyright_year": int(row.copyright_year) if hasattr(row, 'copyright_year') and row.copyright_year else None,
                "description": row.description if hasattr(row, 'description') else None,
                "physical_description": row.physical_description if hasattr(row, 'physical_description') else None,
                "genres": row.genres if hasattr(row, 'genres') else [],
                "cover_image_url": row.cover_image_url if hasattr(row, 'cover_image_url') else None
            })

        print(f"✅ Found {row_count} volumes in BigQuery for series: {series_name}")
        return volumes

    except Exception as e:
        print(f"❌ BigQuery volume range query failed: {e}")
    return []

'''

    # Replace the current function with the enhanced version
    current_function = content[start_pos:end_pos]
    content = content.replace(current_function, enhanced_functions)

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Series range caching feature reimplemented successfully")
    return True

if __name__ == "__main__":
    reimplement_series_range_caching()