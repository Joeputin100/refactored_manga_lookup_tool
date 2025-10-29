#!/usr/bin/env python3
"""
Replace parse_volume_range function with fixed version
"""

def replace_volume_range():
    """Replace parse_volume_range calls with the fixed version"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Replace all calls to parse_volume_range with parse_volume_range_fixed
    if 'parse_volume_range(' in content:
        content = content.replace('parse_volume_range(', 'parse_volume_range_fixed(')
        print("✅ Successfully replaced parse_volume_range calls")
    else:
        print("⚠️ No parse_volume_range calls found")

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    return True

if __name__ == "__main__":
    replace_volume_range()