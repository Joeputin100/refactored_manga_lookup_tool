#!/usr/bin/env python3
"""
Make MARC exporter robust to handle incomplete BookInfo objects
"""


def make_marc_exporter_robust():
    """Update MARC exporter to handle incomplete BookInfo objects gracefully"""

    print("🔧 Making MARC exporter robust to incomplete data...")

    # Read the current MARC exporter
    with open('marc_exporter.py', 'r') as f:
        content = f.read()

    # Fix the error handling in create_bibliographic_record
    old_error_handling = '''    except Exception as e:
        print(f"Error creating bibliographic MARC record for {book.series_name} vol {book.volume_number}: {e}")
        return None'''

    new_error_handling = '''    except Exception as e:
        # Safe error handling for incomplete book objects
        series_info = "unknown series"
        volume_info = "unknown volume"
        if hasattr(book, 'series_name') and book.series_name:
            series_info = book.series_name
        if hasattr(book, 'volume_number'):
            volume_info = str(book.volume_number)
        print(f"Error creating bibliographic MARC record for {series_info} vol {volume_info}: {e}")
        return None'''

    if old_error_handling in content:
        content = content.replace(old_error_handling, new_error_handling)
        print("✅ Fixed error handling in create_bibliographic_record")
    else:
        print("❌ Could not find error handling to update")

    # Make create_fixed_field robust to missing attributes
    old_fixed_field_start = '''def create_fixed_field(book) -> str:
    """Create 008 fixed field data"""
    # Positions: 00-05: Date entered, 06: Type, 07-10: Date 1, 11-14: Date 2, 15-17: Place, etc.
    entry_date = datetime.now().strftime('%y%m%d')

    # Type of record (a = Language material)
    record_type = 'a'

    # Bibliographic level (m = Monograph/Item)
    bib_level = 'm'

    # Type of control (blank = No specific type)
    control_type = ' '

    # Character coding (blank = MARC-8)
    char_coding = ' '

    # Date 1 (publication date) - use cleaned copyright year
    cleaned_year = clean_copyright_year(book.copyright_year)
    date1 = str(cleaned_year) if cleaned_year else '    '
    date1 = date1.ljust(4)'''

    new_fixed_field_start = '''def create_fixed_field(book) -> str:
    """Create 008 fixed field data"""
    # Positions: 00-05: Date entered, 06: Type, 07-10: Date 1, 11-14: Date 2, 15-17: Place, etc.
    entry_date = datetime.now().strftime('%y%m%d')

    # Type of record (a = Language material)
    record_type = 'a'

    # Bibliographic level (m = Monograph/Item)
    bib_level = 'm'

    # Type of control (blank = No specific type)
    control_type = ' '

    # Character coding (blank = MARC-8)
    char_coding = ' '

    # Date 1 (publication date) - use cleaned copyright year
    copyright_year = getattr(book, 'copyright_year', None)
    cleaned_year = clean_copyright_year(copyright_year)
    date1 = str(cleaned_year) if cleaned_year else '    '
    date1 = date1.ljust(4)'''

    if old_fixed_field_start in content:
        content = content.replace(old_fixed_field_start, new_fixed_field_start)
        print("✅ Made create_fixed_field robust to missing copyright_year")
    else:
        print("❌ Could not find create_fixed_field to update")

    # Make add_control_fields robust
    old_control_fields = '''def add_control_fields(record: Record, book) -> None:
    """Add control fields to MARC record"""
    # 001 - Control Number
    if book.barcode:
        record.add_field(Field(tag='001', data=book.barcode))

    # 005 - Date and Time of Latest Transaction
    current_time = datetime.now().strftime('%Y%m%d%H%M%S.0')
    record.add_field(Field(tag='005', data=current_time))

    # 008 - Fixed-Length Data Elements
    fixed_field = create_fixed_field(book)
    record.add_field(Field(tag='008', data=fixed_field))'''

    new_control_fields = '''def add_control_fields(record: Record, book) -> None:
    """Add control fields to MARC record"""
    # 001 - Control Number
    barcode = getattr(book, 'barcode', None)
    if barcode:
        record.add_field(Field(tag='001', data=barcode))

    # 005 - Date and Time of Latest Transaction
    current_time = datetime.now().strftime('%Y%m%d%H%M%S.0')
    record.add_field(Field(tag='005', data=current_time))

    # 008 - Fixed-Length Data Elements
    fixed_field = create_fixed_field(book)
    record.add_field(Field(tag='008', data=fixed_field))'''

    if old_control_fields in content:
        content = content.replace(old_control_fields, new_control_fields)
        print("✅ Made add_control_fields robust to missing barcode")
    else:
        print("❌ Could not find add_control_fields to update")

    # Make add_variable_fields robust
    # Update ISBN handling
    old_isbn_section = '''    # 020 - ISBN
    if book.isbn_13:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[Subfield('a', book.isbn_13)]
        ))'''

    new_isbn_section = '''    # 020 - ISBN
    isbn_13 = getattr(book, 'isbn_13', None)
    if isbn_13:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[Subfield('a', isbn_13)]
        ))'''

    if old_isbn_section in content:
        content = content.replace(old_isbn_section, new_isbn_section)
        print("✅ Made ISBN handling robust")

    # Update author handling
    old_author_section = '''    # 100 - Main Entry - Personal Name (Author)
    if book.authors:
        primary_author = book.authors[0]
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=[Subfield('a', primary_author)]
        ))'''

    new_author_section = '''    # 100 - Main Entry - Personal Name (Author)
    authors = getattr(book, 'authors', None)
    if authors:
        primary_author = authors[0]
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=[Subfield('a', primary_author)]
        ))'''

    if old_author_section in content:
        content = content.replace(old_author_section, new_author_section)
        print("✅ Made author handling robust")

    # Update series handling
    old_series_section = '''    # 490 - Series Statement
    if book.series_name:
        record.add_field(Field(
            tag='490',
            indicators=['1', ' '],
            subfields=[
                Subfield('a', book.series_name),
                Subfield('v', str(book.volume_number))
            ]
        ))'''

    new_series_section = '''    # 490 - Series Statement
    series_name = getattr(book, 'series_name', None)
    volume_number = getattr(book, 'volume_number', None)
    if series_name:
        record.add_field(Field(
            tag='490',
            indicators=['1', ' '],
            subfields=[
                Subfield('a', series_name),
                Subfield('v', str(volume_number) if volume_number else '')
            ]
        ))'''

    if old_series_section in content:
        content = content.replace(old_series_section, new_series_section)
        print("✅ Made series handling robust")

    # Update description handling
    old_description_section = '''    # 520 - Summary, etc.
    if book.description:
        # Clean and truncate description
        clean_desc = clean_text(book.description)
        if len(clean_desc) > 500:
            clean_desc = clean_desc[:497] + '...'

        record.add_field(Field(
            tag='520',
            indicators=[' ', ' '],
            subfields=[Subfield('a', clean_desc)]
        ))'''

    new_description_section = '''    # 520 - Summary, etc.
    description = getattr(book, 'description', None)
    if description:
        # Clean and truncate description
        clean_desc = clean_text(description)
        if len(clean_desc) > 500:
            clean_desc = clean_desc[:497] + '...'

        record.add_field(Field(
            tag='520',
            indicators=[' ', ' '],
            subfields=[Subfield('a', clean_desc)]
        ))'''

    if old_description_section in content:
        content = content.replace(old_description_section, new_description_section)
        print("✅ Made description handling robust")

    # Update publisher handling
    old_publisher_section = '''    # Publisher
    if book.publisher_name:
        subfields.append(Subfield('b', book.publisher_name))
    else:
        subfields.append(Subfield('b', 'Unknown'))'''

    new_publisher_section = '''    # Publisher
    publisher_name = getattr(book, 'publisher_name', None)
    if publisher_name:
        subfields.append(Subfield('b', publisher_name))
    else:
        subfields.append(Subfield('b', 'Unknown'))'''

    if old_publisher_section in content:
        content = content.replace(old_publisher_section, new_publisher_section)
        print("✅ Made publisher handling robust")

    # Write the updated content
    with open('marc_exporter.py', 'w') as f:
        f.write(content)

    print("✅ MARC exporter made robust to incomplete BookInfo objects")
    return True


def deploy_robust_marc_to_ec2():
    """Deploy the robust MARC exporter to EC2"""

    print("\n🚀 Deploying robust MARC exporter to EC2...")

    copy_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-i', '~/.ssh/Rosie2.pem',
        'marc_exporter.py',
        'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com:/home/ec2-user/refactored_manga_lookup_tool/'
    ]

    try:
        import subprocess
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Successfully deployed robust MARC exporter to EC2")
            return True
        else:
            print(f"❌ Failed to deploy to EC2: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error deploying to EC2: {e}")
        return False


def test_robust_marc():
    """Test the robust MARC exporter"""

    print("\n🧪 Testing robust MARC exporter...")

    try:
        from marc_exporter import create_bibliographic_record

        # Test with a very minimal book object
        class MinimalBook:
            def __init__(self):
                # Only provide minimal required data
                self.series_name = "Test Series"
                self.volume_number = 1
                # Intentionally leave out other required fields

        minimal_book = MinimalBook()
        record = create_bibliographic_record(minimal_book)

        if record:
            print("✅ Robust MARC exporter created record from minimal data")
            title_fields = record.get_fields('245')
            if title_fields:
                print(f"   Title field: {title_fields[0]}")
            return True
        else:
            print("❌ Robust MARC exporter failed with minimal data")
            return False

    except Exception as e:
        print(f"❌ Error testing robust MARC exporter: {e}")
        return False


def main():
    """Main function to make MARC exporter robust"""

    print("🔧 Making MARC Exporter Robust")
    print("=" * 60)

    # Make MARC exporter robust
    if make_marc_exporter_robust():
        print("✅ MARC exporter updated")
    else:
        print("❌ MARC exporter update failed")
        return

    # Test the robust MARC exporter
    if test_robust_marc():
        print("✅ Robust MARC exporter test passed")
    else:
        print("❌ Robust MARC exporter test failed")
        return

    # Deploy to EC2
    if deploy_robust_marc_to_ec2():
        print("✅ Robust MARC exporter deployed to EC2")
    else:
        print("❌ Deployment to EC2 failed")
        return

    print("\n" + "=" * 60)
    print("✅ MARC exporter robustness fixes completed!")
    print("\n📋 Summary of changes:")
    print("1. Made all attribute access robust using getattr()")
    print("2. Fixed error handling to work with incomplete objects")
    print("3. Tested with minimal BookInfo objects")
    print("4. Deployed to EC2 instance")
    print("\n🚀 The MARC exporter should now handle incomplete BookInfo objects")
    print("   without generating blank title errors")


if __name__ == "__main__":
    main()