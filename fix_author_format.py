#!/usr/bin/env python3
"""
Fix author names to use proper inverted comma separated format
"""

import re

def invert_author_name(name):
    """Convert "First Last" to "Last, First" format"""
    if not name or not isinstance(name, str):
        return name

    # Handle common patterns
    parts = name.strip().split()
    if len(parts) >= 2:
        # If it's already in inverted format, leave it
        if ',' in name:
            return name
        # Convert "First Last" to "Last, First"
        last_name = parts[-1]
        first_names = ' '.join(parts[:-1])
        return f"{last_name}, {first_names}"

    # Single name - leave as is
    return name

if __name__ == "__main__":
    print("🔄 Testing author name inversion...")
    test_names = ["Eiichiro Oda", "Masashi Kishimoto", "Hajime Isayama", "Oda, Eiichiro", "One Name"]
    for name in test_names:
        inverted = invert_author_name(name)
        print(f"  {name} -> {inverted}")