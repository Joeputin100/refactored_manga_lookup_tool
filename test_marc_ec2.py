
import sys
sys.path.append('.')

from marc_exporter import export_books_to_marc, create_bibliographic_record, create_holding_record
from pymarc import MARCReader

# Create a test book with minimal required data
class TestBook:
    def __init__(self):
        self.series_name = "One Piece"
        self.volume_number = 1
        self.authors = ["Eiichiro Oda"]
        self.barcode = "TEST001"
        self.isbn_13 = "9781421502400"
        self.copyright_year = "2003"
        self.publisher_name = "VIZ Media"
        self.description = "The first volume of One Piece"
        self.genres = ["Action", "Adventure"]
        self.cover_image_url = "http://example.com/cover.jpg"
        self.physical_description = "200 pages"
        self.msrp = 9.99

print("1. Testing individual record creation...")
test_book = TestBook()

# Test bibliographic record
bib_record = create_bibliographic_record(test_book)
if bib_record:
    print(f"   ✅ Bibliographic record created")
    title_fields = bib_record.get_fields('245')
    if title_fields:
        for field in title_fields:
            print(f"     Title (245): {field}")
            for subfield in field.subfields:
                print(f"       Subfield {subfield.code}: '{subfield.value}'")
    else:
        print("     ❌ No title field found!")
else:
    print("   ❌ Bibliographic record creation failed")

# Test holding record
holding_record = create_holding_record(test_book)
if holding_record:
    print(f"   ✅ Holding record created")
    location_fields = holding_record.get_fields('852')
    if location_fields:
        print(f"     Location field (852): Found {len(location_fields)}")
    else:
        print("     ❌ No location field found!")
else:
    print("   ❌ Holding record creation failed")

print("\n2. Testing full MARC export...")
books = [test_book]
marc_data = export_books_to_marc(books)

if marc_data:
    print(f"   ✅ MARC export successful")
    print(f"     Data size: {len(marc_data)} bytes")

    # Parse and analyze the MARC data
    reader = MARCReader(marc_data)
    records = list(reader)
    print(f"     Records generated: {len(records)}")

    for i, record in enumerate(records):
        print(f"     Record {i+1}:")
        print(f"       Leader: '{record.leader}'")
        print(f"       Fields: {len(record.fields)}")

        # Check for title field
        title_fields = record.get_fields('245')
        if title_fields:
            print(f"       ✅ Title field (245) found")
            for field in title_fields:
                print(f"         {field}")
        else:
            print(f"       ❌ No title field (245) found!")

        # List all fields for debugging
        print(f"       All fields:")
        for field in record.fields:
            print(f"         {field}")

else:
    print("   ❌ MARC export failed - no data generated")

print("\n3. Testing with problematic book data...")
# Test with a book that might have missing data
class ProblematicBook:
    def __init__(self):
        # Intentionally leave out series_name to test fallback
        self.volume_number = 1
        self.authors = ["Test Author"]
        self.barcode = "PROB001"
        # Missing other required fields

problem_book = ProblematicBook()
print("   Testing book with missing series_name...")

bib_record2 = create_bibliographic_record(problem_book)
if bib_record2:
    print(f"   ✅ Bibliographic record created for problematic book")
    title_fields = bib_record2.get_fields('245')
    if title_fields:
        for field in title_fields:
            print(f"     Title (245): {field}")
            for subfield in field.subfields:
                print(f"       Subfield {subfield.code}: '{subfield.value}'")
    else:
        print("     ❌ No title field found for problematic book!")
else:
    print("   ❌ Bibliographic record creation failed for problematic book")
