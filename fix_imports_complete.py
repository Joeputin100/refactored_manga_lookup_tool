#!/usr/bin/env python3
"""
Complete fix for import section - remove all duplicates and fix indentation
"""

def fix_imports_complete():
    """Completely fix the import section by removing duplicates"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Define the clean import section
    clean_imports = '''# Import existing core logic
from manga_lookup import (
    DeepSeekAPI,
    GoogleBooksAPI,
    VertexAIAPI,
    ProjectState,
    generate_sequential_general_barcodes,
    parse_volume_range,
    validate_barcode,
    validate_general_barcode,
    validate_series_name,
    sanitize_series_name,
)
from fix_volume_range import parse_volume_range_fixed

'''

    # Find the start and end of the corrupted import section
    # Look for the line after the initial imports
    start_marker = 'except ImportError:'
    end_marker = 'import requests'

    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("❌ Could not find start marker")
        return False

    # Find the end of the corrupted section (look for the next meaningful code)
    end_pos = content.find('import requests', start_pos)
    if end_pos == -1:
        print("❌ Could not find end marker")
        return False

    # Find the actual end of the corrupted import section
    # Look for the next line that's not an import
    lines = content[end_pos:].split('\n')
    actual_end_pos = end_pos
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith(('from ', 'import ', '    ', ')'):
            actual_end_pos = end_pos + sum(len(line) + 1 for line in lines[:i])
            break

    # Replace the corrupted section with clean imports
    new_content = content[:start_pos] + start_marker + '\n    sys.exit(1)\n\n' + clean_imports + content[actual_end_pos:]

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(new_content)

    print("✅ Successfully fixed import section completely")
    return True

if __name__ == "__main__":
    fix_imports_complete()