#!/usr/bin/env python3
"""
Fix the validate_series_name function regex pattern
"""

import re

# Read the file
with open('manga_lookup.py', 'r') as f:
    content = f.read()

# Find and fix the regex pattern
# The issue is that \w is being escaped as \\w
old_pattern = r"if not re.match(r'^[\\\\w\\\\s\\-\\.\\,\\'()!?:]+\$', series_name):"
new_pattern = "if not re.match(r'^[\\w\\s\\-\\.\\,\\'()!?:]+$', series_name):"

# Replace the pattern
content = content.replace(
    "if not re.match(r'^[\\\\w\\\\s\\-\\.\\,\\'()!?:]+$', series_name):",
    "if not re.match(r'^[\\w\\s\\-\\.\\,\\'()!?:]+$', series_name):"
)

# Write the file back
with open('manga_lookup.py', 'w') as f:
    f.write(content)

print("✅ Fixed validate_series_name regex pattern")

# Test the fix
from manga_lookup import validate_series_name

test_names = [
    'One piece',
    'One Piece',
    'Naruto',
    'Attack on Titan',
    'Dragon Ball Z',
    'Tokyo Ghoul:re',
]

print("\nTesting fixed function:")
for name in test_names:
    result = validate_series_name(name)
    print(f'  \"{name}\" ({len(name)} chars): {result}')