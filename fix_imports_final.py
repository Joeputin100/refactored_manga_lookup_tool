#!/usr/bin/env python3
"""
Fix import section indentation errors in Streamlit app
"""

def fix_imports_final():
    """Fix the import section with proper indentation"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        lines = f.readlines()

    # Find and replace the corrupted import section (lines 30-50)
    new_lines = []
    i = 0
    while i < len(lines):
        if i >= 29 and i <= 49:  # Lines 30-50
            # Replace this section with clean, properly formatted imports
            new_lines.extend([
                '# Import existing core logic\n',
                'from manga_lookup import (\n',
                '    DeepSeekAPI,\n',
                '    GoogleBooksAPI,\n',
                '    VertexAIAPI,\n',
                '    ProjectState,\n',
                '    generate_sequential_general_barcodes,\n',
                '    parse_volume_range,\n',
                '    validate_barcode,\n',
                '    validate_general_barcode,\n',
                '    validate_series_name,\n',
                '    sanitize_series_name,\n',
                ')\n',
                'from fix_volume_range import parse_volume_range_fixed\n',
                '\n'
            ])
            i = 50  # Skip to after the replaced section
        else:
            new_lines.append(lines[i])
            i += 1

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.writelines(new_lines)

    print("✅ Successfully fixed import section indentation")
    return True

if __name__ == "__main__":
    fix_imports_final()