#!/usr/bin/env python3
"""
MARC Exporter for Manga Lookup Tool

Exports manga book data to MARC21 format for library systems.
"""

import re
from datetime import datetime

from pymarc import Field, Record, Subfield
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


def get_author_initials(author):
    """Extract first 3 letters of author's last name in uppercase"""
    if not author:
        return "UNK"

    # Handle inverted format "Last, First"
    if ',' in author:
        last_name = author.split(',')[0].strip()
    else:
        # Handle "First Last" format
        parts = author.split()
        last_name = parts[-1] if parts else ""

    # Get first 3 letters, uppercase, padded if needed
    initials = last_name[:3].upper()
    return initials.ljust(3, 'X') if len(initials) < 3 else initials


def create_call_number(book):
    """Create call number: FIC [Author initials] [Year] [Barcode]"""
    # Get author initials
    authors = getattr(book, 'authors', [])
    author_initials = "UNK"
    if authors:
        author_initials = get_author_initials(authors[0])

    # Get copyright year
    copyright_year = getattr(book, 'copyright_year', None)
    cleaned_year = clean_copyright_year(copyright_year)
    year_str = cleaned_year if cleaned_year else "0000"

    # Get barcode
    barcode = getattr(book, 'barcode', "UNKNOWN")

    # Format: FIC MAS 2008 BARCODE#
    return f"FIC {author_initials} {year_str} {barcode}"



def export_books_to_marc(books: list) -> bytes:
    """
    Export a list of BookInfo objects to MARC21 format.
    Creates both bibliographic and holding records for each book.

    Args:
        books: List of BookInfo objects

    Returns:
        MARC data as bytes
    """
    records = []

    for book in books:
        # Create bibliographic record
        bib_record = create_bibliographic_record(book)
        if bib_record:
            records.append(bib_record)

        # Create holding record
        holding_record = create_holding_record(book)
        if holding_record:
            records.append(holding_record)

    # Combine all records into a single byte stream
    marc_data = b""
    for record in records:
        marc_data += record.as_marc()

    return marc_data


def create_bibliographic_record(book) -> Record:
    """
    Create a MARC21 bibliographic record from a BookInfo object.

    Args:
        book: BookInfo object

    Returns:
        pymarc.Record object or None if creation fails
    """
    try:
        record = Record()

        # Leader (mandatory)
        record.leader = '00000nam a2200000   4500'

        # Control fields
        add_control_fields(record, book)

        # Variable fields
        add_variable_fields(record, book)

        return record

    except Exception as e:
        # Safe error handling for incomplete book objects
        series_info = "unknown series"
        volume_info = "unknown volume"
        if hasattr(book, 'series_name') and book.series_name:
            series_info = book.series_name
        if hasattr(book, 'volume_number'):
            volume_info = str(book.volume_number)
        print(f"Error creating bibliographic MARC record for {series_info} vol {volume_info}: {e}")
        return None


def create_holding_record(book) -> Record:
    """
    Create a MARC21 holding record from a BookInfo object.

    Args:
        book: BookInfo object

    Returns:
        pymarc.Record object or None if creation fails
    """
    try:
        record = Record()

        # Leader for holding record
        record.leader = '00000nu  a2200000   4500'

        # Control fields for holding record
        add_holding_control_fields(record, book)

        # Variable fields for holding record
        add_holding_variable_fields(record, book)

        return record

    except Exception as e:
        print(f"Error creating holding MARC record for {book.series_name} vol {book.volume_number}: {e}")
        return None


def add_control_fields(record: Record, book) -> None:
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
    record.add_field(Field(tag='008', data=fixed_field))


def create_fixed_field(book) -> str:
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
    date1 = date1.ljust(4)

    # Date 2 (blank for single date)
    date2 = '    '

    # Country (xxu = United States, unknown)
    country = 'xxu'

    # Illustrations (a = Illustrations)
    illustrations = 'a'

    # Target audience (blank = Unknown)
    audience = ' '

    # Form of item (blank = None of the following)
    form = ' '

    # Nature of contents (blank = Not specified)
    contents = ' '

    # Government publication (blank = Not a gov pub)
    gov_pub = ' '

    # Conference publication (0 = Not a conference pub)
    conference = '0'

    # Festschrift (0 = Not a festschrift)
    festschrift = '0'

    # Index (0 = No index)
    index = '0'

    # Literary form (0 = Not fiction)
    literary_form = '0'

    # Biography (blank = No biographical material)
    biography = ' '

    # Language (eng = English)
    language = 'eng'

    # Modified record (blank = Not modified)
    modified = ' '

    # Cataloging source (d = Other)
    source = 'd'

    # Combine all parts
    fixed_field = (
        f'{entry_date}'  # 00-05
        f'{record_type}'  # 06
        f'{bib_level}'  # 07
        f'{control_type}'  # 08
        f'{char_coding}'  # 09
        f'{date1}'  # 10-13
        f'{date2}'  # 14-17
        f'{country}'  # 18-20
        f'{illustrations}'  # 21
        f'{audience}'  # 22
        f'{form}'  # 23
        f'{contents}'  # 24-27
        f'{gov_pub}'  # 28
        f'{conference}'  # 29
        f'{festschrift}'  # 30
        f'{index}'  # 31
        f'{literary_form}'  # 33
        f'{biography}'  # 34
        f'{language}'  # 35-37
        f'{modified}'  # 38
        f'{source}'  # 39
    )

    return fixed_field.ljust(40)


def add_holding_control_fields(record: Record, book) -> None:
    """Add control fields to holding record"""
    # 001 - Control Number (use barcode with H prefix)
    if book.barcode:
        record.add_field(Field(tag='001', data=f'H{book.barcode}'))

    # 005 - Date and Time of Latest Transaction
    current_time = datetime.now().strftime('%Y%m%d%H%M%S.0')
    record.add_field(Field(tag='005', data=current_time))

    # 008 - Fixed-Length Data Elements for holdings
    fixed_field = create_holding_fixed_field(book)
    record.add_field(Field(tag='008', data=fixed_field))


def create_holding_fixed_field(book) -> str:
    """Create 008 fixed field data for holding record"""
    entry_date = datetime.now().strftime('%y%m%d')

    # Type of record (v = Multipart item holdings)
    record_type = 'v'

    # Receipt/acquisition status (1 = Other)
    receipt_status = '1'

    # General retention policy (blank = Not specified)
    retention = ' '

    # Completeness (blank = Not specified)
    completeness = ' '

    # Date of report (blank = Not specified)
    report_date = '    '

    # Fixed field for holdings
    fixed_field = (
        f'{entry_date}'  # 00-05
        f'{record_type}'  # 06
        f'{receipt_status}'  # 07
        f'{retention}'  # 08
        f'{completeness}'  # 09
        f'{report_date}'  # 10-13
    )

    return fixed_field.ljust(40)


def add_holding_variable_fields(record: Record, book) -> None:
    """Add variable fields to holding record"""

    # 852 - Location with proper call number format
    call_number = create_call_number(book)
    record.add_field(Field(
        tag='852',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'MANG'),  # Location code
            Subfield('b', 'Manga Collection'),  # Sublocation
            Subfield('h', call_number)  # Call number in proper format
        ]
    ))

    # 245 - Title Statement (added to match Atriuum holding record format)
    title_field = create_title_field(book)
    record.add_field(title_field)


    # 856 - Electronic Location and Access
    if book.cover_image_url:
        record.add_field(Field(
            tag='856',
            indicators=['4', '1'],
            subfields=[
                Subfield('u', book.cover_image_url),
                Subfield('z', 'Cover image')
            ]
        ))

    # 876 - Item Information
    barcode = getattr(book, 'barcode', None)
    if barcode:
        record.add_field(Field(
            tag='876',
            indicators=[' ', ' '],
            subfields=[
                Subfield('a', barcode),  # Barcode
                Subfield('p', barcode),  # Material barcode (Text format)
                Subfield('j', 'Text')    # Material type
            ]
        ))

    # 020 - Price (MSRP) in holding record
    if hasattr(book, 'msrp') and book.msrp:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[
                Subfield('c', f'${book.msrp:.2f}')  # Price field
            ]
        ))

    # 037 - Source of Acquisition (Cost) in holding record
    if hasattr(book, 'msrp') and book.msrp:
        record.add_field(Field(
            tag='037',
            indicators=[' ', ' '],
            subfields=[
                Subfield('a', f'${book.msrp:.2f}'),  # Cost field
                Subfield('b', 'MSRP')
            ]
        ))


def add_variable_fields(record: Record, book) -> None:
    """Add variable fields to MARC record"""

    # 020 - ISBN
    isbn_13 = getattr(book, 'isbn_13', None)
    if isbn_13:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[Subfield('a', isbn_13)]
        ))

    # 040 - Cataloging Source
    record.add_field(Field(
        tag='040',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'MANG'),
            Subfield('c', 'MANG'),
            Subfield('e', 'rda')
        ]
    ))

    # 100 - Main Entry - Personal Name (Author)
    authors = getattr(book, 'authors', None)
    if authors:
        primary_author = invert_author_name(authors[0])
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=[Subfield('a', primary_author)]
        ))

    # 245 - Title Statement
    title_field = create_title_field(book)
    record.add_field(title_field)

    # 250 - Edition Statement
    record.add_field(Field(
        tag='250',
        indicators=[' ', ' '],
        subfields=[Subfield('a', 'First edition')]
    ))

    # 260 - Publication, Distribution, etc.
    pub_field = create_publication_field(book)
    record.add_field(pub_field)

    # 300 - Physical Description
    phys_desc_field = create_physical_description_field(book)
    record.add_field(phys_desc_field)

    # 490 - Series Statement
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
        ))

    # 520 - Summary, etc.
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
        ))

    # 650 - Subject Added Entry - Topical Term
    for genre in book.genres[:3]:  # Limit to first 3 genres
        record.add_field(Field(
            tag='650',
            indicators=[' ', '0'],
            subfields=[Subfield('a', genre)]
        ))

    # 655 - Index Term - Genre/Form
    record.add_field(Field(
        tag='655',
        indicators=[' ', '7'],
        subfields=[
            Subfield('a', 'Manga'),
            Subfield('2', 'lcgft')
        ]
    ))

    # 856 - Electronic Location and Access (Cover Image)
    if book.cover_image_url:
        record.add_field(Field(
            tag='856',
            indicators=['4', '1'],
            subfields=[
                Subfield('u', book.cover_image_url),
                Subfield('z', 'Cover image')
            ]
        ))

    # 020 - Price (MSRP)
    if hasattr(book, 'msrp') and book.msrp:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[
                Subfield('c', f'${book.msrp:.2f}')  # Price field
            ]
        ))

    # 037 - Source of Acquisition (Cost)
    if hasattr(book, 'msrp') and book.msrp:
        record.add_field(Field(
            tag='037',
            indicators=[' ', ' '],
            subfields=[
                Subfield('a', f'${book.msrp:.2f}'),  # Cost field
                Subfield('b', 'MSRP')
            ]
        ))


def create_title_field(book) -> Field:
    """Create 245 title field - ROBUST VERSION"""
    subfields = []

    # Main title - ensure it's never blank
    title = ""

    # Try multiple fallback strategies
    if hasattr(book, 'book_title') and book.book_title and book.book_title.strip():
        title = book.book_title.strip()
    elif hasattr(book, 'series_name') and book.series_name:
        volume_num = getattr(book, 'volume_number', 1)
        title = f'{book.series_name} Volume {volume_num}'
    else:
        volume_num = getattr(book, 'volume_number', 1)
        title = f'Manga Volume {volume_num}'

    # Ensure title is never empty
    if not title or not title.strip():
        title = "Unknown Manga Title"

    subfields.append(Subfield('a', title))

    # Statement of responsibility - use inverted author names
    if hasattr(book, 'authors') and book.authors:
        # Use the pre-inverted author names
        inverted_authors = invert_author_list(book.authors)
        authors_str = ' ; '.join(inverted_authors)
        subfields.append(Subfield('c', authors_str))

    return Field(
        tag='245',
        indicators=['1', '0'],
        subfields=subfields
    )


def create_publication_field(book) -> Field:
    """Create 260 publication field"""
    subfields = []

    # Place of publication
    subfields.append(Subfield('a', '[United States]'))

    # Publisher
    publisher_name = getattr(book, 'publisher_name', None)
    if publisher_name:
        subfields.append(Subfield('b', publisher_name))
    else:
        subfields.append(Subfield('b', 'Unknown'))

    # Date of publication - use cleaned copyright year
    cleaned_year = clean_copyright_year(book.copyright_year)
    if cleaned_year:
        subfields.append(Subfield('c', str(cleaned_year)))
    else:
        subfields.append(Subfield('c', '[n.d.]'))

    return Field(
        tag='260',
        indicators=[' ', ' '],
        subfields=subfields
    )


def create_physical_description_field(book) -> Field:
    """Create 300 physical description field"""
    subfields = []

    # Extent
    if book.physical_description:
        # Try to extract page count from physical description
        page_match = re.search(r'(\d+)\s*pages?', book.physical_description, re.IGNORECASE)
        if page_match:
            subfields.append(Subfield('a', f'{page_match.group(1)} pages'))
        else:
            subfields.append(Subfield('a', 'pages'))
    else:
        subfields.append(Subfield('a', 'pages'))

    # Other physical details
    subfields.append(Subfield('b', 'illustrations'))

    # Dimensions
    subfields.append(Subfield('c', '19 cm'))

    return Field(
        tag='300',
        indicators=[' ', ' '],
        subfields=subfields
    )


def clean_copyright_year(year):
    """Clean copyright year to ensure 4-digit year only"""
    if not year:
        return None

    # Convert to string and remove 'c' prefix and dots
    year_str = str(year)
    # Remove 'c' prefix and any non-digit characters except digits
    year_str = re.sub(r'^c', '', year_str, flags=re.IGNORECASE)
    year_str = re.sub(r'[^0-9]', '', year_str)

    # Ensure we have a 4-digit year
    if len(year_str) == 4:
        return year_str
    elif len(year_str) == 2:
        # Assume 20th/21st century
        year_num = int(year_str)
        if year_num <= 50:  # If year <= 50, assume 2000s
            return f"20{year_str}"
        else:  # If year > 50, assume 1900s
            return f"19{year_str}"
    else:
        # If we can't determine, return None
        return None


def clean_text(text: str) -> str:
    """Clean text for MARC fields"""
    if not text:
        return ""

    # Remove extra whitespace
    text = ' '.join(text.split())

    # Remove problematic characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    return text


def main():
    """Test function for MARC export"""
    print("MARC Exporter Test")
    print("This module is designed to be used with the manga_lookup tool.")


if __name__ == "__main__":
    main()