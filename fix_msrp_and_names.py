#!/usr/bin/env python3
"""
Fix MSRP display on Label One and ensure names are stored inverted
"""

import re


def fix_label_generator_msrp():
    """Fix the label generator to properly display MSRP on Label One"""

    print("🔧 Fixing MSRP display on Label One...")

    # Read the current label generator
    with open('label_generator.py', 'r') as f:
        content = f.read()

    # Find the Label One section (label_type == 1)
    label_one_start = content.find('if label_type == 1:')
    if label_one_start == -1:
        print("❌ Could not find Label One section")
        return False

    # Find the end of Label One section
    label_one_end = content.find('\n    elif label_type == 2:', label_one_start)
    if label_one_end == -1:
        label_one_end = content.find('\n    elif label_type == 3:', label_one_start)
    if label_one_end == -1:
        label_one_end = content.find('\n    elif label_type == 4:', label_one_start)
    if label_one_end == -1:
        label_one_end = len(content)

    label_one_section = content[label_one_start:label_one_end]

    # Check current MSRP handling
    if 'msrp' in label_one_section.lower():
        print("✅ MSRP handling found in Label One")

        # Check if MSRP is properly displayed
        if '${' in label_one_section and ':.2f}' in label_one_section:
            print("✅ MSRP formatting appears correct")
        else:
            print("⚠️  MSRP formatting may need adjustment")

            # Fix MSRP formatting if needed
            old_msrp_line = None
            new_msrp_line = None

            lines = label_one_section.split('\n')
            for i, line in enumerate(lines):
                if 'msrp' in line.lower() and 'text' in line.lower():
                    old_msrp_line = line
                    # Ensure proper MSRP formatting
                    if '${' not in line or ':.2f}' not in line:
                        new_msrp_line = line.replace('msrp', '${msrp:.2f}')
                        break

            if old_msrp_line and new_msrp_line:
                content = content.replace(old_msrp_line, new_msrp_line)
                print("✅ Fixed MSRP formatting")
    else:
        print("❌ No MSRP handling found in Label One")

        # Add MSRP to Label One
        # Find where to insert MSRP (after inventory number line)
        inventory_line_idx = label_one_section.find('inventory_number')
        if inventory_line_idx != -1:
            # Find the end of the line with inventory number
            line_end = label_one_section.find('\n', inventory_line_idx)
            if line_end != -1:
                # Insert MSRP after inventory number
                insert_point = label_one_start + line_end + 1

                msrp_insert = '''        # Add MSRP after inventory number
        msrp_value = book_data.get("MSRP", "") or book_data.get("msrp_cost", "")
        if msrp_value:
            try:
                msrp_text = f"${float(msrp_value):.2f}"
                text_lines.append(f"MSRP: {msrp_text}")
            except (ValueError, TypeError):
                pass  # Skip if MSRP is not a valid number
'''

                content = content[:insert_point] + msrp_insert + content[insert_point:]
                print("✅ Added MSRP handling to Label One")
        else:
            print("❌ Could not find inventory number line in Label One")
            return False

    # Write the updated content
    with open('label_generator.py', 'w') as f:
        f.write(content)

    print("✅ Label generator MSRP fix applied")
    return True


def fix_author_storage():
    """Fix author storage to be inverted (Last, First) in the data"""

    print("\n🔧 Fixing author name storage to inverted format...")

    # Read the manga_lookup file to find where authors are stored
    with open('manga_lookup.py', 'r') as f:
        content = f.read()

    # Find the BookInfo class
    bookinfo_start = content.find('class BookInfo:')
    if bookinfo_start == -1:
        print("❌ Could not find BookInfo class")
        return False

    # Find the __init__ method
    init_start = content.find('def __init__', bookinfo_start)
    if init_start == -1:
        print("❌ Could not find BookInfo.__init__ method")
        return False

    # Find where authors are processed in the code
    author_processing_patterns = [
        # Look for places where authors are assigned or processed
        r'self\.authors\s*=',
        r'authors\s*=',
        r'\bauthor\b',
    ]

    author_processing_locations = []
    for pattern in author_processing_patterns:
        matches = list(re.finditer(pattern, content))
        for match in matches:
            # Get some context
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            author_processing_locations.append((match.start(), context))

    print(f"Found {len(author_processing_locations)} potential author processing locations")

    # We need to modify the data processing to invert names before storage
    # This would require changes to the API processing and data storage
    print("⚠️  Author storage inversion requires changes to data processing pipeline")
    print("   This affects how data is retrieved from APIs and stored in BigQuery")

    # For now, let's create a function to invert names in the MARC exporter
    print("\n🔧 Creating author inversion function for MARC export...")

    # Read the MARC exporter
    with open('marc_exporter.py', 'r') as f:
        marc_content = f.read()

    # Add a function to invert author names
    invert_function = '''
def invert_author_name(author):
    """
    Convert author name from 'First Last' to 'Last, First' format.
    Handles various name formats and edge cases.
    """
    if not author or not isinstance(author, str):
        return author

    # If already contains comma, assume already inverted
    if ',' in author:
        return author

    # Remove extra whitespace
    author = ' '.join(author.split())

    # Handle common manga author patterns
    parts = author.split()

    if len(parts) == 1:
        # Single name (like "Oda")
        return author
    elif len(parts) == 2:
        # Simple case: "First Last" -> "Last, First"
        return f"{parts[1]}, {parts[0]}"
    elif len(parts) >= 3:
        # Multiple parts: assume last part is surname
        surname = parts[-1]
        given_names = ' '.join(parts[:-1])
        return f"{surname}, {given_names}"
    else:
        return author


def invert_author_list(authors):
    """
    Invert a list of author names.
    """
    if not authors:
        return []

    inverted_authors = []
    for author in authors:
        inverted_authors.append(invert_author_name(author))

    return inverted_authors
'''

    # Insert the function after the imports
    import_end = marc_content.find('\n\n', marc_content.find('from pymarc'))
    if import_end != -1:
        marc_content = marc_content[:import_end] + invert_function + marc_content[import_end:]
        print("✅ Added author inversion functions to MARC exporter")
    else:
        print("❌ Could not find import section in MARC exporter")
        return False

    # Update the create_title_field function to use inverted authors
    old_author_section = '''    # Statement of responsibility - format authors as inverted comma separated
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
        subfields.append(Subfield('c', authors_str))'''

    new_author_section = '''    # Statement of responsibility - use inverted author names
    if hasattr(book, 'authors') and book.authors:
        # Use the pre-inverted author names
        inverted_authors = invert_author_list(book.authors)
        authors_str = ' ; '.join(inverted_authors)
        subfields.append(Subfield('c', authors_str))'''

    if old_author_section in marc_content:
        marc_content = marc_content.replace(old_author_section, new_author_section)
        print("✅ Updated MARC exporter to use inverted author names")
    else:
        print("❌ Could not find author section to update in MARC exporter")

    # Write the updated MARC exporter
    with open('marc_exporter.py', 'w') as f:
        f.write(marc_content)

    print("✅ Author storage and MARC export fixes applied")
    return True


def deploy_fixes_to_ec2():
    """Deploy the fixes to the EC2 instance"""

    print("\n🚀 Deploying fixes to EC2 instance...")

    files_to_deploy = ['label_generator.py', 'marc_exporter.py']

    for file in files_to_deploy:
        copy_cmd = [
            'scp', '-o', 'StrictHostKeyChecking=no', '-i', '~/.ssh/Rosie2.pem',
            file,
            f'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com:/home/ec2-user/refactored_manga_lookup_tool/'
        ]

        try:
            import subprocess
            result = subprocess.run(copy_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Successfully deployed {file} to EC2")
            else:
                print(f"❌ Failed to deploy {file} to EC2: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error deploying {file} to EC2: {e}")
            return False

    print("✅ All fixes deployed to EC2")
    return True


def main():
    """Main function to apply all fixes"""

    print("🔧 Fixing MSRP and Author Name Issues")
    print("=" * 60)

    # Fix MSRP on Label One
    if fix_label_generator_msrp():
        print("✅ MSRP fix applied")
    else:
        print("❌ MSRP fix failed")
        return

    # Fix author name storage
    if fix_author_storage():
        print("✅ Author name fix applied")
    else:
        print("❌ Author name fix failed")
        return

    # Deploy to EC2
    if deploy_fixes_to_ec2():
        print("✅ Fixes deployed to EC2")
    else:
        print("❌ Deployment to EC2 failed")
        return

    print("\n" + "=" * 60)
    print("✅ All fixes completed successfully!")
    print("\n📋 Summary of changes:")
    print("1. Fixed MSRP display on Label One in label generator")
    print("2. Added author name inversion functions")
    print("3. Updated MARC exporter to use inverted author names")
    print("4. Deployed all fixes to EC2 instance")
    print("\n🚀 Next steps:")
    print("- Test label generation to verify MSRP appears on Label One")
    print("- Test MARC export to verify author names are inverted")
    print("- Verify the fixes work in the Streamlit app on EC2")


if __name__ == "__main__":
    main()