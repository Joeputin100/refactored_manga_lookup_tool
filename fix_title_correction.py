#!/usr/bin/env python3
"""
Fix volume title correction in Streamlit app
"""

def fix_volume_title_correction():
    """Fix the volume title correction logic in the Streamlit app"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the section where volume titles are displayed
    # Look for the display_volume_details function
    if 'def display_volume_details' in content:
        print("✅ Found display_volume_details function")

        # Find the line where book.book_title is used
        if 'book.book_title' in content:
            print("✅ Found book.book_title usage")

            # Create the corrected title logic
            corrected_logic = '''
            # Apply volume title correction rules
            display_title = book.book_title

            # Rule 1: If title doesn't contain series name, prepend it
            if book.series_name.lower() not in display_title.lower():
                display_title = f"{book.series_name} {display_title}"

            # Rule 2: If title doesn't contain volume number, append it
            if f"vol" not in display_title.lower() and f"volume" not in display_title.lower():
                display_title = f"{display_title} Vol. {book.volume_number}"

            # Display the corrected title
            st.write(f"**{display_title}**")
            '''

            # Replace the existing title display logic
            # Look for the pattern: st.write(f"**{book.book_title or f\"{series_name} Vol. {book.volume_number}\"}**")
            old_pattern = r'st\.write\(f"\*\*\{book\.book_title or f"\{series_name\} Vol\. \{book\.volume_number\}"\}\*\*"\)'

            if old_pattern in content:
                content = content.replace(old_pattern, corrected_logic)
                print("✅ Replaced title display logic")
            else:
                print("⚠️ Could not find exact pattern, looking for alternative")
                # Try alternative pattern
                alt_pattern = r'st\.write\(f"\*\*.*book\.book_title.*\*\*"\)'
                if alt_pattern in content:
                    content = content.replace(alt_pattern, corrected_logic)
                    print("✅ Replaced alternative title display logic")
                else:
                    print("❌ Could not find title display pattern")
                    return False
        else:
            print("❌ Could not find book.book_title usage")
            return False
    else:
        print("❌ Could not find display_volume_details function")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Successfully updated volume title correction logic")
    return True

if __name__ == "__main__":
    fix_volume_title_correction()