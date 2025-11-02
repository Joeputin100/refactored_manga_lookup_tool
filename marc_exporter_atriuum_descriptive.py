#!/usr/bin/env python3
"""
MARC exporter that precisely matches Atriuum descriptive format
Based on analysis of Atriuum_Descriptive_MARC.mrc
"""
import re
from typing import List
from pymarc import Record, Field, Subfield

from manga_lookup import BookInfo


def clean_copyright_year(year):
    """Clean copyright year to remove 'c' prefix and extract 4-digit year"""
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


def format_author_inverted(author):
    """Convert author name to inverted format (Last, First)"""
    if not author:
        return ""

    # If already in inverted format, return as-is
    if ',' in author:
        return author

    # Convert "First Last" to "Last, First"
    parts = author.strip().split()
    if len(parts) >= 2:
        # Assume "First Last" format, convert to "Last, First"
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    else:
        # Single name, return as-is
        return author


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


def format_cost(msrp_cost):
    """Format cost with commas like $31,337.00"""
    if not msrp_cost:
        return "0.00"

    try:
        cost = float(msrp_cost)
        return f"${cost:,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def create_bibliographic_record(book: BookInfo) -> Record:
    """Create a bibliographic record in Atriuum descriptive format"""
    record = Record()

    # Set leader - Atriuum descriptive format: "03697cmm  2200757 i 4500"
    # cmm = computer file (not nam = language material)
    record.leader = f"00000cmm  2200000 i 4500"

    # 001 - Control Number
    record.add_field(Field(tag='001', data=f'{book.barcode}'))

    # 003 - Control Number Identifier (OCoLC)
    record.add_field(Field(tag='003', data='OCoLC'))

    # 005 - Date and Time of Latest Transaction
    from datetime import datetime
    record.add_field(Field(tag='005', data=datetime.now().strftime('%Y%m%d%H%M%S.0')))

    # 008 - Fixed-Length Data Elements - Atriuum descriptive format
    copyright_year = clean_copyright_year(getattr(book, 'copyright_year', None))
    year_str = copyright_year if copyright_year else "0000"
    # Format: "180214m20179999nyua   d 6    000 1 eng d"
    fixed_data = f"{datetime.now().strftime('%y%m%d')}m{year_str}9999nyua   d 6    000 1 eng d"
    record.add_field(Field(tag='008', data=fixed_data))

    # 010 - LCCN
    record.add_field(Field(tag='010', data='|a LCCN GOES HERE'))

    # 019 - OCLC Control Numbers
    record.add_field(Field(tag='019', data='|a OCLC CONTROL NUMBERS GO HERE'))

    # 020 - International Standard Book Number (multiple possible)
    isbn_13 = getattr(book, 'isbn_13', None)
    isbn_10 = getattr(book, 'isbn_10', None)

    if isbn_13:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[Subfield('a', isbn_13)]
        ))

    if isbn_10:
        record.add_field(Field(
            tag='020',
            indicators=[' ', ' '],
            subfields=[Subfield('a', isbn_10)]
        ))

    # 040 - Cataloging Source
    record.add_field(Field(
        tag='040',
        indicators=[' ', ' '],
        subfields=[
            Subfield('b', 'eng'),
            Subfield('e', 'rda'),
            Subfield('c', 'DLC')
        ]
    ))

    # 041 - Language Code
    record.add_field(Field(
        tag='041',
        indicators=['1', ' '],
        subfields=[
            Subfield('a', 'eng'),
            Subfield('h', 'jpn')
        ]
    ))

    # 042 - Authentication Code
    record.add_field(Field(tag='042', data='|a lccopycat'))

    # 043 - Geographic Area Code
    record.add_field(Field(tag='043', data='|a a-ja---'))

    # 050 - Library of Congress Call Number
    record.add_field(Field(tag='050', indicators=['0', '0'], data='|a PZ7.7.O38|b To 2017'))

    # 082 - Dewey Decimal Classification Number
    record.add_field(Field(tag='082', indicators=['0', '0'], data='|a 741.5/952|2 23'))

    # 100 - Main Entry - Personal Name (Author)
    authors = getattr(book, 'authors', [])
    if authors:
        # Atriuum format: "100 1 : |a INVERTED AUTHOR NAME GOES HERE|0https://id.loc.gov/authorities/names/no2011130112|eauthor,|eartist."
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=[
                Subfield('a', authors[0]),
                Subfield('0', 'https://id.loc.gov/authorities/names/no2011130112'),
                Subfield('e', 'author,'),
                Subfield('e', 'artist.')
            ]
        ))

    # 240 - Uniform Title
    record.add_field(Field(
        tag='240',
        indicators=['1', '0'],
        subfields=[
            Subfield('l', 'English'),
            Subfield('0', 'https://id.loc.gov/authorities/names/no2018017825.')
        ]
    ))

    # 245 - Title Statement
    title = getattr(book, 'book_title', f"{getattr(book, 'series_name', 'Unknown')} Volume {getattr(book, 'volume_number', 'Unknown')}")
    record.add_field(Field(
        tag='245',
        indicators=['1', '0'],
        subfields=[
            Subfield('a', title),
            Subfield('c', authors[0] if authors else "Unknown")
        ]
    ))

    # 264 - Production, Publication, Distribution, Manufacture, and Copyright Notice
    publisher = getattr(book, 'publisher_name', None)
    if publisher:
        # Publisher info
        record.add_field(Field(
            tag='264',
            indicators=[' ', '1'],
            subfields=[
                Subfield('b', publisher),
                Subfield('c', copyright_year if copyright_year else "")
            ]
        ))

        # Copyright info
        if copyright_year:
            record.add_field(Field(
                tag='264',
                indicators=[' ', '4'],
                subfields=[Subfield('c', f'c{copyright_year}.')]
            ))

    # 300 - Physical Description
    physical_desc = getattr(book, 'physical_description', None)
    if physical_desc:
        # Extract size information if available
        size_info = "19 cm"  # Default manga size
        if "inches" in physical_desc.lower() or "cm" in physical_desc.lower():
            # Extract size from description
            import re
            size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:x\s*\d+(?:\.\d+)?)?\s*(?:inches|cm|\"))', physical_desc, re.IGNORECASE)
            if size_match:
                size_info = size_match.group(1)

        record.add_field(Field(
            tag='300',
            indicators=[' ', ' '],
            subfields=[
                Subfield('a', physical_desc),
                Subfield('b', 'illustrations'),
                Subfield('c', size_info)
            ]
        ))

    # 336 - Content Type (RDA)
    record.add_field(Field(
        tag='336',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'text'),
            Subfield('b', 'txt'),
            Subfield('2', 'rdacontent.')
        ]
    ))
    record.add_field(Field(
        tag='336',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'still image'),
            Subfield('b', 'sti'),
            Subfield('2', 'rdacontent.')
        ]
    ))

    # 337 - Media Type (RDA)
    record.add_field(Field(
        tag='337',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'unmediated'),
            Subfield('b', 'n'),
            Subfield('2', 'rdamedia.')
        ]
    ))

    # 338 - Carrier Type (RDA)
    record.add_field(Field(
        tag='338',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'volume'),
            Subfield('b', 'nc'),
            Subfield('2', 'rdacarrier.')
        ]
    ))

    # 490 - Series Statement
    series_name = getattr(book, 'series_name', None)
    volume_number = getattr(book, 'volume_number', None)
    if series_name:
        subfields = [Subfield('a', series_name)]
        if volume_number:
            subfields.append(Subfield('v', str(volume_number)))
        record.add_field(Field(
            tag='490',
            indicators=[' ', ' '],
            subfields=subfields
        ))

    # 500 - General Note
    genres = getattr(book, 'genres', [])
    note_parts = []
    if genres:
        note_parts.append(" / ".join(genres))
    note_parts.append("English")
    if note_parts:
        record.add_field(Field(
            tag='500',
            indicators=[' ', ' '],
            subfields=[Subfield('a', f"Manga / {' / '.join(note_parts)}")]
        ))

    # 520 - Summary, etc.
    description = getattr(book, 'description', None)
    if description:
        record.add_field(Field(
            tag='520',
            indicators=[' ', ' '],
            subfields=[Subfield('a', description)]
        ))

    # 546 - Language Note
    record.add_field(Field(
        tag='546',
        indicators=[' ', ' '],
        subfields=[Subfield('a', 'Text in English, translated from the Japanese.')]
    ))

    # 650 - Subject Added Entry - Topical Term
    if genres:
        for i, genre in enumerate(genres[:4], 1):
            record.add_field(Field(
                tag='650',
                indicators=[' ', '0'],
                subfields=[
                    Subfield('a', genre),
                    Subfield('2', 'lcgft')
                ]
            ))

    # 856 - Electronic Location and Access
    cover_image = getattr(book, 'cover_image', None) or getattr(book, 'cover_image_url', None)
    if cover_image:
        record.add_field(Field(
            tag='856',
            indicators=[' ', ' '],
            subfields=[
                Subfield('u', cover_image),
                Subfield('3', 'Cover image')
            ]
        ))

    # 907 - Local Processing Data
    record.add_field(Field(tag='907', data='|a .b390757019'))

    # 852 - Location (Atriuum descriptive format)
    call_number = create_call_number(book)
    msrp_cost = getattr(book, 'msrp_cost', 0)
    formatted_cost = format_cost(msrp_cost)

    record.add_field(Field(
        tag='852',
        indicators=[' ', ' '],
        subfields=[
            Subfield('a', 'Main Library'),
            Subfield('b', 'Main Library'),
            Subfield('h', call_number),
            # NOTE: Bibliographic records should NOT have barcodes in 852 field
            # Barcodes belong only in holding records
            Subfield('9', formatted_cost),
            Subfield('x', '{BookSysInc::00005403::    ::BookSysInc}'),
            Subfield('3', datetime.now().strftime('%m/%d/%Y'))
        ]
    ))

    return record


# Note: Atriuum descriptive format uses SINGLE records with both bibliographic
# and holding information. No separate holding records are created.


def export_books_to_marc_atriuum_descriptive(books: List[BookInfo]) -> bytes:
    """
    Export a list of BookInfo objects to MARC21 format matching Atriuum descriptive exactly.
    Atriuum descriptive uses SINGLE RECORDS with both bibliographic and holding information.
    Returns MARC data as bytes.
    """
    from datetime import datetime
    records = []

    for book in books:
        # Create SINGLE record with both bibliographic and holding information
        # This matches the Atriuum descriptive sample format
        record = create_bibliographic_record(book)

        # Add barcode to 852 field (Atriuum descriptive includes barcode in bibliographic record)
        if '852' in record:
            # Remove the existing 852 field
            record.remove_field(record['852'])

        # Recreate 852 field WITH barcode
        call_number = create_call_number(book)
        msrp_cost = getattr(book, 'msrp_cost', 0)
        formatted_cost = format_cost(msrp_cost)

        record.add_field(Field(
            tag='852',
            indicators=[' ', ' '],
            subfields=[
                Subfield('a', 'Main Library'),
                Subfield('b', 'Main Library'),
                Subfield('h', call_number),
                Subfield('p', book.barcode if book.barcode else 'UNKNOWN'),  # Barcode IN bibliographic record
                Subfield('9', formatted_cost),
                Subfield('x', '{BookSysInc::00005403::    ::BookSysInc}'),
                Subfield('3', datetime.now().strftime('%m/%d/%Y'))
            ]
        ))

        records.append(record)

    # Convert records to MARC binary format
    marc_data = b''
    for record in records:
        marc_data += record.as_marc()

    return marc_data


if __name__ == "__main__":
    # Test the descriptive exporter
    class TestBook:
        def __init__(self):
            self.series_name = "Fairy Tail"
            self.volume_number = 60
            self.title = "Fairy Tail Volume 60"
            self.authors = ["Mashima, Hiro"]
            self.isbn_13 = "9781632361088"
            self.publisher_name = "Kodansha Comics"
            self.copyright_year = "c2016."
            self.physical_description = "192 p."
            self.description = "The epic conclusion to the Fairy Tail series!"
            self.genres = ["Manga", "Fantasy", "Action"]
            self.cover_image = "https://www.kodansha.us/uploads/book_cover_image/9781632361088.jpg"
            self.barcode = "FAIRY060"
            self.msrp_cost = 31337.00

    test_book = TestBook()
    marc_data = export_books_to_marc_atriuum_descriptive([test_book])

    print(f"Generated {len(marc_data)} bytes of MARC data")

    # Save to file for inspection
    with open('test_atriuum_descriptive.mrc', 'wb') as f:
        f.write(marc_data)

    print("MARC data saved to test_atriuum_descriptive.mrc")