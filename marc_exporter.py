#!/usr/bin/env python3
"""
MARC Exporter for Manga Lookup Tool

Exports manga book data to MARC21 format for library systems.
"""

import re
from datetime import datetime

from pymarc import Field, Record


def export_books_to_marc(books: list) -> bytes:
    """
    Export a list of BookInfo objects to MARC21 format.

    Args:
        books: List of BookInfo objects

    Returns:
        MARC data as bytes
    """
    records = []

    for book in books:
        record = create_marc_record(book)
        if record:
            records.append(record)

    # Combine all records into a single byte stream
    marc_data = b""
    for record in records:
        marc_data += record.as_marc()

    return marc_data


def create_marc_record(book) -> Record:
    """
    Create a MARC21 record from a BookInfo object.

    Args:
        book: BookInfo object

    Returns:
        pymarc.Record object or None if creation fails
    """
    try:
        record = Record()

        # Leader (mandatory)
        record.leader = '00000nam a2200000Ia 4500'

        # Control fields
        add_control_fields(record, book)

        # Variable fields
        add_variable_fields(record, book)

        return record

    except Exception as e:
        print(f"Error creating MARC record for {book.series_name} vol {book.volume_number}: {e}")
        return None


def add_control_fields(record: Record, book) -> None:
    """Add control fields to MARC record"""
    # 001 - Control Number
    if book.barcode:
        record.add_field(Field(tag='001', data=book.barcode))

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

    # Date 1 (publication date)
    date1 = str(book.copyright_year) if book.copyright_year else '    '
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


def add_variable_fields(record: Record, book) -> None:
    """Add variable fields to MARC record"""

    # 020 - ISBN
    if book.isbn_13:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=['a', book.isbn_13]
        ))

    # 040 - Cataloging Source
    record.add_field(Field(
        tag='040',
        indicators=[' ', ' '],
        subfields=['a', 'MANG', 'c', 'MANG', 'e', 'rda']
    ))

    # 100 - Main Entry - Personal Name (Author)
    if book.authors:
        primary_author = book.authors[0]
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=['a', primary_author]
        ))

    # 245 - Title Statement
    title_field = create_title_field(book)
    record.add_field(title_field)

    # 250 - Edition Statement
    record.add_field(Field(
        tag='250',
        indicators=[' ', ' '],
        subfields=['a', 'First edition']
    ))

    # 260 - Publication, Distribution, etc.
    pub_field = create_publication_field(book)
    record.add_field(pub_field)

    # 300 - Physical Description
    phys_desc_field = create_physical_description_field(book)
    record.add_field(phys_desc_field)

    # 490 - Series Statement
    if book.series_name:
        record.add_field(Field(
            tag='490',
            indicators=['1', ' '],
            subfields=['a', book.series_name, 'v', str(book.volume_number)]
        ))

    # 520 - Summary, etc.
    if book.description:
        # Clean and truncate description
        clean_desc = clean_text(book.description)
        if len(clean_desc) > 500:
            clean_desc = clean_desc[:497] + '...'

        record.add_field(Field(
            tag='520',
            indicators=[' ', ' '],
            subfields=['a', clean_desc]
        ))

    # 650 - Subject Added Entry - Topical Term
    for genre in book.genres[:3]:  # Limit to first 3 genres
        record.add_field(Field(
            tag='650',
            indicators=[' ', '0'],
            subfields=['a', genre]
        ))

    # 655 - Index Term - Genre/Form
    record.add_field(Field(
        tag='655',
        indicators=[' ', '7'],
        subfields=['a', 'Manga', '2', 'lcgft']
    ))

    # 856 - Electronic Location and Access (Cover Image)
    if book.cover_image_url:
        record.add_field(Field(
            tag='856',
            indicators=['4', '1'],
            subfields=['u', book.cover_image_url, 'z', 'Cover image']
        ))


def create_title_field(book) -> Field:
    """Create 245 title field"""
    title_parts = []

    # Main title
    if book.book_title:
        title_parts.extend(['a', book.book_title])
    else:
        title_parts.extend(['a', f'{book.series_name} Volume {book.volume_number}'])

    # Statement of responsibility
    if book.authors:
        authors_str = ' ; '.join(book.authors)
        title_parts.extend(['c', authors_str])

    return Field(
        tag='245',
        indicators=['1', '0'],
        subfields=title_parts
    )


def create_publication_field(book) -> Field:
    """Create 260 publication field"""
    subfields = []

    # Place of publication
    subfields.extend(['a', '[United States]'])

    # Publisher
    if book.publisher_name:
        subfields.extend(['b', book.publisher_name])
    else:
        subfields.extend(['b', 'Unknown'])

    # Date of publication
    if book.copyright_year:
        subfields.extend(['c', str(book.copyright_year)])
    else:
        subfields.extend(['c', '[n.d.]'])

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
            subfields.extend(['a', f'{page_match.group(1)} pages'])
        else:
            subfields.extend(['a', 'pages'])
    else:
        subfields.extend(['a', 'pages'])

    # Other physical details
    subfields.extend(['b', 'illustrations'])

    # Dimensions
    subfields.extend(['c', '19 cm'])

    return Field(
        tag='300',
        indicators=[' ', ' '],
        subfields=subfields
    )


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