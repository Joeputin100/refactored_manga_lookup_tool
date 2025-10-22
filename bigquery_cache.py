#!/usr/bin/env python3
"""
BigQuery Cache for Manga Lookup Tool

Provides caching for series and volume information using Google BigQuery.
This will improve performance and reduce API calls.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    print("⚠️ BigQuery not available - caching disabled")


class BigQueryCache:
    """BigQuery-based cache for manga series and volume information"""

    def __init__(self):
        if not BIGQUERY_AVAILABLE:
            self.enabled = False
            return

        try:
            # Get credentials from Streamlit secrets or environment
            import streamlit as st
            if hasattr(st, 'secrets') and 'vertex_ai' in st.secrets:
                vertex_secrets = st.secrets["vertex_ai"]
                self.credentials = service_account.Credentials.from_service_account_info({
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
                # Fallback to environment variables
                self.credentials = None

            self.client = bigquery.Client(
                project="static-webbing-461904-c4",
                credentials=self.credentials
            )
            self.enabled = True
            self.dataset_id = "manga_lookup_cache"
            self.series_table_id = f"{self.dataset_id}.series_info"
            self.volumes_table_id = f"{self.dataset_id}.volume_info"

            # Initialize tables if they don't exist
            self._initialize_tables()

        except Exception as e:
            print(f"❌ BigQuery initialization failed: {e}")
            self.enabled = False

    def _initialize_tables(self):
        """Initialize BigQuery tables if they don't exist"""
        if not self.enabled:
            return

        try:
            # Create dataset if it doesn't exist
            dataset = bigquery.Dataset(f"{self.client.project}.{self.dataset_id}")
            dataset.location = "US"
            self.client.create_dataset(dataset, exists_ok=True)

            # Create series info table
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

            # Create volume info table
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

            print("✅ BigQuery tables initialized")

        except Exception as e:
            print(f"❌ BigQuery table initialization failed: {e}")

    def get_series_info(self, series_name: str) -> Optional[Dict]:
        """Get series information from cache"""
        if not self.enabled:
            return None

        try:
            query = f"""
                SELECT * FROM `{self.series_table_id}`
                WHERE series_name = @series_name
                ORDER BY last_updated DESC
                LIMIT 1
            """
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
                "last_updated": datetime.utcnow(),
                "api_source": api_source,
            }

            errors = self.client.insert_rows_json(self.series_table_id, [row])
            if errors:
                print(f"❌ BigQuery series insert failed: {errors}")
            else:
                print(f"✅ Cached series info for: {series_name}")

        except Exception as e:
            print(f"❌ BigQuery series cache failed: {e}")

    def get_volume_info(self, series_name: str, volume_number: int) -> Optional[Dict]:
        """Get volume information from cache"""
        if not self.enabled:
            return None

        try:
            query = f"""
                SELECT * FROM `{self.volumes_table_id}`
                WHERE series_name = @series_name AND volume_number = @volume_number
                ORDER BY last_updated DESC
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("series_name", "STRING", series_name),
                    bigquery.ScalarQueryParameter("volume_number", "INT64", volume_number)
                ]
            )
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job)

            if results:
                row = results[0]
                return {
                    "series_name": row.get("series_name"),
                    "volume_number": row.get("volume_number"),
                    "book_title": row.get("book_title"),
                    "authors": list(row.get("authors", [])),
                    "isbn_13": row.get("isbn_13"),
                    "publisher_name": row.get("publisher_name"),
                    "copyright_year": row.get("copyright_year"),
                    "description": row.get("description"),
                    "physical_description": row.get("physical_description"),
                    "genres": list(row.get("genres", [])),
                    "msrp_cost": row.get("msrp_cost"),
                    "cover_image_url": row.get("cover_image_url"),
                    "cached": True,
                    "cache_source": "bigquery"
                }
        except Exception as e:
            print(f"❌ BigQuery volume query failed: {e}")

        return None

    def cache_volume_info(self, series_name: str, volume_number: int, volume_info: Dict, api_source: str = "vertex_ai"):
        """Cache volume information"""
        if not self.enabled:
            return

        try:
            # Prepare data for insertion
            row = {
                "series_name": series_name,
                "volume_number": volume_number,
                "book_title": volume_info.get("book_title", f"{series_name} Volume {volume_number}"),
                "authors": volume_info.get("authors", []),
                "isbn_13": volume_info.get("isbn_13"),
                "publisher_name": volume_info.get("publisher_name"),
                "copyright_year": volume_info.get("copyright_year"),
                "description": volume_info.get("description", ""),
                "physical_description": volume_info.get("physical_description", ""),
                "genres": volume_info.get("genres", []),
                "msrp_cost": volume_info.get("msrp_cost"),
                "cover_image_url": volume_info.get("cover_image_url"),
                "last_updated": datetime.utcnow(),
                "api_source": api_source,
            }

            errors = self.client.insert_rows_json(self.volumes_table_id, [row])
            if errors:
                print(f"❌ BigQuery volume insert failed: {errors}")
            else:
                print(f"✅ Cached volume info for: {series_name} Vol {volume_number}")

        except Exception as e:
            print(f"❌ BigQuery volume cache failed: {e}")

    def pre_seed_popular_titles(self):
        """Pre-seed the cache with popular manga titles"""
        if not self.enabled:
            return

        popular_series = [
            {
                "series_name": "Attack on Titan",
                "corrected_name": "Attack on Titan",
                "authors": ["Hajime Isayama"],
                "total_volumes": 34,
                "summary": "In a world where humanity lives inside cities surrounded by enormous walls due to the Titans, gigantic humanoid creatures who devour humans seemingly without reason.",
                "spinoff_series": ["Attack on Titan: Before the Fall", "Attack on Titan: No Regrets"],
                "alternate_editions": ["Colossal Edition", "Omnibus Edition"],
                "cover_image_url": "https://books.google.com/books/content?id=example",
                "api_source": "pre_seeded"
            },
            {
                "series_name": "One Piece",
                "corrected_name": "One Piece",
                "authors": ["Eiichiro Oda"],
                "total_volumes": 107,
                "summary": "Monkey D. Luffy and his pirate crew explore the Grand Line in search of the world's ultimate treasure known as 'One Piece' in order to become the next Pirate King.",
                "spinoff_series": [],
                "alternate_editions": ["Omnibus Edition"],
                "cover_image_url": "https://books.google.com/books/content?id=example",
                "api_source": "pre_seeded"
            },
            {
                "series_name": "Naruto",
                "corrected_name": "Naruto",
                "authors": ["Masashi Kishimoto"],
                "total_volumes": 72,
                "summary": "Naruto Uzumaki, a young ninja who seeks recognition from his peers and dreams of becoming the Hokage, the leader of his village.",
                "spinoff_series": ["Boruto: Naruto Next Generations"],
                "alternate_editions": ["3-in-1 Edition"],
                "cover_image_url": "https://books.google.com/books/content?id=example",
                "api_source": "pre_seeded"
            }
        ]

        for series in popular_series:
            try:
                series["last_updated"] = datetime.utcnow()
                errors = self.client.insert_rows_json(self.series_table_id, [series])
                if errors:
                    print(f"❌ Failed to pre-seed {series['series_name']}: {errors}")
                else:
                    print(f"✅ Pre-seeded: {series['series_name']}")
            except Exception as e:
                print(f"❌ Pre-seeding failed for {series['series_name']}: {e}")


def test_bigquery_cache():
    """Test the BigQuery cache functionality"""
    print("🔧 Testing BigQuery Cache...")

    cache = BigQueryCache()
    if not cache.enabled:
        print("❌ BigQuery cache not available")
        return

    # Test series caching
    test_series = {
        "corrected_series_name": "Attack on Titan",
        "authors": ["Hajime Isayama"],
        "extant_volumes": 34,
        "summary": "Test summary",
        "spinoff_series": ["Before the Fall"],
        "alternate_editions": ["Colossal Edition"],
        "cover_image_url": "https://example.com/cover.jpg"
    }

    cache.cache_series_info("Attack on Titan", test_series)

    # Test retrieval
    cached_info = cache.get_series_info("Attack on Titan")
    if cached_info:
        print("✅ Series caching working")
    else:
        print("❌ Series caching failed")

    # Pre-seed popular titles
    cache.pre_seed_popular_titles()


if __name__ == "__main__":
    test_bigquery_cache()