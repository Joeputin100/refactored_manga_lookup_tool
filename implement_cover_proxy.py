#!/usr/bin/env python3
"""
Implement cover image proxy for blocked sites
"""

def implement_cover_proxy():
    """Add cover image proxy functionality to handle blocked sites"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the import section and add the proxy function
    import_section_end = 'from fix_volume_range import parse_volume_range_fixed'

    import_pos = content.find(import_section_end)
    if import_pos == -1:
        print("❌ Could not find import section")
        return False

    # Add the proxy function after imports
    proxy_function = '''

def get_proxied_cover_url(cover_url: str) -> str:
    """
    Get proxied cover URL for sites that block direct image access.
    Downloads the image and serves it locally to avoid CORS/blocking issues.

    Args:
        cover_url: Original cover URL

    Returns:
        Proxied URL or original URL if proxy not needed
    """
    if not cover_url:
        return cover_url

    # Sites that need proxying
    blocked_domains = [
        'mangadex.org',
        'goodreads.com',
        'images-na.ssl-images-amazon.com',
        'm.media-amazon.com'
    ]

    # Check if URL needs proxying
    needs_proxy = any(domain in cover_url for domain in blocked_domains)

    if not needs_proxy:
        return cover_url

    try:
        import requests
        import base64
        from io import BytesIO

        # Download the image
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()

        # Convert to base64 data URL
        image_data = base64.b64encode(response.content).decode('utf-8')
        mime_type = response.headers.get('content-type', 'image/jpeg')

        # Return data URL
        return f"data:{mime_type};base64,{image_data}"

    except Exception as e:
        print(f"❌ Cover proxy failed for {cover_url}: {e}")
        # Return original URL if proxy fails
        return cover_url

'''

    # Insert the proxy function after imports
    insert_pos = import_pos + len(import_section_end)
    content = content[:insert_pos] + proxy_function + content[insert_pos:]

    # Now update the cover image display section to use the proxy
    current_cover_section = '''            # Cover image with comprehensive error handling
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    try:
                        # Validate URL before displaying
                        import requests
                        response = requests.head(book.cover_image_url, timeout=5)
                        if response.status_code == 200:
                            st.image(book.cover_image_url, width=50)
                        else:
                            # Show placeholder for broken URLs
                            st.write("📚")
                    except Exception as e:
                        # Show placeholder for any errors
                        st.write("📚")
                else:
                    st.write("📚")'''

    # Create the enhanced cover section with proxy
    enhanced_cover_section = '''            # Cover image with proxy and comprehensive error handling
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    try:
                        # Use proxy for blocked sites
                        proxied_url = get_proxied_cover_url(book.cover_image_url)

                        # Validate URL before displaying
                        import requests
                        if proxied_url.startswith('data:'):
                            # Data URL - no need to validate
                            st.image(proxied_url, width=50)
                        else:
                            # Regular URL - validate first
                            response = requests.head(proxied_url, timeout=5)
                            if response.status_code == 200:
                                st.image(proxied_url, width=50)
                            else:
                                # Show placeholder for broken URLs
                                st.write("📚")
                    except Exception as e:
                        # Show placeholder for any errors
                        st.write("📚")
                else:
                    st.write("📚")'''

    # Replace the current section with the enhanced version
    if current_cover_section in content:
        content = content.replace(current_cover_section, enhanced_cover_section)
        print("✅ Successfully implemented cover image proxy")
    else:
        print("❌ Could not find current cover image section")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Cover image proxy feature implemented successfully")
    return True

if __name__ == "__main__":
    implement_cover_proxy()