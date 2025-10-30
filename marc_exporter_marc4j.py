#!/usr/bin/env python3
"""
MARC21 exporter using MARC4J via JPype
"""

import sys
import os

# Add JPype to path if needed
sys.path.append('/data/data/com.termux/files/usr/lib/python3.11/site-packages')

try:
    import jpype
    import jpype.imports
    from jpype.types import *
except ImportError as e:
    print(f"JPype import error: {e}")
    print("Trying alternative import...")

    # Try direct import
    import importlib.util
    spec = importlib.util.find_spec("jpype")
    if spec is not None:
        jpype = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jpype)
    else:
        raise ImportError("JPype not found")

def start_jvm():
    """Start JVM with MARC4J classpath"""
    if not jpype.isJVMStarted():
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        marc4j_jar = os.path.join(current_dir, "marc4j.jar")

        # Start JVM
        jpype.startJVM(
            jpype.getDefaultJVMPath(),
            "-Dfile.encoding=UTF-8",
            f"-Djava.class.path={marc4j_jar}"
        )

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

def create_bibliographic_record_marc4j(book):
    """Create a MARC21 bibliographic record using MARC4J."""

    # Import MARC4J classes
    from org.marc4j.marc import Record, DataField, ControlField, Leader
    from org.marc4j.marc.impl import RecordImpl, DataFieldImpl, ControlFieldImpl
    from org.marc4j.marc.impl import LeaderImpl

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

    # Create record
    record = RecordImpl()

    # Create leader
    leader = LeaderImpl()
    leader.setRecordStatus('n')  # New record
    leader.setTypeOfRecord('a')  # Language material
    leader.setBibliographicLevel('m')  # Monograph
    leader.setEncodingLevel(' ')  # Full level
    leader.setCharCodingScheme('a')  # UCS/Unicode
    record.setLeader(leader)

    # 001 - Control Number
    if barcode:
        control_field = ControlFieldImpl("001")
        control_field.setData(barcode)
        record.addVariableField(control_field)

    # 005 - Date and Time of Latest Transaction
    from java.text import SimpleDateFormat
    from java.util import Date
    date_format = SimpleDateFormat("yyyyMMddHHmmss.S")
    current_time = date_format.format(Date())

    control_field = ControlFieldImpl("005")
    control_field.setData(current_time)
    record.addVariableField(control_field)

    # 008 - Fixed-Length Data Elements
    pub_date = str(copyright_year) if copyright_year else '    '
    fixed_data = f"{current_time[:6]}s{pub_date[:4]}xxu          eng d       0  0 eng d"

    control_field = ControlFieldImpl("008")
    control_field.setData(fixed_data.ljust(40))
    record.addVariableField(control_field)

    # 020 - ISBN
    if isbn_13:
        data_field = DataFieldImpl("020", ' ', ' ')
        data_field.addSubfield('a', isbn_13)
        record.addVariableField(data_field)

    # 040 - Cataloging Source
    data_field = DataFieldImpl("040", ' ', ' ')
    data_field.addSubfield('a', "MANG")
    data_field.addSubfield('c', "MANG")
    data_field.addSubfield('e', "rda")
    record.addVariableField(data_field)

    # 100 - Main Entry - Personal Name
    if inverted_authors:
        data_field = DataFieldImpl("100", '1', ' ')
        data_field.addSubfield('a', inverted_authors[0])
        record.addVariableField(data_field)

    # 245 - Title Statement
    data_field = DataFieldImpl("245", '1', '0')
    data_field.addSubfield('a', title)
    if inverted_authors:
        data_field.addSubfield('c', ' ; '.join(inverted_authors))
    record.addVariableField(data_field)

    # 250 - Edition Statement
    data_field = DataFieldImpl("250", ' ', ' ')
    data_field.addSubfield('a', "First edition")
    record.addVariableField(data_field)

    # 260 - Publication, Distribution, etc.
    data_field = DataFieldImpl("260", ' ', ' ')
    data_field.addSubfield('a', "[United States]")
    data_field.addSubfield('b', publisher_name)
    if copyright_year:
        data_field.addSubfield('c', str(copyright_year))
    record.addVariableField(data_field)

    # 300 - Physical Description
    data_field = DataFieldImpl("300", ' ', ' ')
    if physical_description:
        data_field.addSubfield('a', physical_description)
    else:
        data_field.addSubfield('a', "pages")
        data_field.addSubfield('b', "illustrations")
        data_field.addSubfield('c', "19 cm")
    record.addVariableField(data_field)

    # 490 - Series Statement
    if series_name:
        data_field = DataFieldImpl("490", '1', ' ')
        data_field.addSubfield('a', series_name)
        data_field.addSubfield('v', str(volume_number))
        record.addVariableField(data_field)

    # 520 - Summary, etc.
    if description:
        # Truncate description if too long
        desc = description[:500] if len(description) > 500 else description
        data_field = DataFieldImpl("520", ' ', ' ')
        data_field.addSubfield('a', desc)
        record.addVariableField(data_field)

    # 650 - Subject Added Entry - Topical Term
    for genre in genres[:3]:  # Limit to 3 genres
        data_field = DataFieldImpl("650", ' ', '0')
        data_field.addSubfield('a', genre)
        record.addVariableField(data_field)

    # 655 - Index Term - Genre/Form
    data_field = DataFieldImpl("655", ' ', '7')
    data_field.addSubfield('a', "Manga")
    data_field.addSubfield('2', "lcgft")
    record.addVariableField(data_field)

    return record

def create_holding_record_marc4j(book):
    """Create a MARC21 holding record using MARC4J."""

    from org.marc4j.marc import Record, DataField, ControlField, Leader
    from org.marc4j.marc.impl import RecordImpl, DataFieldImpl, ControlFieldImpl
    from org.marc4j.marc.impl import LeaderImpl

    barcode = getattr(book, 'barcode', '')
    msrp_cost = getattr(book, 'msrp_cost', None)

    # Create record
    record = RecordImpl()

    # Create leader for holdings
    leader = LeaderImpl()
    leader.setRecordStatus(' ')  # No specific status
    leader.setTypeOfRecord('v')  # Holdings
    leader.setBibliographicLevel(' ')  # No level
    leader.setEncodingLevel(' ')  # Full level
    leader.setCharCodingScheme('a')  # UCS/Unicode
    record.setLeader(leader)

    # 001 - Control Number (prefixed with H for holding)
    if barcode:
        control_field = ControlFieldImpl("001")
        control_field.setData(f"H{barcode}")
        record.addVariableField(control_field)

    # 005 - Date and Time of Latest Transaction
    from java.text import SimpleDateFormat
    from java.util import Date
    date_format = SimpleDateFormat("yyyyMMddHHmmss.S")
    current_time = date_format.format(Date())

    control_field = ControlFieldImpl("005")
    control_field.setData(current_time)
    record.addVariableField(control_field)

    # 008 - Fixed-Length Data Elements (holding format)
    fixed_data = f"{current_time[:6]}v{getattr(book, 'volume_number', 1)}                "

    control_field = ControlFieldImpl("008")
    control_field.setData(fixed_data.ljust(40))
    record.addVariableField(control_field)

    # 852 - Location
    if barcode:
        data_field = DataFieldImpl("852", ' ', ' ')
        data_field.addSubfield('a', "MANG")
        data_field.addSubfield('b', "Manga Collection")
        data_field.addSubfield('h', barcode)
        record.addVariableField(data_field)

    # 020 - Standard Technical Report Number (using for MSRP)
    if msrp_cost:
        data_field = DataFieldImpl("020", ' ', ' ')
        data_field.addSubfield('c', f"${msrp_cost:.2f}")
        record.addVariableField(data_field)

    # 037 - Source of Acquisition (using for cost)
    if msrp_cost:
        data_field = DataFieldImpl("037", ' ', ' ')
        data_field.addSubfield('a', f"${msrp_cost:.2f}")
        data_field.addSubfield('b', "MSRP")
        record.addVariableField(data_field)

    return record

def export_books_to_marc_marc4j(books):
    """Export a list of BookInfo objects to MARC21 format using MARC4J."""

    # Start JVM if not already started
    start_jvm()

    from org.marc4j import MarcStreamWriter
    from java.io import ByteArrayOutputStream

    records = []

    for book in books:
        # Create bibliographic record
        bib_record = create_bibliographic_record_marc4j(book)
        if bib_record:
            records.append(bib_record)

        # Create holding record
        holding_record = create_holding_record_marc4j(book)
        if holding_record:
            records.append(holding_record)

    # Write records to byte array
    output_stream = ByteArrayOutputStream()
    writer = MarcStreamWriter(output_stream, "UTF-8")

    for record in records:
        writer.write(record)

    writer.close()

    return bytes(output_stream.toByteArray())

# Test function
def test_marc4j_export():
    """Test the MARC4J exporter"""

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

    print("Testing MARC4J exporter...")

    try:
        # Test full export
        marc_data = export_books_to_marc_marc4j([test_book])
        print(f"MARC4J export size: {len(marc_data)} bytes")

        # Save to file
        with open("marc4j_test.mrc", "wb") as f:
            f.write(marc_data)
        print("Saved to 'marc4j_test.mrc'")

    except Exception as e:
        print(f"MARC4J export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_marc4j_export()