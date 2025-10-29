#!/usr/bin/env python3
"""
Fix the parse_volume_range function to handle mixed formats
"""

import re

def parse_volume_range_fixed(volume_range: str) -> list[int]:
    """
    Parse a volume range string into a list of volume numbers.

    Args:
        volume_range: String like "1-5" or "1,3,5" or "1-5,8,10" or "5, 7, 9-11"

    Returns:
        List of volume numbers
    """
    import re

    if not volume_range:
        return []

    # Clean the input - keep spaces, digits, commas, and dashes
    volume_range = ''.join(c for c in volume_range if c.isdigit() or c in '-, ')
    volume_range = volume_range.replace(' ', '')  # Remove spaces

    try:
        volumes = []

        # Split by commas first to handle mixed formats
        parts = volume_range.split(',')

        for part in parts:
            if '-' in part:
                # Handle ranges like '1-5' or '9-11'
                start, end = part.split('-')
                start_num = int(start)
                end_num = int(end)
                volumes.extend(range(start_num, end_num + 1))
            else:
                # Handle single numbers
                if part:  # Skip empty parts
                    volumes.append(int(part))

        return sorted(set(volumes))  # Remove duplicates and sort

    except (ValueError, IndexError):
        # If parsing fails, return empty list
        return []

# Read the current manga_lookup.py
with open('manga_lookup.py', 'r') as f:
    content = f.read()

# Find the parse_volume_range function using regex
pattern = r'def parse_volume_range\(volume_range: str\) -> list\[int\]:\s*\"\"\"[\s\S]*?\"\"\"[\s\S]*?return \[\]'

# Get the source of the new function
import inspect
new_function_source = inspect.getsource(parse_volume_range_fixed)

# Replace the function
if re.search(pattern, content):
    content = re.sub(pattern, new_function_source, content)
    with open('manga_lookup.py', 'w') as f:
        f.write(content)
    print('✅ Fixed parse_volume_range function')
else:
    print('❌ Could not find the function to replace')

# Test the fix
print('\nTesting fixed function:')
test_ranges = [
    '5, 7, 9-11',
    '1-10',
    '1,3,5,7',
    '1-5,8,10'
]

for test_range in test_ranges:
    result = parse_volume_range_fixed(test_range)
    print(f'{test_range} -> {result}')