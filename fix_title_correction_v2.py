#!/usr/bin/env python3
"""
Fix volume title correction in Streamlit app - Version 2
"""

def fix_volume_title_correction():
    """Fix the volume title correction logic in the Streamlit app"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        lines = f.readlines()

    # Find and replace the title correction section (lines 1264-1274)
    for i in range(len(lines)):
        if i >= 1263 and i <= 1273:  # 0-indexed, so lines 1264-1274 are indices 1263-1273
            if i == 1263:  # Line 1264
                lines[i] = '                # Apply title correction rules\n'
            elif i == 1264:  # Line 1265
                lines[i] = '                corrected_title = book.book_title or f"{series_name} Vol. {book.volume_number}"\n'
            elif i == 1265:  # Line 1266
                lines[i] = '\n'
            elif i == 1266:  # Line 1267
                lines[i] = '                # Rule 1: If title doesn\'t contain series name, prepend it\n'
            elif i == 1267:  # Line 1268
                lines[i] = '                if series_name.lower() not in corrected_title.lower():\n'
            elif i == 1268:  # Line 1269
                lines[i] = '                    corrected_title = f"{series_name} {corrected_title}"\n'
            elif i == 1269:  # Line 1270
                lines[i] = '\n'
            elif i == 1270:  # Line 1271
                lines[i] = '                # Rule 2: If title doesn\'t contain volume number, append it\n'
            elif i == 1271:  # Line 1272
                lines[i] = '                if f"vol" not in corrected_title.lower() and f"volume" not in corrected_title.lower():\n'
            elif i == 1272:  # Line 1273
                lines[i] = '                    corrected_title = f"{corrected_title} Vol. {book.volume_number}"\n'
            elif i == 1273:  # Line 1274
                lines[i] = '\n'

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.writelines(lines)

    print("✅ Successfully updated volume title correction logic")
    return True

if __name__ == "__main__":
    fix_volume_title_correction()