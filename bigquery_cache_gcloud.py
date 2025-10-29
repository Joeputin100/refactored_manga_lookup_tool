#!/usr/bin/env python3
"""
BigQuery Cache with gcloud Authentication

Modified version that uses gcloud authentication instead of Streamlit secrets
for running as standalone scripts on EC2.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List

try:
    from google.cloud import bigquery
    from google.auth import default
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    print("⚠️ BigQuery not available - caching disabled")


class BigQueryCacheGCloud:
    """BigQuery-based cache using gcloud authentication"""

    def __init__(self):
        if not BIGQUERY_AVAILABLE:
            self.enabled = False
            return

        try:
            # Use gcloud default credentials
            credentials, project = default()

            if not project:
                project = "static-webbing-461904-c4"
                print(f"⚠️ No project detected, using default: {project}")

            self.client = bigquery.Client(
                project=project,
                credentials=credentials
            )

            # Test if we have basic permissions
            try:
                # Simple test query to check permissions
                query = "SELECT 1 as test"
                query_job = self.client.query(query)
                results = list(query_job)
                self.enabled = True
                print(f"✅ BigQuery permissions verified for project: {project}")
            except Exception as perm_error:
                print(f"⚠️ BigQuery permissions issue: {perm_error}")
                print("⚠️ BigQuery caching disabled - gcloud account needs permissions")
                self.enabled = False
                return

            self.dataset_id = "manga_lookup_cache"
            self.series_table_id = f"{self.client.project}.{self.dataset_id}.series_info"
            self.volumes_table_id = f"{self.client.project}.{self.dataset_id}.volume_info"

            # Initialize tables if they don't exist
            self._initialize_tables()

        except Exception as e:
            print(f"❌ BigQuery initialization failed: {e}")
            self.enabled = False

    def _validate_table_name(self, table_name: str) -> bool:
        """Validate table name to prevent SQL injection"""
        import re
        # Allow only alphanumeric, underscores, dots, and dashes
        pattern = r'^[a-zA-Z0-9_.-]+$'
        return bool(re.match(pattern, table_name))

    def _initialize_tables(self):
        """Initialize BigQuery tables if they don't exist"""
        if not self.enabled:
            return

        # Validate table names
        if not self._validate_table_name(self.dataset_id):
            print(f"❌ Invalid dataset name: {self.dataset_id}")
            self.enabled = False
            return

        try:
            # Check if dataset exists first
            try:
                self.client.get_dataset(self.dataset_id)
                print(f"✅ BigQuery dataset '{self.dataset_id}' exists")
            except Exception:
                # Dataset doesn't exist, try to create it
                try:
                    dataset = bigquery.Dataset(f"{self.client.project}.{self.dataset_id}")
                    dataset.location = "US"
                    self.client.create_dataset(dataset, exists_ok=True)
                    print(f"✅ Created BigQuery dataset: {self.dataset_id}")
                except Exception as create_error:
                    print(f"⚠️ Cannot create dataset (permission issue): {create_error}")
                    print("⚠️ BigQuery caching disabled - dataset creation permission required")
                    self.enabled = False
                    return

            # Create series info table if it doesn't exist
            try:
                self.client.get_table(self.series_table_id)
                print(f"✅ Series table '{self.series_table_id}' exists")
            except Exception:
                try:
                    series_schema = [
                        bigquery.SchemaField("series_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("corrected_name", "STRING"),
                        bigquery.SchemaField("authors", "STRING", mode="REPEATED"),
                        bigquery.SchemaField("total_volumes", "INTEGER"),
                        bigquery.SchemaField("summary", "STRING"),
                        bigquery.SchemaField("spinoff_series", "STRING", mode="REPEATED"),
                        bigquery.SchemaField("alternate_editions", "STRING", mode="REPEATED"),
                        bigquery.SchemaField("cover_image_url", "STRING"),
                        bigquery.SchemaField("last_updated", "TIMESTAMP"),
                        bigquery.SchemaField("api_source", "STRING"),
                    ]
                    series_table = bigquery.Table(self.series_table_id, schema=series_schema)
                    self.client.create_table(series_table, exists_ok=True)
                    print(f"✅ Created series table: {self.series_table_id}")
                except Exception as table_error:
                    print(f"❌ Cannot create series table: {table_error}")
                    print("⚠️ BigQuery caching disabled - table creation permission required")
                    self.enabled = False
                    return

            # Create volume info table if it doesn't exist
            try:
                self.client.get_table(self.volumes_table_id)
                print(f"✅ Volume table '{self.volumes_table_id}' exists")
            except Exception:
                try:
                    volume_schema = [
                        bigquery.SchemaField("series_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("volume_number", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("book_title", "STRING"),
                        bigquery.SchemaField("authors", "STRING", mode="REPEATED"),
                        bigquery.SchemaField("isbn_13", "STRING"),
                        bigquery.SchemaField("publisher_name", "STRING"),
                        bigquery.SchemaField("copyright_year", "INTEGER"),
                        bigquery.SchemaField("description", "STRING"),
                        bigquery.SchemaField("physical_description", "STRING"),
                        bigquery.SchemaField("genres", "STRING", mode="REPEATED"),
                        bigquery.SchemaField("msrp_cost", "FLOAT"),
                        bigquery.SchemaField("cover_image_url", "STRING"),
                        bigquery.SchemaField("last_updated", "TIMESTAMP"),
                        bigquery.SchemaField("api_source", "STRING"),
                    ]
                    volume_table = bigquery.Table(self.volumes_table_id, schema=volume_schema)
                    self.client.create_table(volume_table, exists_ok=True)
                    print(f"✅ Created volume table: {self.volumes_table_id}")
                except Exception as table_error:
                    print(f"❌ Cannot create volume table: {table_error}")
                    print("⚠️ BigQuery caching disabled - table creation permission required")
                    self.enabled = False
                    return

        except Exception as e:
            print(f"❌ BigQuery table initialization failed: {e}")
            self.enabled = False

    # [Rest of the methods remain the same as the original BigQueryCache]
    # For brevity, I'm including the key methods needed for cover fetching

    def get_series_info(self, series_name: str) -> Optional[Dict]:
        """Get series information from cache"""
        if not self.enabled:
            return None

        # Validate table name
        if not self._validate_table_name(self.dataset_id):
            print(f"❌ Invalid dataset name: {self.dataset_id}")
            return None

        try:
            # Use safer query construction with table name validation
            query = """
                SELECT * FROM `{project}.{dataset}.series_info`
                WHERE LOWER(series_name) = LOWER(@series_name)
                ORDER BY last_updated DESC
                LIMIT 1
            """.format(
                project=self.client.project,
                dataset=self.dataset_id
            )
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("series_name", "STRING", series_name)
                ]
            )
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job)

            if results:
                row = results[0]
                return {
                    "corrected_series_name": row.get("corrected_name") or series_name,
                    "authors": list(row.get("authors", [])),
                    "extant_volumes": row.get("total_volumes", 0),
                    "summary": row.get("summary", ""),
                    "spinoff_series": list(row.get("spinoff_series", [])),
                    "alternate_editions": list(row.get("alternate_editions", [])),
                    "cover_image_url": row.get("cover_image_url"),
                    "cached": True,
                    "cache_source": "bigquery"
                }
        except Exception as e:
            print(f"❌ BigQuery series query failed: {e}")

        return None

    def cache_series_info(self, series_name: str, series_info: Dict, api_source: str = "vertex_ai"):
        """Cache series information"""
        if not self.enabled:
            return

        try:
            # Prepare data for insertion
            row = {
                "series_name": series_name,
                "corrected_name": series_info.get("corrected_series_name", series_name),
                "authors": series_info.get("authors", []),
                "total_volumes": series_info.get("extant_volumes", 0),
                "summary": series_info.get("summary", ""),
                "spinoff_series": series_info.get("spinoff_series", []),
                "alternate_editions": series_info.get("alternate_editions", []),
                "cover_image_url": series_info.get("cover_image_url"),
                "genres": series_info.get("genres", []),
                "publisher": series_info.get("publisher", ""),
                "status": series_info.get("status", ""),
                "alternative_titles": series_info.get("alternative_titles", []),
                "adaptations": series_info.get("adaptations", []),
                "last_updated": datetime.utcnow().isoformat(),
                "api_source": api_source,
            }

            errors = self.client.insert_rows_json(self.series_table_id, [row])
            if errors:
                print(f"❌ BigQuery series insert failed: {errors}")
            else:
                print(f"✅ Cached series info for: {series_name}")

        except Exception as e:
            print(f"❌ BigQuery series cache failed: {e}")


def test_bigquery_gcloud():
    """Test the gcloud-based BigQuery cache"""
    print("🔧 Testing BigQuery Cache with gcloud authentication...")

    cache = BigQueryCacheGCloud()
    if not cache.enabled:
        print("❌ BigQuery cache not available")
        return

    print("✅ BigQuery cache initialized successfully with gcloud authentication")


if __name__ == "__main__":
    test_bigquery_gcloud()