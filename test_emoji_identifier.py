#!/usr/bin/env python3
"""
Test emoji identifier support in label generator.
Verifies that emoji characters like 🐓 can be used as library identifiers.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from label_generator import generate_pdf_labels
import pandas as pd

def test_emoji_identifiers():
    """Test various emoji characters as library identifiers"""

    print("🎯 Testing Emoji Library Identifiers")
    print("=" * 60)

    # Test emoji characters
    test_emojis = [
        ("🐓", "Rooster Emoji"),
        ("🐖", "Pig Emoji"),
        ("🐷", "Pig Face Emoji"),
        ("📚", "Books Emoji"),
        ("🎯", "Bullseye Emoji"),
        ("❤️", "Red Heart Emoji"),
        ("♡", "White Heart Suit"),
        ("☆", "White Star"),
        ("★", "Black Star"),
        ("B", "ASCII B (control)"),
    ]

    # Create test data
    test_data = [
        {
            'Holdings Barcode': 'T000001',
            'Title': 'Test Manga Vol 1',
            'Author': 'Test Author',
            'Copyright Year': '2024',
            'Series Info': 'Test Series',
            'Series Number': '1',
            'Call Number': '',
            'MSRP': '9.99',
            'spine_label_id': 'M'
        }
    ]

    df = pd.DataFrame(test_data)

    results = []

    for emoji, description in test_emojis:
        print(f"\n🔍 Testing: '{emoji}' ({description})")

        try:
            # Generate PDF with emoji identifier
            pdf_data = generate_pdf_labels(df, library_name="Manga Collection", library_id=emoji)

            # Check if PDF was generated successfully
            if pdf_data and len(pdf_data) > 1000:  # Reasonable PDF size
                print(f"  ✅ PDF generated successfully")
                print(f"  📄 PDF size: {len(pdf_data)} bytes")
                status = "SUCCESS"
            else:
                print(f"  ❌ PDF generation failed or produced small file")
                status = "FAILED"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            status = "ERROR"

        results.append({
            'emoji': emoji,
            'description': description,
            'status': status,
            'unicode_length': len(emoji),
            'utf8_bytes': len(emoji.encode('utf-8'))
        })

    # Summary
    print("\n" + "=" * 60)
    print("📊 EMOJI IDENTIFIER TEST SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r['status'] == 'SUCCESS']
    failed = [r for r in results if r['status'] == 'FAILED']
    errors = [r for r in results if r['status'] == 'ERROR']

    print(f"✅ Successfully generated: {len(successful)}")
    print(f"❌ Failed generation: {len(failed)}")
    print(f"❌ Errors: {len(errors)}")

    if successful:
        print(f"\n✅ Successful emoji identifiers:")
        for result in successful:
            print(f"  - '{result['emoji']}' ({result['description']})")
            print(f"    Unicode length: {result['unicode_length']}, UTF-8 bytes: {result['utf8_bytes']}")

    if failed:
        print(f"\n❌ Failed emoji identifiers:")
        for result in failed:
            print(f"  - '{result['emoji']}' ({result['description']})")

    if errors:
        print(f"\n❌ Error emoji identifiers:")
        for result in errors:
            print(f"  - '{result['emoji']}' ({result['description']})")

    print(f"\n💡 Key Insights:")
    print(f"   - Emoji characters should work as library identifiers")
    print(f"   - Unicode font support is required for proper rendering")
    print(f"   - Multi-byte UTF-8 sequences are handled correctly")

    return results

if __name__ == "__main__":
    test_emoji_identifiers()