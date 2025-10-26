#!/usr/bin/env python3
"""
Test script to verify label generator works
"""

import sys
import os
import pandas as pd

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from label_generator import generate_pdf_labels

def test_label_generator():
    """Test the label generator with sample data"""
    print("🔍 Testing label generator...")

    # Create sample data
    sample_data = [
        {
            'Holdings Barcode': 'TEST000001',
            'Title': 'Attack on Titan Vol. 1',
            'Author': 'Hajime Isayama',
            'Copyright Year': '2012',
            'Series Info': 'Attack on Titan',
            'Series Number': '1',
            'Call Number': '',
            'spine_label_id': 'M'
        },
        {
            'Holdings Barcode': 'TEST000002',
            'Title': 'One Piece Vol. 1',
            'Author': 'Eiichiro Oda',
            'Copyright Year': '1997',
            'Series Info': 'One Piece',
            'Series Number': '1',
            'Call Number': '',
            'spine_label_id': 'M'
        }
    ]

    df = pd.DataFrame(sample_data)

    try:
        pdf_data = generate_pdf_labels(df, library_name="Manga Collection Test")
        print(f"✅ Label PDF generated successfully! Size: {len(pdf_data)} bytes")

        # Save the test PDF
        with open("test_labels.pdf", "wb") as f:
            f.write(pdf_data)
        print("✅ Test PDF saved as 'test_labels.pdf'")

        return True
    except Exception as e:
        print(f"❌ Label generation failed: {e}")
        return False

if __name__ == "__main__":
    test_label_generator()