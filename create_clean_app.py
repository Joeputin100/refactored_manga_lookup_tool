#!/usr/bin/env python3
"""
Create a clean version of the Streamlit app by extracting the good parts
"""

def create_clean_app():
    """Create a clean version of the app"""

    # Read the current file
    with open('app_new_workflow_backup.py', 'r') as f:
        lines = f.readlines()

    # Find the clean part (up to line 44)
    clean_lines = lines[:44]

    # Add the rest of the file starting from after the corrupted section
    # Look for the next meaningful code after the imports
    for i in range(44, len(lines)):
        line = lines[i]
        # Skip empty lines and corrupted imports
        if line.strip() and not line.strip().startswith(('    ', 'from ', 'import ')) and ')' not in line:
            clean_lines.extend(lines[i:])
            break

    # Write the clean content
    with open('app_new_workflow.py', 'w') as f:
        f.writelines(clean_lines)

    print("✅ Successfully created clean app version")
    return True

if __name__ == "__main__":
    create_clean_app()