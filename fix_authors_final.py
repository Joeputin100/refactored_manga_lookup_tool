#!/usr/bin/env python3
"""
Final fix for the authors TypeError
"""

# Read the file
with open('app_new_workflow.py', 'r') as f:
    lines = f.readlines()

# Fix line 742
line_742 = lines[741]
if "join(result['authors'])" in line_742:
    lines[741] = line_742.replace("join(result['authors'])", "join([str(a) for a in result['authors']])")
    print("✅ Fixed authors line")
else:
    print(f"❌ Could not find the line to fix. Current: {line_742}")

# Write the fixed content
with open('app_new_workflow.py', 'w') as f:
    f.writelines(lines)

print("✅ File updated")