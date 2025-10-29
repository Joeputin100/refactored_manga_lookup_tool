#!/usr/bin/env python3
"""
Add Tokyo Ghoul:re series manually
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigquery_cache import BigQueryCache

def add_tokyo_ghoul_re():
    """Add Tokyo Ghoul:re series manually"""

    cache = BigQueryCache()

    print("📚 Adding Tokyo Ghoul:re series manually")
    print("=" * 50)

    # Tokyo Ghoul:re series information
    series_info = {
        "corrected_series_name": "Tokyo Ghoul:re",
        "authors": ["Sui Ishida"],
        "extant_volumes": 16,
        "summary": "Tokyo Ghoul:re is the sequel to Tokyo Ghoul, continuing the story in a world where humans and ghouls coexist. The series follows Haise Sasaki, an investigator who leads the CCG's special squad, Quinx Squad, as they hunt ghouls while dealing with his own mysterious past and connection to the original Tokyo Ghoul protagonist, Ken Kaneki.",
        "spinoff_series": [],
        "alternate_editions": [],
        "cover_image_url": "https://upload.wikimedia.org/wikipedia/en/thumb/6/6e/Tokyo_Ghoul_re_volume_1_cover.jpg/220px-Tokyo_Ghoul_re_volume_1_cover.jpg",
        "genres": ["Horror", "Dark fantasy", "Supernatural", "Action"],
        "publisher": "Shueisha",
        "status": "Completed",
        "alternative_titles": ["Tokyo Ghoul:re"],
        "adaptations": ["Anime", "Live-action"]
    }

    # Cache the series info
    cache.cache_series_info("Tokyo Ghoul:re", series_info, api_source="manual")

    print("✅ Tokyo Ghoul:re series added to database")
    print(f"📊 Series info: {series_info['extant_volumes']} volumes")
    print(f"📝 Summary: {series_info['summary'][:100]}...")

if __name__ == "__main__":
    add_tokyo_ghoul_re()