#!/usr/bin/env python3
"""
Simple fix for the authors TypeError
"""

# Read the file
with open('app_new_workflow.py', 'r') as f:
    lines = f.readlines()

# Fix line 742 (0-indexed line 741)
old_line = '                        st.write(f"**Authors:** {", ".join(result[\'authors\'])}")\n'
new_line = '                        st.write(f"**Authors:** {", ".join([str(a) for a in result[\'authors\']])}")\n'

if lines[741] == old_line:
    lines[741] = new_line
    print("✅ Fixed line 742")
else:
    print(f"❌ Line doesn't match. Current: {repr(lines[741])}")

# Write the fixed content
with open('app_new_workflow.py', 'w') as f:
    f.writelines(lines)

print("✅ File updated")