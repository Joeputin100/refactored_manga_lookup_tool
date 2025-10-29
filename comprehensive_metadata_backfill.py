#!/usr/bin/env python3
"""
Comprehensive Metadata Backfill Script

This script identifies volumes with missing metadata and backfills them
using the enhanced Vertex AI API with Gemini 2.5 models.
"""

import time
import re
from typing import List, Dict, Any
from bigquery_cache import BigQueryCache
from vertexai_enhanced import EnhancedVertexAIAPI
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter


class MetadataBackfill:
    """Handles comprehensive metadata backfill operations"""

    def __init__(self):
        self.cache = BigQueryCache()
        self.vertex_api = EnhancedVertexAIAPI()

    def get_volumes_with_missing_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all volumes with missing metadata, categorized by field"""
        if not self.cache.enabled:
            print('❌ BigQuery cache not enabled')
            return {}

        print('🔍 Identifying volumes with missing metadata...')

        missing_volumes = {
            'descriptions': [],
            'isbns': [],
            'copyright_years': [],
            'publishers': [],
            'cover_images': []
        }

        # Query for volumes missing descriptions
        desc_query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE description IS NULL OR description = ''
        '''
        desc_result = self.cache.client.query(desc_query)
        missing_volumes['descriptions'] = list(desc_result)

        # Query for volumes missing ISBNs
        isbn_query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE isbn_13 IS NULL OR isbn_13 = ''
        '''
        isbn_result = self.cache.client.query(isbn_query)
        missing_volumes['isbns'] = list(isbn_result)

        # Query for volumes missing copyright years
        copyright_query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE copyright_year IS NULL OR copyright_year = 0
        '''
        copyright_result = self.cache.client.query(copyright_query)
        missing_volumes['copyright_years'] = list(copyright_result)

        # Query for volumes missing publishers
        publisher_query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE publisher_name IS NULL OR publisher_name = ''
        '''
        publisher_result = self.cache.client.query(publisher_query)
        missing_volumes['publishers'] = list(publisher_result)

        # Query for volumes missing cover images
        cover_query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE cover_image_url IS NULL OR cover_image_url = ''
        '''
        cover_result = self.cache.client.query(cover_query)
        missing_volumes['cover_images'] = list(cover_result)

        # Print summary
        print(f"📊 Missing metadata summary:")
        print(f"   - Descriptions: {len(missing_volumes['descriptions'])} volumes")
        print(f"   - ISBNs: {len(missing_volumes['isbns'])} volumes")
        print(f"   - Copyright years: {len(missing_volumes['copyright_years'])} volumes")
        print(f"   - Publishers: {len(missing_volumes['publishers'])} volumes")
        print(f"   - Cover images: {len(missing_volumes['cover_images'])} volumes")

        return missing_volumes

    def backfill_volume_metadata(self, series_name: str, volume_number: int) -> Dict[str, Any]:
        """Backfill metadata for a specific volume"""
        try:
            print(f"🔄 Backfilling metadata for {series_name} Vol {volume_number}...")

            # Get comprehensive book info from Vertex AI
            book_info = self.vertex_api.get_book_info(series_name, volume_number)
            if not book_info:
                print(f"❌ Failed to get metadata for {series_name} Vol {volume_number}")
                return {}

            # Prepare update data
            update_data = {}

            if book_info.get('description'):
                update_data['description'] = book_info['description']

            if book_info.get('isbn_13'):
                update_data['isbn_13'] = book_info['isbn_13']

            if book_info.get('copyright_year'):
                update_data['copyright_year'] = book_info['copyright_year']

            if book_info.get('publisher_name'):
                update_data['publisher_name'] = book_info['publisher_name']

            # Update the database
            if update_data:
                self._update_volume_metadata(series_name, volume_number, update_data)
                print(f"✅ Updated {len(update_data)} fields for {series_name} Vol {volume_number}")
                return update_data
            else:
                print(f"⚠️ No valid metadata found for {series_name} Vol {volume_number}")
                return {}

        except Exception as e:
            print(f"❌ Error backfilling {series_name} Vol {volume_number}: {e}")
            return {}

    def _update_volume_metadata(self, series_name: str, volume_number: int, update_data: Dict[str, Any]):
        """Update volume metadata in BigQuery"""
        try:
            set_clauses = []
            params = []
            param_count = 0

            for field, value in update_data.items():
                if field == 'copyright_year' and isinstance(value, str):
                    # Extract year from string if needed
                    year_match = re.search(r'\b(19|20)\d{2}\b', value)
                    if year_match:
                        value = int(year_match.group())
                    else:
                        continue

                if field in ['description', 'isbn_13', 'publisher_name']:
                    set_clauses.append(f'{field} = @param{param_count}')
                    params.append(ScalarQueryParameter(f'param{param_count}', 'STRING', str(value)))
                    param_count += 1
                elif field == 'copyright_year' and isinstance(value, int):
                    set_clauses.append(f'{field} = @param{param_count}')
                    params.append(ScalarQueryParameter(f'param{param_count}', 'INT64', value))
                    param_count += 1

            if not set_clauses:
                return

            query = f'''
            UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            SET {', '.join(set_clauses)}
            WHERE series_name = @series_name AND volume_number = @volume_number
            '''

            params.extend([
                ScalarQueryParameter('series_name', 'STRING', series_name),
                ScalarQueryParameter('volume_number', 'INT64', volume_number)
            ])

            # Execute update with proper QueryJobConfig
            job_config = QueryJobConfig(
                query_parameters=params
            )
            job = self.cache.client.query(query, job_config=job_config)
            job.result()  # Wait for completion

        except Exception as e:
            print(f"❌ Database update failed for {series_name} Vol {volume_number}: {e}")

    def batch_backfill_metadata(self, missing_volumes: Dict[str, List[Dict[str, Any]]], max_volumes: int = 50):
        """Batch backfill metadata for multiple volumes"""
        print(f"🚀 Starting batch metadata backfill (max {max_volumes} volumes)...")

        # Combine all volumes that need backfilling
        all_volumes = set()
        for category, volumes in missing_volumes.items():
            for volume in volumes:
                key = (volume['series_name'], volume['volume_number'])
                all_volumes.add(key)

        # Convert to list and limit
        volumes_to_process = list(all_volumes)[:max_volumes]

        print(f"📚 Processing {len(volumes_to_process)} volumes...")

        success_count = 0
        for series_name, volume_number in volumes_to_process:
            result = self.backfill_volume_metadata(series_name, volume_number)
            if result:
                success_count += 1

            # Rate limiting
            time.sleep(2)

        print(f"🎯 Batch backfill complete: {success_count}/{len(volumes_to_process)} volumes updated")

    def run_comprehensive_backfill(self, max_volumes: int = 100):
        """Run comprehensive metadata backfill"""
        print("🚀 Starting Comprehensive Metadata Backfill")
        print("=" * 50)

        # Get volumes with missing metadata
        missing_volumes = self.get_volumes_with_missing_metadata()

        if not any(len(volumes) > 0 for volumes in missing_volumes.values()):
            print("✅ No missing metadata found!")
            return

        # Run batch backfill
        self.batch_backfill_metadata(missing_volumes, max_volumes)

        print("\n✅ Comprehensive metadata backfill completed!")


def main():
    """Main function for metadata backfill"""
    backfill = MetadataBackfill()

    # Run comprehensive backfill (limit to 50 volumes for testing)
    backfill.run_comprehensive_backfill(max_volumes=50)


if __name__ == "__main__":
    main()