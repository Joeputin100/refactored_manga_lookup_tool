#!/usr/bin/env python3
"""
Generate sample MARC file and save to file
"""

from marc_exporter import export_books_to_marc
from manga_lookup import BookInfo

def generate_sample_marc():
    """Generate sample MARC file and save to file"""

    print("🎯 Generating sample MARC file...")

    # Create sample books for export
    sample_books = []
    test_series = [
        "Attack on Titan",
        "One Piece",
        "Naruto",
        "Spy x Family",
        "Berserk",
        "Death Note",
        "Haikyuu!!",
        "Tokyo Ghoul",
        "My Hero Academia",
        "Demon Slayer: Kimetsu no Yaiba"
    ]

    for i, series in enumerate(test_series, 1):
        book = BookInfo(
            series_name=series,
            volume_number=1,
            book_title=f"{series} Volume 1",
            authors=["Various Authors"],
            msrp_cost=9.99,
            isbn_13=f"978123456789{i}",
            publisher_name="Sample Publisher",
            copyright_year=2024,
            description=f"First volume of the popular manga series {series}",
            physical_description="192 pages",
            genres=["Manga", "Action"],
            warnings=[],
            barcode=f"TEST{i:03d}",
            cover_image_url=None
        )
        sample_books.append(book)

    marc_data = export_books_to_marc(sample_books)

    # Save to file
    filename = "manga_sample_marc.mrc"
    with open(filename, "wb") as f:
        f.write(marc_data)

    print(f"✅ Generated sample MARC file: {filename}")
    print(f"📊 Records generated: {len(sample_books)}")
    print(f"📁 File size: {len(marc_data)} bytes")

    return filename

if __name__ == "__main__":
    generate_sample_marc()