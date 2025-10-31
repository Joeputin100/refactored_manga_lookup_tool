#!/usr/bin/env python3
"""
Simple test for the specific MARC fixes we applied
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from marc_exporter import clean_copyright_year, create_call_number, get_author_initials

print("Testing specific MARC fixes...")

# Test 1: Copyright year cleaning
print("\n1. Copyright Year Cleaning:")
test_cases = [
    ("c2008.", "2008"),
    ("c2010.", "2010"),
    ("c2015.", "2015"),
    ("2008", "2008"),
    ("c08.", "2008"),
    ("c98.", "1998")
]

for input_year, expected in test_cases:
    result = clean_copyright_year(input_year)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"  {status}: '{input_year}' -> '{result}' (expected: '{expected}')")

# Test 2: Author initials
print("\n2. Author Initials:")
author_tests = [
    ("Masashi Kishimoto", "KIS"),
    ("Hiro Mashima", "MAS"),
    ("Eiichiro Oda", "ODA"),
    ("Unknown", "UNK"),
    ("Oda", "ODA")
]

for author, expected in author_tests:
    result = get_author_initials(author)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"  {status}: '{author}' -> '{result}' (expected: '{expected}')")

# Test 3: Call number format
print("\n3. Call Number Format:")

class MockBook:
    def __init__(self, authors, copyright_year, barcode):
        self.authors = authors
        self.copyright_year = copyright_year
        self.barcode = barcode

# Test with Fairy Tail author
book = MockBook(["Hiro Mashima"], "c2010.", "FAIRY001")
call_num = create_call_number(book)
print(f"  Call number: {call_num}")
print(f"  Expected format: FIC MAS 2010 FAIRY001")

print("\n✅ All specific fixes tested!")