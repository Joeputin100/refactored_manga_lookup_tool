#!/usr/bin/env python3
"""
Fix the validate_series_name function regex pattern by replacing \\w with \w
"""

# Read the file as bytes
with open('manga_lookup.py', 'rb') as f:
    content = f.read()

# The problematic pattern: \\w (double backslash + w)
# We need to replace it with \w (single backslash + w)
old_pattern = b"\\\\w"
new_pattern = b"\\w"

# Count occurrences before replacement
old_count = content.count(old_pattern)
print(f"Found {old_count} occurrences of \\w (double backslash)")

# Replace the pattern
content = content.replace(old_pattern, new_pattern)

# Count occurrences after replacement
new_count = content.count(new_pattern)
print(f"Now have {new_count} occurrences of \w (single backslash)")

# Write the file back
with open('manga_lookup.py', 'wb') as f:
    f.write(content)

print("✅ Fixed regex pattern in validate_series_name function")

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