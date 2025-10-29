#!/usr/bin/env python3
"""
Check why specific series are failing to import from Wikipedia
"""

import requests
from bs4 import BeautifulSoup

def check_wikipedia_urls():
    """Check Wikipedia URLs for failed series"""

    failed_series = [
        "Case Closed / Detective Conan",
        "Emblem Take 2",
        "Gaki Deka",
        "Himitsu Series"
    ]

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'MangaLookupTool/1.0 (https://github.com/your-repo; your-email@example.com)'
    })

    print('🔍 Investigating Failed Wikipedia Imports')
    print('=' * 50)

    for series in failed_series:
        print(f'\n📚 Checking: {series}')

        # Try different URL formats
        url_formats = [
            f"https://en.wikipedia.org/wiki/{series.replace(' ', '_')}",
            f"https://en.wikipedia.org/wiki/{series.replace(' ', '_').replace('/', '_')}",
        ]

        # Special cases
        if series == "Case Closed / Detective Conan":
            url_formats.append("https://en.wikipedia.org/wiki/Case_Closed")
            url_formats.append("https://en.wikipedia.org/wiki/Detective_Conan")
        elif series == "Emblem Take 2":
            url_formats.append("https://en.wikipedia.org/wiki/Emblem_Take_2")
        elif series == "Gaki Deka":
            url_formats.append("https://en.wikipedia.org/wiki/Gaki_Deka")
        elif series == "Himitsu Series":
            url_formats.append("https://en.wikipedia.org/wiki/Himitsu_Series")

        found = False
        for url in url_formats:
            try:
                print(f'  Trying: {url}')
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    print(f'  ✅ Found at: {url}')
                    found = True
                    break
                elif response.status_code == 404:
                    print(f'  ❌ 404 Not Found')
                else:
                    print(f'  ⚠️ Status: {response.status_code}')
            except Exception as e:
                print(f'  ❌ Error: {e}')

        if not found:
            print(f'  ❌ No valid Wikipedia page found for {series}')

if __name__ == "__main__":
    check_wikipedia_urls()