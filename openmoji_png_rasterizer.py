#!/usr/bin/env python3
"""
OpenMoji PNG-based Unicode character rasterizer
Uses pre-rendered PNG emojis from OpenMoji project
"""

import os
import io
from PIL import Image
from reportlab.lib.utils import ImageReader

# Get the absolute path to the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
openmoji_png_dir = os.path.join(current_dir, "openmoji_png")

def get_emoji_png_path(character):
    """
    Get the PNG file path for a Unicode character
    Returns None if not found
    """
    # Convert character to Unicode code point
    unicode_code = f"{ord(character):04X}".upper()

    # Look for the PNG file
    png_path = os.path.join(openmoji_png_dir, f"{unicode_code}.png")

    if os.path.exists(png_path):
        return png_path

    return None

def rasterize_unicode_with_openmoji_png(character, output_size=256):
    """
    Rasterize a Unicode character using OpenMoji PNG files
    Returns an ImageReader object for use with ReportLab
    """
    print(f"🔍 OPENMOJI PNG RASTERIZE: Processing character '{character}'")

    # Get the PNG file path
    png_path = get_emoji_png_path(character)

    if png_path:
        print(f"✅ OPENMOJI PNG: Found PNG for '{character}': {os.path.basename(png_path)}")

        try:
            # Open the PNG file
            png_image = Image.open(png_path)

            # Convert to RGB if needed (handle transparency)
            if png_image.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', png_image.size, (255, 255, 255))
                if png_image.mode == 'P':
                    png_image = png_image.convert('RGBA')
                if png_image.mode == 'RGBA':
                    background.paste(png_image, mask=png_image.split()[-1])
                    png_image = background
                else:
                    png_image = png_image.convert('RGB')
            else:
                png_image = png_image.convert('RGB')

            # Resize to desired output size
            png_image = png_image.resize((output_size, output_size), Image.Resampling.LANCZOS)

            # Convert to bytes
            buffer = io.BytesIO()
            png_image.save(buffer, format='PNG')
            buffer.seek(0)

            print(f"✅ OPENMOJI PNG: Successfully rasterized '{character}' from PNG")
            return ImageReader(buffer)

        except Exception as e:
            print(f"❌ OPENMOJI PNG: Failed to process PNG for '{character}': {e}")
            return None
    else:
        print(f"❌ OPENMOJI PNG: No PNG found for character '{character}'")
        return None

def test_openmoji_png_rasterizer():
    """Test the OpenMoji PNG rasterizer"""
    print("🔍 TESTING OPENMOJI PNG RASTERIZER")
    print("=" * 60)

    test_characters = [
        ('🐀', 'Rat emoji'),
        ('📚', 'Books emoji'),
        ('🎯', 'Target emoji'),
        ('♡', 'Heart symbol'),
        ('☆', 'Star symbol'),
    ]

    for char, description in test_characters:
        print(f"\n🎯 Testing: {char} ({description})")

        result = rasterize_unicode_with_openmoji_png(char)

        if result:
            print(f"✅ Success - PNG found and processed")
        else:
            print(f"❌ Failed - No PNG available")

if __name__ == "__main__":
    test_openmoji_png_rasterizer()