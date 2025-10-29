#!/usr/bin/env python3
"""
Reimplement volume title correction feature
"""

def reimplement_title_correction():
    """Add volume title correction logic to the Streamlit app"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the current title display section
    current_title_section = '''            # Title
            with col2:
                st.write(book.book_title or f"{series_name} Vol. {book.volume_number}")'''

    # Create the enhanced title section with correction logic
    enhanced_title_section = '''            # Title
            with col2:
                # Apply title correction rules
                corrected_title = book.book_title or f"{series_name} Vol. {book.volume_number}"

                # Rule 1: If title doesn't contain series name, prepend it
                if series_name.lower() not in corrected_title.lower():
                    corrected_title = f"{series_name} {corrected_title}"

                # Rule 2: If title doesn't contain volume number, append it
                if f"vol" not in corrected_title.lower() and f"volume" not in corrected_title.lower():
                    corrected_title = f"{corrected_title} Vol. {book.volume_number}"

                st.write(corrected_title)'''

    # Replace the current section with the enhanced version
    if current_title_section in content:
        content = content.replace(current_title_section, enhanced_title_section)
        print("✅ Successfully reimplemented volume title correction")
    else:
        print("❌ Could not find current title section")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Volume title correction feature reimplemented successfully")
    return True

if __name__ == "__main__":
    reimplement_title_correction()