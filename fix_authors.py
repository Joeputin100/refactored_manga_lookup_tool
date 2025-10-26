#!/usr/bin/env python3
"""
Fix the authors TypeError in app_new_workflow.py
"""

import re

# Read the file
with open('app_new_workflow.py', 'r') as f:
    content = f.read()

# Fix the authors line - handle both list and string formats
old_line = 'st.write(f"**Authors:** {", ".join(result[\'authors\'])}")'
new_line = 'st.write(f"**Authors:** {", ".join([str(a) for a in result[\"authors\"]] if isinstance(result[\"authors\"], list) else [result[\"authors\"]])}")'

content = content.replace(old_line, new_line)

# Write the fixed content
with open('app_new_workflow.py', 'w') as f:
    f.write(content)

print("✅ Fixed authors TypeError")