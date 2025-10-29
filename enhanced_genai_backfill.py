#!/usr/bin/env python3
"""Enhanced GenAI backfill with fallback strategy

Primary: gemini-2.5-flash-lite (fast, cost-effective)
Secondary: gemini-2.5-pro (reasoning, research for failed fields)
"""

from bigquery_cache import BigQueryCache
import google.generativeai as genai
from google.cloud import bigquery
import time
import json
import re

class EnhancedGenAIBackfill:
    def __init__(self):
        self.cache = BigQueryCache()
        if not self.cache.enabled:
            print('❌ BigQuery cache not enabled')
            return

        # Configure GenAI models
        self.primary_model = 'gemini-2.5-flash-lite'
        self.secondary_model = 'gemini-2.5-pro'

        print(f'🤖 GenAI Backfill initialized')
        print(f'   Primary: {self.primary_model} (fast processing)')
        print(f'   Secondary: {self.secondary_model} (reasoning fallback)')

    def get_metadata_with_fallback(self, series_name: str, volume_number: int):
        """Get metadata with primary model, fallback to secondary for failed fields"""

        # Try primary model first
        primary_result = self._call_genai_model(
            self.primary_model, series_name, volume_number
        )

        if not primary_result:
            print(f'❌ Primary model failed for {series_name} Vol {volume_number}')
            return None

        # Check for missing/invalid fields
        missing_fields = self._check_missing_fields(primary_result)

        if missing_fields:
            print(f'⚠️  Missing fields from primary model: {missing_fields}')

            # Use secondary model for missing fields
            secondary_result = self._call_genai_model(
                self.secondary_model, series_name, volume_number,
                focus_fields=missing_fields
            )

            if secondary_result:
                # Merge results
                merged_result = {**primary_result, **secondary_result}
                print(f'✅ Secondary model filled missing fields')
                return merged_result
            else:
                print(f'❌ Secondary model also failed')
                return primary_result

        return primary_result

    def _call_genai_model(self, model_name: str, series_name: str, volume_number: int, focus_fields=None):
        """Call GenAI model with appropriate prompt"""

        if focus_fields:
            prompt = self._create_focused_prompt(series_name, volume_number, focus_fields)
        else:
            prompt = self._create_comprehensive_prompt(series_name, volume_number)

        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)

            # Parse JSON response
            response_text = response.text.strip()
            response_text = response_text.removeprefix("```json")
            response_text = response_text.removesuffix("```")
            response_text = response_text.strip()

            book_data = json.loads(response_text)
            return book_data

        except Exception as e:
            print(f'❌ {model_name} failed: {e}')
            return None

    def _create_comprehensive_prompt(self, series_name: str, volume_number: int) -> str:
        """Create comprehensive prompt for primary model"""
        return f"""
        Provide comprehensive information for the manga "{series_name}" Volume {volume_number}.

        Return a JSON object with these exact fields:
        - "series_name": The official series name
        - "book_title": The specific title for this volume (e.g., "Volume 1: The Beginning")
        - "authors": List of author names (e.g., ["Eiichiro Oda", "Masashi Kishimoto"])
        - "msrp_cost": The retail price in USD (e.g., 9.99)
        - "isbn_13": The 13-digit ISBN (e.g., "9781421502670")
        - "publisher_name": The publisher (e.g., "VIZ Media", "Kodansha Comics")
        - "copyright_year": The copyright year (e.g., 2003)
        - "description": A brief description of the volume's content
        - "physical_description": Physical details like pages, dimensions (e.g., "192 pages, 5 x 7.5 inches")
        - "genres": List of genres (e.g., ["Action", "Adventure", "Fantasy"])
        - "number_of_extant_volumes": Total number of volumes in the series
        - "cover_image_url": URL to the cover image if available

        Important:
        - Return ONLY valid JSON, no additional text
        - Use exact field names as specified
        - If information is unavailable, use null or empty values
        - Prioritize English edition information
        - For manga, typical MSRP is $9.99-12.99 for standard volumes
        """

    def _create_focused_prompt(self, series_name: str, volume_number: int, focus_fields: list) -> str:
        """Create focused prompt for secondary model to research specific fields"""
        fields_str = ", ".join(focus_fields)

        return f"""
        Research and provide ONLY the following missing fields for "{series_name}" Volume {volume_number}:
        {fields_str}

        Please provide authoritative, well-researched information for these specific fields.
        Return ONLY a JSON object with these exact field names and their values.
        If you cannot find reliable information for a field, use null.

        Focus on finding accurate ISBN numbers, copyright years, publisher names, and descriptions.
        Use reliable sources like official publisher websites, ISBN databases, and authoritative manga references.
        """

    def _check_missing_fields(self, result: dict) -> list:
        """Check which fields are missing, null, or invalid"""
        required_fields = [
            'description', 'isbn_13', 'copyright_year', 'publisher_name'
        ]

        missing = []
        for field in required_fields:
            value = result.get(field)
            if not value or value == '' or value is None:
                missing.append(field)
            elif field == 'isbn_13' and not self._validate_isbn(value):
                missing.append(field)
            elif field == 'copyright_year' and not self._validate_year(value):
                missing.append(field)

        return missing

    def _validate_isbn(self, isbn: str) -> bool:
        """Validate ISBN-13 format"""
        if not isbn:
            return False

        # Remove any non-digit characters
        clean_isbn = re.sub(r'[^\d]', '', isbn)

        # Check if it's 13 digits
        if len(clean_isbn) != 13:
            return False

        # Basic format check (starts with 978 or 979)
        if not clean_isbn.startswith(('978', '979')):
            return False

        return True

    def _validate_year(self, year) -> bool:
        """Validate copyright year"""
        if not year:
            return False

        try:
            year_int = int(year)
            return 1900 <= year_int <= 2025
        except (ValueError, TypeError):
            return False

    def backfill_metadata(self):
        """Main backfill process with enhanced GenAI"""
        if not self.cache.enabled:
            return

        print('🔍 Finding volumes with missing metadata...')

        # Query for volumes missing any metadata
        query = '''
        SELECT series_name, volume_number, book_title
        FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
        WHERE description IS NULL OR description = ''
           OR isbn_13 IS NULL OR isbn_13 = ''
           OR copyright_year IS NULL
           OR publisher_name IS NULL OR publisher_name = ''
        LIMIT 5  # Process in small batches
        '''

        job = self.cache.client.query(query)
        volumes = list(job.result())

        print(f'📚 Found {len(volumes)} volumes with missing metadata')

        processed = 0

        for vol in volumes:
            series_name = vol['series_name']
            volume_number = vol['volume_number']

            print(f'🔍 Processing: {series_name} Vol {volume_number}')

            # Get metadata with fallback strategy
            try:
                result = self.get_metadata_with_fallback(series_name, volume_number)

                if result:
                    updates = []

                    # Build update query dynamically based on what we found
                    if 'description' in result and result['description']:
                        description = result['description'].replace("'", "''")  # Escape single quotes
                        updates.append(f"description = '{description}'")

                    if 'isbn_13' in result and result['isbn_13']:
                        isbn = result['isbn_13'].replace("'", "''")
                        updates.append(f"isbn_13 = '{isbn}'")

                    if 'copyright_year' in result and result['copyright_year']:
                        updates.append(f"copyright_year = {result['copyright_year']}")

                    if 'publisher_name' in result and result['publisher_name']:
                        publisher = result['publisher_name'].replace("'", "''")
                        updates.append(f"publisher_name = '{publisher}'")

                    if updates:
                        # Use parameterized query to avoid SQL injection and syntax errors
                        update_query = f'''
                        UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                        SET {', '.join(updates)}
                        WHERE series_name = @series_name AND volume_number = @volume_number
                        '''

                        job_config = bigquery.QueryJobConfig(
                            query_parameters=[
                                bigquery.ScalarQueryParameter('series_name', 'STRING', series_name),
                                bigquery.ScalarQueryParameter('volume_number', 'INT64', volume_number)
                            ]
                        )
                        update_job = self.cache.client.query(update_query, job_config=job_config)
                        update_job.result()  # Wait for completion

                        print(f'✅ Updated metadata for {series_name} Vol {volume_number}')
                        processed += 1
                    else:
                        print(f'❌ No metadata found for {series_name} Vol {volume_number}')
                else:
                    print(f'❌ No result from GenAI for {series_name} Vol {volume_number}')

            except Exception as e:
                print(f'⚠️ Error processing {series_name}: {e}')

            # Add small delay to avoid rate limiting
            time.sleep(2)

        print(f'🎯 Processed {processed} volumes')

if __name__ == '__main__':
    backfill = EnhancedGenAIBackfill()
    backfill.backfill_metadata()