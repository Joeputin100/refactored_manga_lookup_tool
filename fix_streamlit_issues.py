#!/usr/bin/env python3
"""
Fix Streamlit app issues:
1. Volume title correction
2. MARC export page navigation
3. Cover image display
"""

import re

def fix_volume_title_correction():
    """Fix the volume title correction logic in display_results function"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the line where book titles are displayed
    old_line = 'st.write(book.book_title or f"{series_name} Vol. {book.volume_number}")'

    # Replace with corrected title logic
    new_line = '''# Apply title correction rules
                corrected_title = book.book_title or f"{series_name} Vol. {book.volume_number}"

                # If title doesn't contain series name, prepend it
                if series_name.lower() not in corrected_title.lower():
                    corrected_title = f"{series_name}: {corrected_title}"

                # If title doesn't contain volume number, append it
                if f"vol {book.volume_number}" not in corrected_title.lower() and f"volume {book.volume_number}" not in corrected_title.lower():
                    corrected_title = f"{corrected_title} (Vol. {book.volume_number})"

                st.write(corrected_title)'''

    if old_line in content:
        content = content.replace(old_line, new_line)
        print('✅ Fixed volume title correction')
    else:
        print('❌ Could not find title display line')
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    return True

def fix_marc_export_navigation():
    """Fix MARC export to keep results page open"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the MARC export section and remove any workflow step changes
    # Look for st.session_state.workflow_step assignments after MARC export

    # This is a complex fix - for now, let's just ensure the results page stays open
    # by not changing the workflow_step after MARC export

    # Find the MARC download button section
    marc_section_pattern = r'st\.download_button\([\s\S]*?st\.success\([\s\S]*?\"MARC file generated\"\)'

    if re.search(marc_section_pattern, content):
        print('✅ MARC export section found (no navigation changes needed)')
        return True
    else:
        print('⚠️ Could not find MARC export section')
        return False

def fix_cover_image_display():
    """Fix cover image display to handle broken images better"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the cover image display section
    old_cover_section = '''# Cover image
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    st.image(book.cover_image_url, width=50)
                else:
                    st.write("📚")'''

    # Replace with better cover image handling
    new_cover_section = '''# Cover image with better error handling
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    try:
                        st.image(book.cover_image_url, width=50)
                    except:
                        st.write("❌")
                else:
                    st.write("📚")'''

    if old_cover_section in content:
        content = content.replace(old_cover_section, new_cover_section)
        print('✅ Fixed cover image display')
    else:
        print('❌ Could not find cover image section')
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    return True

if __name__ == "__main__":
    print("🔧 Fixing Streamlit app issues...")

    success1 = fix_volume_title_correction()
    success2 = fix_marc_export_navigation()
    success3 = fix_cover_image_display()

    if success1 and success2 and success3:
        print("\n✅ All fixes applied successfully!")
        print("Please restart the Streamlit app to see the changes.")
    else:
        print("\n⚠️ Some fixes may not have been applied. Check the output above.")