#!/usr/bin/env python3
"""
Verify author last name extraction is correct
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from marc_exporter import get_author_initials

print("🔍 VERIFYING AUTHOR LAST NAME EXTRACTION")
print("=" * 50)

# Test cases for author last name extraction
test_cases = [
    ("Mashima, Hiro", "MAS"),  # Inverted format
    ("Hiro Mashima", "MAS"),   # Normal format
    ("Kishimoto, Masashi", "KIS"),
    ("Masashi Kishimoto", "KIS"),
    ("Oda, Eiichiro", "ODA"),
    ("Eiichiro Oda", "ODA"),
    ("Isayama, Hajime", "ISA"),
    ("Hajime Isayama", "ISA"),
    ("A", "AXX"),  # Short name padding
    ("", "UNK"),   # Empty
    (None, "UNK")   # None
]

print("\nTesting get_author_initials() function:")
print("-" * 40)

all_correct = True
for author_input, expected in test_cases:
    result = get_author_initials(author_input)
    status = "✅ CORRECT" if result == expected else "❌ WRONG"
    print(f"{status}: '{author_input}' -> '{result}' (expected: '{expected}')")
    if result != expected:
        all_correct = False

print("\n" + "=" * 50)
if all_correct:
    print("🎉 ALL TESTS PASSED - Author last name extraction is working correctly!")
    print("\n📋 CONFIRMATION:")
    print("  - 'Mashima, Hiro' → 'MAS' (first 3 letters of LAST NAME)")
    print("  - 'Hiro Mashima' → 'MAS' (first 3 letters of LAST NAME)")
    print("  - NOT using initials, using last name letters")
else:
    print("⚠️  Some tests failed - please check the implementation")