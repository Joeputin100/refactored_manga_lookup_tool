#!/usr/bin/env python3
"""
Simple MARC21 exporter using pure Python without external dependencies
Implements basic MARC21 record structure with proper encoding
"""

import struct
from datetime import datetime

def invert_author_name(author):
    """Convert author name from 'First Last' to 'Last, First' format."""
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
    """Invert a list of author names."""
    if not authors:
        return []

    inverted_authors = []
    for author in authors:
        inverted_authors.append(invert_author_name(author))

    return inverted_authors

def encode_marc_field(tag, indicators, subfields):
    """Encode a MARC field as bytes."""
    # Build field content
    content = ''.join(subfields)

    # Create field directory entry
    field_length = len(content) + len(indicators) + 1  # +1 for field terminator
    field_start = 0  # Will be calculated later

    # Return field data (directory will be built later)
    field_data = indicators + content + '\x1e'
    return field_data, field_length

def create_leader(record_length, record_status='n', record_type='a', encoding_level=' '):
    """Create MARC leader field."""
    # Leader structure (24 bytes):
    # 00-04: Record length
    # 05: Record status
    # 06: Record type
    # 07: Bibliographic level
    # 08-09: Type of control
    # 10: Character coding scheme
    # 11: Indicator count
    # 12: Subfield code count
    # 13-16: Base address of data
    # 17: Encoding level
    # 18: Descriptive cataloging form
    # 19: Multipart resource record level
    # 20: Length of field length portion
    # 21: Length of starting character position portion
    # 22: Length of implementation-defined portion
    # 23: Undefined

    # Base address is always 24 (leader length) + directory length
    # We'll calculate this later
    base_address = 24

    leader = f"{record_length:05d}{record_status}{record_type}a  {encoding_level}22    4500"
    return leader.ljust(24)

def create_bibliographic_record_simple(book):
    """Create a MARC21 bibliographic record using simple encoding."""

    # Get book data with fallbacks
    series_name = getattr(book, 'series_name', 'Unknown Manga')
    volume_number = getattr(book, 'volume_number', 1)
    book_title = getattr(book, 'book_title', '')
    authors = getattr(book, 'authors', [])
    copyright_year = getattr(book, 'copyright_year', '')
    publisher_name = getattr(book, 'publisher_name', 'Unknown')
    isbn_13 = getattr(book, 'isbn_13', '')
    barcode = getattr(book, 'barcode', '')
    description = getattr(book, 'description', '')
    physical_description = getattr(book, 'physical_description', '')
    genres = getattr(book, 'genres', [])

    # Create title
    if book_title:
        title = book_title
    elif series_name:
        title = f"{series_name} Volume {volume_number}"
    else:
        title = f"Unknown Manga Volume {volume_number}"

    # Invert author names
    inverted_authors = invert_author_list(authors)

    # Build fields
    fields = []

    # 001 - Control Number
    if barcode:
        fields.append(('001', '  ', f"{barcode}"))

    # 005 - Date and Time of Latest Transaction
    current_time = datetime.now().strftime("%Y%m%d%H%M%S.0")
    fields.append(('005', '  ', current_time))

    # 008 - Fixed-Length Data Elements
    # Simplified 008 field for books
    pub_date = str(copyright_year) if copyright_year else '    '
    country = 'xxu'  # Unknown country
    language = 'eng'  # English
    illus = 'a' if 'illustrations' in physical_description.lower() else ' '

    fixed_data = f"{current_time[:6]}s{pub_date[:4]}{country}    {language} d{illus}     0  0 eng d"
    fields.append(('008', '  ', fixed_data.ljust(40)))

    # 020 - ISBN
    if isbn_13:
        fields.append(('020', '  ', f"$a{isbn_13}"))

    # 040 - Cataloging Source
    fields.append(('040', '  ', "$aMANG$cMANG$erda"))

    # 100 - Main Entry - Personal Name
    if inverted_authors:
        fields.append(('100', '1 ', f"$a{inverted_authors[0]}"))

    # 245 - Title Statement
    title_field = f"$a{title}"
    if inverted_authors:
        title_field += f"$c{'; '.join(inverted_authors)}"
    fields.append(('245', '10', title_field))

    # 250 - Edition Statement
    fields.append(('250', '  ', "$aFirst edition"))

    # 260 - Publication, Distribution, etc.
    pub_field = f"$a[United States]$b{publisher_name}"
    if copyright_year:
        pub_field += f"$c{copyright_year}"
    fields.append(('260', '  ', pub_field))

    # 300 - Physical Description
    if physical_description:
        fields.append(('300', '  ', f"$a{physical_description}"))
    else:
        fields.append(('300', '  ', "$apages$billustrations$c19 cm"))

    # 490 - Series Statement
    if series_name:
        fields.append(('490', '1 ', f"$a{series_name}$v{volume_number}"))

    # 520 - Summary, etc.
    if description:
        # Truncate description if too long
        desc = description[:500] if len(description) > 500 else description
        fields.append(('520', '  ', f"$a{desc}"))

    # 650 - Subject Added Entry - Topical Term
    for genre in genres[:3]:  # Limit to 3 genres
        fields.append(('650', ' 0', f"$a{genre}"))

    # 655 - Index Term - Genre/Form
    fields.append(('655', ' 7', "$aManga$2lcgft"))

    # Encode the record
    return encode_marc_record(fields, record_type='a')

def create_holding_record_simple(book):
    """Create a MARC21 holding record using simple encoding."""

    barcode = getattr(book, 'barcode', '')
    msrp_cost = getattr(book, 'msrp_cost', None)

    fields = []

    # 001 - Control Number (prefixed with H for holding)
    if barcode:
        fields.append(('001', '  ', f"H{barcode}"))

    # 005 - Date and Time of Latest Transaction
    current_time = datetime.now().strftime("%Y%m%d%H%M%S.0")
    fields.append(('005', '  ', current_time))

    # 008 - Fixed-Length Data Elements (holding format)
    fixed_data = f"{current_time[:6]}v{getattr(book, 'volume_number', 1)}                "
    fields.append(('008', '  ', fixed_data.ljust(40)))

    # 852 - Location
    if barcode:
        fields.append(('852', '  ', f"$aMANG$bManga Collection$h{barcode}"))

    # 020 - Standard Technical Report Number (using for MSRP)
    if msrp_cost:
        fields.append(('020', '  ', f"$c${msrp_cost:.2f}"))

    # 037 - Source of Acquisition (using for cost)
    if msrp_cost:
        fields.append(('037', '  ', f"$a${msrp_cost:.2f}$bMSRP"))

    # Encode the record
    return encode_marc_record(fields, record_type='v')

def encode_marc_record(fields, record_type='a'):
    """Encode a complete MARC record as bytes."""

    # Build directory and data
    directory = []
    data = b""
    base_address = 24  # Leader length

    # Calculate directory length
    directory_length = 0
    for tag, indicators, content in fields:
        field_length = len(content) + len(indicators) + 1  # +1 for field terminator
        directory_length += 12  # Each directory entry is 12 bytes

    base_address += directory_length

    # Build directory and data
    current_position = 0
    for tag, indicators, content in fields:
        field_data = indicators + content + '\x1e'
        field_length = len(field_data)

        # Directory entry: tag(3) + field_length(4) + start_position(5)
        directory_entry = f"{tag}{field_length:04d}{current_position:05d}"
        directory.append(directory_entry)

        data += field_data.encode('utf-8')
        current_position += field_length

    # Add record terminator
    data += b'\x1d'

    # Calculate total record length
    record_length = base_address + len(data)

    # Create leader
    if record_type == 'a':
        leader = create_leader(record_length, 'n', 'a', ' ')
    else:
        leader = create_leader(record_length, ' ', 'v', ' ')

    # Build complete record
    directory_str = ''.join(directory)
    marc_record = leader.encode('utf-8') + directory_str.encode('utf-8') + data

    return marc_record

def export_books_to_marc_simple(books):
    """Export a list of BookInfo objects to MARC21 format using simple encoding."""
    records = []

    for book in books:
        # Create bibliographic record
        bib_record = create_bibliographic_record_simple(book)
        if bib_record:
            records.append(bib_record)

        # Create holding record
        holding_record = create_holding_record_simple(book)
        if holding_record:
            records.append(holding_record)

    # Combine all records
    marc_data = b"".join(records)
    return marc_data

# Test function
def test_simple_marc_export():
    """Test the simple MARC exporter"""

    # Create test book
    test_book = type("Book", (), {
        "series_name": "Attack on Titan",
        "volume_number": 1,
        "book_title": "Attack on Titan Volume 1",
        "authors": ["Hajime Isayama"],
        "copyright_year": "2012",
        "publisher_name": "Kodansha Comics",
        "isbn_13": "9781612620244",
        "msrp_cost": 10.99,
        "barcode": "AOT000001",
        "description": "In this post-apocalyptic sci-fi story, humanity has been devastated by the bizarre, giant humanoids known as the Titans.",
        "physical_description": "192 pages : illustrations ; 19 cm",
        "genres": ["Action", "Horror", "Science Fiction"]
    })()

    print("Testing simple MARC exporter...")

    # Test bibliographic record
    bib_record = create_bibliographic_record_simple(test_book)
    print(f"Bibliographic record size: {len(bib_record)} bytes")

    # Test holding record
    holding_record = create_holding_record_simple(test_book)
    print(f"Holding record size: {len(holding_record)} bytes")

    # Test full export
    marc_data = export_books_to_marc_simple([test_book])
    print(f"Full MARC export size: {len(marc_data)} bytes")

    # Save to file
    with open("simple_marc_test.mrc", "wb") as f:
        f.write(marc_data)
    print("Saved to 'simple_marc_test.mrc'")

if __name__ == "__main__":
    test_simple_marc_export()