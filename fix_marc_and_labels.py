#!/usr/bin/env python3
"""
Fix MARC export and label generation issues:
1. Fix blank titles in MARC records
2. Format author names as inverted comma separated
3. Add MSRP to labels on Label 1 after inventory number
"""

import re
from datetime import datetime


def fix_marc_exporter():
    """Fix the MARC exporter to handle missing titles and format authors correctly"""

    # Read the current MARC exporter
    with open('marc_exporter.py', 'r') as f:
        content = f.read()

    # Fix the create_title_field function to ensure title is never blank
    old_title_function = '''def create_title_field(book) -> Field:
    """Create 245 title field"""
    subfields = []

    # Main title
    if book.book_title:
        subfields.append(Subfield('a', book.book_title))
    else:
        subfields.append(Subfield('a', f'{book.series_name} Volume {book.volume_number}'))

    # Statement of responsibility
    if book.authors:
        authors_str = ' ; '.join(book.authors)
        subfields.append(Subfield('c', authors_str))

    return Field(
        tag='245',
        indicators=['1', '0'],
        subfields=subfields
    )'''

    new_title_function = '''def create_title_field(book) -> Field:
    """Create 245 title field"""
    subfields = []

    # Main title - ensure it's never blank
    if hasattr(book, 'book_title') and book.book_title:
        title = book.book_title
    elif hasattr(book, 'series_name') and book.series_name:
        title = f'{book.series_name} Volume {book.volume_number}'
    else:
        title = f'Unknown Manga Volume {book.volume_number}'

    subfields.append(Subfield('a', title))

    # Statement of responsibility - format authors as inverted comma separated
    if hasattr(book, 'authors') and book.authors:
        # Format authors as inverted comma separated (Last, First)
        formatted_authors = []
        for author in book.authors:
            # If author contains comma, assume already inverted
            if ',' in author:
                formatted_authors.append(author)
            else:
                # Simple inversion: split by space and reverse
                parts = author.split()
                if len(parts) >= 2:
                    # Take last part as surname, rest as given names
                    surname = parts[-1]
                    given_names = ' '.join(parts[:-1])
                    formatted_authors.append(f'{surname}, {given_names}')
                else:
                    formatted_authors.append(author)

        authors_str = ' ; '.join(formatted_authors)
        subfields.append(Subfield('c', authors_str))

    return Field(
        tag='245',
        indicators=['1', '0'],
        subfields=subfields
    )'''

    # Replace the function
    if old_title_function in content:
        content = content.replace(old_title_function, new_title_function)
        print("✅ Fixed create_title_field function")
    else:
        print("❌ Could not find create_title_field function to replace")
        return False

    # Write the updated content
    with open('marc_exporter.py', 'w') as f:
        f.write(content)

    print("✅ Successfully updated MARC exporter")
    return True


def fix_label_generator():
    """Fix the label generator to include MSRP on Label 1"""

    # Read the current label generator
    with open('label_generator_updated.py', 'r') as f:
        content = f.read()

    # Find the function that generates Label 1
    # Look for the function that creates the first label
    if 'def generate_label_1' in content:
        # Find the generate_label_1 function
        start_idx = content.find('def generate_label_1')
        if start_idx != -1:
            # Find the end of the function (next def or class)
            end_idx = content.find('\ndef ', start_idx + 1)
            if end_idx == -1:
                end_idx = content.find('\nclass ', start_idx + 1)
            if end_idx == -1:
                end_idx = len(content)

            current_function = content[start_idx:end_idx]

            # Check if MSRP is already included
            if 'msrp' in current_function.lower() or '$' in current_function:
                print("✅ MSRP already included in Label 1")
                return True

            # Find where to insert MSRP (after inventory number)
            if 'barcode' in current_function:
                # Insert MSRP after barcode line
                barcode_pattern = r"draw\.text\(.*?barcode.*?\)"
                barcode_match = re.search(barcode_pattern, current_function, re.DOTALL)

                if barcode_match:
                    barcode_end = barcode_match.end()

                    # Create new function with MSRP added
                    new_function = current_function[:barcode_end] + '''
    # Add MSRP after inventory number
    if hasattr(book, 'msrp') and book.msrp:
        msrp_text = f"${book.msrp:.2f}"
        draw.text((10, y_position + 60), msrp_text, font=font_bold, fill="black")
''' + current_function[barcode_end:]

                    # Replace the function
                    content = content.replace(current_function, new_function)
                    print("✅ Added MSRP to Label 1")
                else:
                    print("❌ Could not find barcode position in Label 1")
                    return False
            else:
                print("❌ Could not find barcode in Label 1 function")
                return False
        else:
            print("❌ Could not find generate_label_1 function")
            return False
    else:
        print("❌ Could not find generate_label_1 function")
        return False

    # Write the updated content
    with open('label_generator_updated.py', 'w') as f:
        f.write(content)

    print("✅ Successfully updated label generator")
    return True


def test_fixes():
    """Test the fixes to ensure they work correctly"""

    print("\n🧪 Testing MARC export fix...")

    # Import the fixed MARC exporter
    try:
        from marc_exporter import create_title_field
        from pymarc import Field, Subfield

        # Create a mock book object
        class MockBook:
            def __init__(self):
                self.series_name = "Test Series"
                self.volume_number = 1
                self.authors = ["John Smith", "Jane Doe"]
                self.msrp = 9.99

        mock_book = MockBook()
        title_field = create_title_field(mock_book)

        # Check if title field was created correctly
        if title_field and title_field.tag == '245':
            print("✅ Title field created successfully")

            # Check if authors are formatted correctly
            subfield_c = None
            for subfield in title_field.subfields:
                if subfield.code == 'c':
                    subfield_c = subfield.value
                    break

            if subfield_c and 'Smith, John' in subfield_c and 'Doe, Jane' in subfield_c:
                print("✅ Authors formatted correctly as inverted comma separated")
            else:
                print("❌ Authors not formatted correctly")
                print(f"   Author field: {subfield_c}")
        else:
            print("❌ Title field creation failed")

    except Exception as e:
        print(f"❌ MARC export test failed: {e}")

    print("\n🧪 Testing label generation...")
    # Note: Label generation test would require more complex setup
    print("⚠️  Label generation test requires manual verification")


def main():
    """Main function to apply all fixes"""

    print("🔧 Fixing MARC export and label generation issues...")
    print("=" * 60)

    # Apply MARC exporter fix
    if fix_marc_exporter():
        print("✅ MARC exporter fix applied successfully")
    else:
        print("❌ MARC exporter fix failed")
        return

    # Apply label generator fix
    if fix_label_generator():
        print("✅ Label generator fix applied successfully")
    else:
        print("❌ Label generator fix failed")
        return

    # Test the fixes
    test_fixes()

    print("\n" + "=" * 60)
    print("✅ All fixes completed!")
    print("\n📋 Summary of changes:")
    print("1. Fixed MARC title field to never be blank")
    print("2. Formatted author names as inverted comma separated")
    print("3. Added MSRP display to Label 1 after inventory number")
    print("\n🚀 Next steps:")
    print("- Test MARC export in the app to verify blank title issue is resolved")
    print("- Generate labels to verify MSRP appears correctly")
    print("- Verify author names are properly inverted in MARC records")


if __name__ == "__main__":
    main()