#!/usr/bin/env python3
"""
Reimplement cover image URL validation feature
"""

def reimplement_cover_validation():
    """Add cover image URL validation to the Streamlit app"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the current cover image display section
    current_cover_section = '''            # Cover image
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    st.image(book.cover_image_url, width=50)
                else:
                    st.write("📚")'''

    # Create the enhanced cover section with URL validation
    enhanced_cover_section = '''            # Cover image with comprehensive error handling
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

    # Replace the current section with the enhanced version
    if current_cover_section in content:
        content = content.replace(current_cover_section, enhanced_cover_section)
        print("✅ Successfully reimplemented cover image URL validation")
    else:
        print("❌ Could not find current cover image section")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Cover image URL validation feature reimplemented successfully")
    return True

if __name__ == "__main__":
    reimplement_cover_validation()