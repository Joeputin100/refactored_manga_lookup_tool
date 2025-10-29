#!/usr/bin/env python3
"""
Debug MARC export issues - investigate why titles are blank and holding records missing
"""

import sys
import traceback
from pymarc import Record


def debug_bookinfo_objects():
    """Debug the BookInfo objects to see what data they contain"""

    print("🔍 Debugging BookInfo objects...")
    print("=" * 60)

    try:
        # Import the manga_lookup module to access BookInfo
        sys.path.append('.')
        from manga_lookup import BookInfo

        # Create a test BookInfo object to see its structure
        test_book = BookInfo()
        print("📚 BookInfo object attributes:")
        for attr in dir(test_book):
            if not attr.startswith('_'):
                value = getattr(test_book, attr, None)
                if value is not None and value != '':
                    print(f"  {attr}: {value}")

        print("\n📝 BookInfo required attributes for MARC:")
        required_attrs = ['series_name', 'volume_number', 'authors', 'barcode', 'isbn_13']
        for attr in required_attrs:
            has_attr = hasattr(test_book, attr)
            value = getattr(test_book, attr, None)
            print(f"  {attr}: {'✅' if has_attr else '❌'} (value: {value})")

    except Exception as e:
        print(f"❌ Error examining BookInfo: {e}")
        traceback.print_exc()


def debug_marc_generation():
    """Debug the actual MARC generation process"""

    print("\n🔍 Debugging MARC generation process...")
    print("=" * 60)

    try:
        from marc_exporter import create_bibliographic_record, create_holding_record, create_title_field
        from pymarc import Field, Subfield

        # Create a minimal test book
        class TestBook:
            def __init__(self):
                self.series_name = "Test Series"
                self.volume_number = 1
                self.authors = ["Test Author"]
                self.barcode = "TEST123456"
                self.isbn_13 = "9781234567890"
                self.copyright_year = "2023"
                self.publisher_name = "Test Publisher"
                self.description = "Test description"
                self.genres = ["Action"]
                self.cover_image_url = "http://example.com/cover.jpg"
                self.physical_description = "200 pages"
                self.msrp = 9.99

        test_book = TestBook()

        print("1. Testing title field creation...")
        title_field = create_title_field(test_book)
        if title_field:
            print(f"   ✅ Title field created: {title_field}")
            for subfield in title_field.subfields:
                print(f"     Subfield {subfield.code}: '{subfield.value}'")
        else:
            print("   ❌ Title field creation failed")

        print("\n2. Testing bibliographic record creation...")
        bib_record = create_bibliographic_record(test_book)
        if bib_record:
            print(f"   ✅ Bibliographic record created")
            print(f"     Leader: {bib_record.leader}")
            print(f"     Fields: {len(bib_record.fields)}")

            # Check for title field
            title_fields = bib_record.get_fields('245')
            if title_fields:
                print(f"     Title field (245): Found {len(title_fields)}")
                for field in title_fields:
                    print(f"       {field}")
            else:
                print("     ❌ No title field (245) found!")
        else:
            print("   ❌ Bibliographic record creation failed")

        print("\n3. Testing holding record creation...")
        holding_record = create_holding_record(test_book)
        if holding_record:
            print(f"   ✅ Holding record created")
            print(f"     Leader: {holding_record.leader}")
            print(f"     Fields: {len(holding_record.fields)}")

            # Check for holding fields
            location_fields = holding_record.get_fields('852')
            if location_fields:
                print(f"     Location field (852): Found {len(location_fields)}")
            else:
                print("     ❌ No location field (852) found!")
        else:
            print("   ❌ Holding record creation failed")

        print("\n4. Testing full MARC export...")
        from marc_exporter import export_books_to_marc

        books = [test_book]
        marc_data = export_books_to_marc(books)

        if marc_data:
            print(f"   ✅ MARC export successful")
            print(f"     Data size: {len(marc_data)} bytes")

            # Try to parse the MARC data
            try:
                from pymarc import MARCReader
                reader = MARCReader(marc_data)
                records = list(reader)
                print(f"     Records in export: {len(records)}")

                for i, record in enumerate(records):
                    print(f"     Record {i+1}: Leader='{record.leader}' Fields={len(record.fields)}")

                    # Check title field
                    title_fields = record.get_fields('245')
                    if title_fields:
                        for field in title_fields:
                            print(f"       Title (245): {field}")
                    else:
                        print(f"       ❌ No title field (245) in record {i+1}!")

            except Exception as e:
                print(f"     ❌ Error parsing MARC data: {e}")
        else:
            print("   ❌ MARC export failed - no data generated")

    except Exception as e:
        print(f"❌ Error in MARC generation debug: {e}")
        traceback.print_exc()


def debug_app_marc_export():
    """Debug the MARC export process from the app perspective"""

    print("\n🔍 Debugging app MARC export...")
    print("=" * 60)

    try:
        # Check what the app is actually exporting
        print("1. Checking app MARC export logic...")

        with open('streamlit_app.py', 'r') as f:
            content = f.read()

        # Find the MARC export section
        if 'export_books_to_marc' in content:
            print("   ✅ MARC export function found in app")

            # Extract the relevant section
            start_idx = content.find('export_books_to_marc')
            if start_idx != -1:
                context_start = max(0, start_idx - 200)
                context_end = min(len(content), start_idx + 500)
                context = content[context_start:context_end]

                print("   MARC export context:")
                lines = context.split('\n')
                for line in lines:
                    if 'export_books_to_marc' in line or 'marc_data' in line or 'st.session_state.all_books' in line:
                        print(f"     {line.strip()}")
        else:
            print("   ❌ MARC export function not found in app")

    except Exception as e:
        print(f"❌ Error debugging app MARC export: {e}")


def main():
    """Main debug function"""

    print("🐛 MARC Export Debug Tool")
    print("=" * 60)

    debug_bookinfo_objects()
    debug_marc_generation()
    debug_app_marc_export()

    print("\n" + "=" * 60)
    print("📋 Debug Summary:")
    print("1. Check BookInfo object structure and data")
    print("2. Test individual MARC record creation")
    print("3. Test full MARC export process")
    print("4. Check app MARC export logic")
    print("\n🔧 Next steps based on debug output above")


if __name__ == "__main__":
    main()