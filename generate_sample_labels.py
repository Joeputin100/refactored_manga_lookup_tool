#!/usr/bin/env python3
"""
Generate sample label PDF and save to file
"""

import pandas as pd
from label_generator import generate_pdf_labels

def generate_sample_labels():
    """Generate sample labels and save to file"""

    print("🎯 Generating sample label PDF...")

    # Create sample data for labels
    label_data = []
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
        label_data.append({
            'Holdings Barcode': f"TEST{i:03d}",
            'Title': f"{series} Vol. 1",
            'Author': "Various Authors",
            'Copyright Year': "2024",
            'Series Info': series,
            'Series Number': "1",
            'Call Number': "",
            'spine_label_id': "M"
        })

    if label_data:
        df = pd.DataFrame(label_data)
        pdf_data = generate_pdf_labels(df, library_name="Manga Collection Test")

        # Save to file
        filename = "manga_sample_labels.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_data)

        print(f"✅ Generated sample label PDF: {filename}")
        print(f"📊 Labels generated: {len(label_data)}")
        print(f"📁 File size: {len(pdf_data)} bytes")

        return filename
    else:
        print("❌ No data for label generation")
        return None

if __name__ == "__main__":
    generate_sample_labels()