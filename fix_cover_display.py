#!/usr/bin/env python3
"""
Fix cover image display with URL validation
"""

def fix_cover_display():
    """Replace the cover image display section with improved version"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        lines = f.readlines()

    # Find and replace the cover image section (lines 1280-1290)
    new_lines = []
    i = 0
    while i < len(lines):
        if i >= 1279 and i <= 1289:  # Lines 1280-1290
            # Replace this section
            new_lines.extend([
                '            # Cover image with comprehensive error handling\n',
                '            with col1:\n',
                '                if hasattr(book, \'cover_image_url\') and book.cover_image_url:\n',
                '                    try:\n',
                '                        # Validate URL before displaying\n',
                '                        import requests\n',
                '                        response = requests.head(book.cover_image_url, timeout=5)\n',
                '                        if response.status_code == 200:\n',
                '                            st.image(book.cover_image_url, width=50)\n',
                '                        else:\n',
                '                            # Show placeholder for broken URLs\n',
                '                            st.write(\"📚\")\n',
                '                    except Exception as e:\n',
                '                        # Show placeholder for any errors\n',
                '                        st.write(\"📚\")\n',
                '                else:\n',
                '                    st.write(\"📚\")\n'
            ])
            i = 1290  # Skip to after the replaced section
        else:
            new_lines.append(lines[i])
            i += 1

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.writelines(new_lines)

    print("✅ Successfully updated cover image display")
    return True

if __name__ == "__main__":
    fix_cover_display()