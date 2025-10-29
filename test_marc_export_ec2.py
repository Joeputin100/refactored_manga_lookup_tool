#!/usr/bin/env python3
"""
Test MARC export on EC2 instance to identify why blank title errors persist
"""

import subprocess


def test_marc_export_on_ec2():
    """Test MARC export functionality directly on the EC2 instance"""

    print("🧪 Testing MARC export on EC2 instance...")
    print("=" * 60)

    # Create a test script to run on EC2
    test_script = '''
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

print("\\n2. Testing full MARC export...")
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

print("\\n3. Testing with problematic book data...")
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
'''

    # Write the test script to a file
    with open('test_marc_ec2.py', 'w') as f:
        f.write(test_script)

    # Copy the test script to EC2
    copy_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-i', '~/.ssh/Rosie2.pem',
        'test_marc_ec2.py',
        'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com:/home/ec2-user/refactored_manga_lookup_tool/'
    ]

    try:
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to copy test script to EC2: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error copying test script to EC2: {e}")
        return False

    # Run the test script on EC2
    run_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-i', '~/.ssh/Rosie2.pem',
        'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com',
        'cd /home/ec2-user/refactored_manga_lookup_tool && python3 test_marc_ec2.py'
    ]

    try:
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test on EC2: {e}")
        return False


def check_actual_book_data():
    """Check what actual BookInfo data looks like from the app"""

    print("\n🔍 Checking actual BookInfo data from app...")
    print("=" * 60)

    # Check the streamlit app on EC2 to see what data is being exported
    check_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-i', '~/.ssh/Rosie2.pem',
        'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com',
        'cd /home/ec2-user/refactored_manga_lookup_tool && grep -A 20 -B 5 "export_books_to_marc" streamlit_app.py'
    ]

    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        print("MARC export section in streamlit_app.py:")
        print(result.stdout)

        if result.stderr:
            print(f"Errors: {result.stderr}")
    except Exception as e:
        print(f"❌ Error checking app code: {e}")


def main():
    """Main test function"""

    print("🐛 MARC Export Debug - EC2 Test")
    print("=" * 60)

    # Test MARC export on EC2
    if test_marc_export_on_ec2():
        print("\n✅ MARC export test completed on EC2")
    else:
        print("\n❌ MARC export test failed on EC2")

    # Check actual app data
    check_actual_book_data()

    print("\n" + "=" * 60)
    print("📋 Analysis:")
    print("If MARC export works in tests but fails in the app, the issue is likely:")
    print("1. BookInfo objects from the app have missing required data")
    print("2. The app is not passing the correct BookInfo objects to the MARC exporter")
    print("3. There's an issue with how the app retrieves or processes book data")
    print("\n🔧 Next steps based on test results above")


if __name__ == "__main__":
    main()