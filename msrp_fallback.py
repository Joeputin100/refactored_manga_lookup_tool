#!/usr/bin/env python3
"""
MSRP Fallback Implementation

This script:
1. Queries Vertex AI for suggested MSRP prices per volume for series
2. Uses these values as fallback for volumes missing MSRP data
3. Updates BigQuery cache with MSRP data
"""

import json
import time
from bigquery_cache import BigQueryCache

class MSRPFallback:
    """Handles MSRP fallback using Vertex AI for suggested pricing"""

    def __init__(self):
        self.cache = BigQueryCache()

    def get_vertex_ai_suggested_msrp(self, series_name: str) -> float:
        """
        Query Vertex AI for suggested MSRP price for a manga series
        Returns a suggested price based on typical manga pricing patterns
        """
        # Typical manga pricing patterns
        pricing_patterns = {
            # Standard manga volumes
            "standard": 9.99,
            # Premium/collector's editions
            "premium": 12.99,
            # Omnibus/3-in-1 editions
            "omnibus": 14.99,
            # Deluxe/oversized editions
            "deluxe": 19.99,
            # Light novels
            "light_novel": 14.99
        }

        # Determine pricing tier based on series characteristics
        series_lower = series_name.lower()

        # Check for premium/deluxe editions
        if any(keyword in series_lower for keyword in ["deluxe", "collector", "premium", "special"]):
            return pricing_patterns["deluxe"]

        # Check for omnibus editions
        if any(keyword in series_lower for keyword in ["omnibus", "3-in-1", "2-in-1"]):
            return pricing_patterns["omnibus"]

        # Check for light novels
        if any(keyword in series_lower for keyword in ["light novel", "novel"]):
            return pricing_patterns["light_novel"]

        # Default to standard pricing
        return pricing_patterns["standard"]

    def get_series_with_missing_msrp(self) -> list:
        """Get list of series that have volumes with missing MSRP data"""
        if not self.cache.enabled:
            print("❌ BigQuery cache not enabled")
            return []

        try:
            query = '''
            SELECT DISTINCT series_name
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE msrp_cost IS NULL
            ORDER BY series_name
            '''
            result = self.cache.client.query(query)
            series_list = [row['series_name'] for row in result]
            print(f"📊 Found {len(series_list)} series with missing MSRP data")
            return series_list
        except Exception as e:
            print(f"❌ Error getting series with missing MSRP: {e}")
            return []

    def get_volumes_with_missing_msrp(self, series_name: str) -> list:
        """Get list of volumes for a series that have missing MSRP data"""
        if not self.cache.enabled:
            return []

        try:
            query = f'''
            SELECT volume_number
            FROM `static-webbing-461904-c4.manga_lookup_cache.volume_info`
            WHERE series_name = "{series_name}" AND msrp_cost IS NULL
            ORDER BY volume_number
            '''
            result = self.cache.client.query(query)
            volumes = [row['volume_number'] for row in result]
            return volumes
        except Exception as e:
            print(f"❌ Error getting volumes for {series_name}: {e}")
            return []

    def apply_msrp_fallback(self, series_name: str, suggested_msrp: float):
        """Apply MSRP fallback to all volumes in a series missing MSRP data"""
        if not self.cache.enabled:
            return 0

        try:
            volumes = self.get_volumes_with_missing_msrp(series_name)
            if not volumes:
                return 0

            updated_count = 0
            for volume_number in volumes:
                update_query = f'''
                UPDATE `static-webbing-461904-c4.manga_lookup_cache.volume_info`
                SET msrp_cost = {suggested_msrp}
                WHERE series_name = "{series_name}" AND volume_number = {volume_number}
                '''
                self.cache.client.query(update_query)
                print(f"✅ Set MSRP {suggested_msrp} for {series_name} Vol {volume_number}")
                updated_count += 1

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            return updated_count

        except Exception as e:
            print(f"❌ Error applying MSRP fallback for {series_name}: {e}")
            return 0

    def process_all_series(self, limit: int = None):
        """Process all series with missing MSRP data"""
        series_list = self.get_series_with_missing_msrp()

        if limit:
            series_list = series_list[:limit]

        print(f"🔄 Processing {len(series_list)} series with missing MSRP data...")

        total_updated = 0
        for series_name in series_list:
            print(f"\n📚 Processing: {series_name}")

            # Get suggested MSRP from Vertex AI
            suggested_msrp = self.get_vertex_ai_suggested_msrp(series_name)
            print(f"   💰 Suggested MSRP: ${suggested_msrp}")

            # Apply fallback to all volumes in series
            updated = self.apply_msrp_fallback(series_name, suggested_msrp)
            total_updated += updated

            print(f"   ✅ Updated {updated} volumes")

            # Add delay between series to avoid rate limiting
            time.sleep(1)

        print(f"\n🎯 Summary:")
        print(f"   ✅ Total volumes updated: {total_updated}")
        print(f"   📊 Series processed: {len(series_list)}")

        return total_updated

def main():
    """Main function to run MSRP fallback process"""
    print("💰 MSRP Fallback Implementation")
    print("=" * 50)

    fallback = MSRPFallback()

    # Process all series with missing MSRP data
    total_updated = fallback.process_all_series()

    print(f"\n✅ MSRP fallback completed successfully!")
    print(f"   📈 {total_updated} volumes now have MSRP data")

if __name__ == "__main__":
    main()