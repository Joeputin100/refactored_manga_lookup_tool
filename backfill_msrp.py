import sys
from manga_lookup import GoogleBooksAPI
from bigquery_cache import BigQueryCache

def backfill_msrp():
    """
    Finds volumes with missing MSRP in BigQuery and updates them
    with data from Google Books.
    """
    print("Starting MSRP backfill process...")
    cache = BigQueryCache()
    google_books_api = GoogleBooksAPI()

    # Query for volumes with missing MSRP
    query = """
    SELECT series_name, volume_number, isbn_13
    FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
    WHERE msrp_cost IS NULL OR msrp_cost = 0
    """
    print("Querying for volumes with missing MSRP...")
    results = cache.client.query(query).result()

    for row in results:
        print(f"Processing {row.series_name} Vol. {row.volume_number}...")
        msrp = None
        if row.isbn_13:
            msrp = google_books_api.get_msrp_by_isbn(row.isbn_13)

        if not msrp:
            msrp = google_books_api.get_msrp_by_title_and_volume(row.series_name, row.volume_number)

        if msrp:
            print(f"Found MSRP: ${msrp}. Updating BigQuery...")
            update_query = f"""
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            SET msrp_cost = {msrp}
            WHERE series_name = "{row.series_name}"
            AND volume_number = {row.volume_number}
            """
            cache.client.query(update_query).result()
            print("Update complete.")
        else:
            print("Could not find MSRP.")

    print("MSRP backfill process complete.")

if __name__ == "__main__":
    backfill_msrp()