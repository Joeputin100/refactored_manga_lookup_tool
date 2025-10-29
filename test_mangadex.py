#!/usr/bin/env python3
"""
Test MangaDex cover URLs
"""

import requests

# Test the MangaDex URL from the logs
cover_url = 'https://uploads.mangadex.org/covers/304ceac3-8cdb-4fe7-acf7-2b6ff7a60613/29f82b1d-b37f-455a-b630-e42bccb1422a.jpg'
print(f'Testing MangaDex cover URL: {cover_url}')

try:
    response = requests.get(cover_url, timeout=5, stream=True)
    print(f'GET request status: {response.status_code}')
    print(f'Content type: {response.headers.get("content-type", "unknown")}')
    content_length = response.headers.get('content-length')
    print(f'Content length: {content_length}')

    # Check if it's a placeholder by looking at content length
    if content_length and int(content_length) < 10000:  # Placeholder images are usually small
        print('⚠️ This might be a placeholder image (small file size)')
    else:
        print('✅ Image looks legitimate')

except Exception as e:
    print(f'Error: {e}')