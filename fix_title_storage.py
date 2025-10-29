#!/usr/bin/env python3
"""
Fix title storage to apply correction rules when creating BookInfo objects
"""

def fix_title_storage():
    """Apply title correction rules when creating BookInfo objects"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the BookInfo creation section
    bookinfo_section = '''                        book = BookInfo(
                            series_name=book_data.get("series_name", series_name),
                            volume_number=volume_num,
                            book_title=book_data.get("book_title", f"{series_name} Vol. {volume_num}"),'''

    # Create the enhanced section with title correction
    enhanced_bookinfo_section = '''                        # Apply title correction rules before creating BookInfo
                        book_title = book_data.get("book_title", f"{series_name} Vol. {volume_num}")

                        # Rule 1: If title doesn't contain series name, prepend it
                        if series_name.lower() not in book_title.lower():
                            book_title = f"{series_name} {book_title}"

                        # Rule 2: If title doesn't contain volume number, append it
                        if f"vol" not in book_title.lower() and f"volume" not in book_title.lower():
                            book_title = f"{book_title} Vol. {volume_num}"

                        book = BookInfo(
                            series_name=book_data.get("series_name", series_name),
                            volume_number=volume_num,
                            book_title=book_title,'''

    # Replace the current section with the enhanced version
    if bookinfo_section in content:
        content = content.replace(bookinfo_section, enhanced_bookinfo_section)
        print("✅ Successfully fixed title storage to apply correction rules")
    else:
        print("❌ Could not find BookInfo creation section")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Title storage now applies correction rules when creating BookInfo objects")
    return True

if __name__ == "__main__":
    fix_title_storage()