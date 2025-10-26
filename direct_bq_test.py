#!/usr/bin/env python3
"""
Direct BigQuery table test
"""
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st

print("🔍 Direct BigQuery Table Test")
print("=" * 50)

try:
    # Get credentials from Streamlit secrets
    if hasattr(st, 'secrets') and 'vertex_ai' in st.secrets:
        vertex_secrets = st.secrets["vertex_ai"]
        credentials = service_account.Credentials.from_service_account_info({
            "type": vertex_secrets.get("type"),
            "project_id": vertex_secrets.get("project_id"),
            "private_key_id": vertex_secrets.get("private_key_id"),
            "private_key": vertex_secrets.get("private_key"),
            "client_email": vertex_secrets.get("client_email"),
            "client_id": vertex_secrets.get("client_id"),
            "auth_uri": vertex_secrets.get("auth_uri"),
            "token_uri": vertex_secrets.get("token_uri"),
            "auth_provider_x509_cert_url": vertex_secrets.get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": vertex_secrets.get("client_x509_cert_url")
        })
    else:
        print("❌ No Streamlit secrets found")
        exit(1)

    client = bigquery.Client(
        project="static-webbing-461904-c4",
        credentials=credentials
    )

    # Test query
    series_table_id = "static-webbing-461904-c4.manga_lookup_cache.series_info"

    print(f"🔍 Querying table: {series_table_id}")

    # Count total rows
    count_query = f"SELECT COUNT(*) as count FROM `{series_table_id}`"
    count_job = client.query(count_query)
    count_result = list(count_job)
    print(f"📊 Total rows: {count_result[0]['count']}")

    # Show first 10 rows
    sample_query = f"SELECT series_name, corrected_name, total_volumes FROM `{series_table_id}` LIMIT 10"
    sample_job = client.query(sample_query)
    sample_results = list(sample_job)

    print("📊 First 10 rows:")
    for i, row in enumerate(sample_results):
        print(f"   {i+1}. {row['series_name']} -> {row['corrected_name']} ({row['total_volumes']} vols)")

    # Test specific lookup
    print("\n🔍 Testing lookup for 'Attack on Titan'...")
    lookup_query = f"""
        SELECT * FROM `{series_table_id}`
        WHERE LOWER(series_name) = LOWER(@series_name)
        ORDER BY last_updated DESC
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("series_name", "STRING", "Attack on Titan")
        ]
    )

    lookup_job = client.query(lookup_query, job_config=job_config)
    lookup_results = list(lookup_job)

    if lookup_results:
        row = lookup_results[0]
        print(f"✅ FOUND: {row['series_name']} -> {row['corrected_name']} ({row['total_volumes']} vols)")
    else:
        print("❌ NOT FOUND")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test completed")