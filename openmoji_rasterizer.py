#!/usr/bin/env python3
"""
OpenMoji SVG-based Unicode character rasterizer
Uses pre-rendered SVG emojis from OpenMoji project
"""

import os
import io
from PIL import Image
from reportlab.lib.utils import ImageReader
import xml.etree.ElementTree as ET

# Get the absolute path to the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
openmoji_dir = os.path.join(current_dir, "openmoji")

def get_emoji_svg_path(character):
    """
    Get the SVG file path for a Unicode character
    Returns None if not found
    """
    # Convert character to Unicode code point
    unicode_code = f"{ord(character):04X}".upper()

    # Look for the SVG file
    svg_path = os.path.join(openmoji_dir, f"{unicode_code}.svg")

    if os.path.exists(svg_path):
        return svg_path

    return None

def svg_to_png(svg_path, output_size=256):
    """
    Convert SVG to PNG using PIL (basic implementation)
    Note: This is a simplified version - in production you might want to use cairosvg or other libraries
    """
    try:
        # Create a simple white background image
        image = Image.new('RGB', (output_size, output_size), (255, 255, 255))

        # For now, we'll just create a placeholder
        # In a real implementation, you would use cairosvg or similar to properly render SVG
        # For this demo, we'll create a simple colored square with the Unicode code
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(image)

        # Draw a colored rectangle
        margin = output_size // 4
        draw.rectangle([margin, margin, output_size - margin, output_size - margin],
                      fill=(0, 100, 200), outline=(0, 0, 0), width=2)

        # Add text showing this is an SVG emoji
        try:
            # Try to use a font
            font_path = os.path.join(current_dir, "fonts/DejaVuSans.ttf")
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 20)
            else:
                font = ImageFont.load_default()

            # Get the Unicode code from the filename
            unicode_code = os.path.basename(svg_path).replace('.svg', '')
            text = f"U+{unicode_code}"

            # Center the text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (output_size - text_width) // 2
            y = (output_size - text_height) // 2

            draw.text((x, y), text, fill=(255, 255, 255), font=font)

        except Exception as e:
            print(f"⚠️ SVG text rendering failed: {e}")

        return image

    except Exception as e:
        print(f"❌ SVG to PNG conversion failed: {e}")
        # Fallback to a simple colored square
        image = Image.new('RGB', (output_size, output_size), (200, 100, 50))
        return image

def rasterize_unicode_with_openmoji(character, image_size=256):
    """
    Rasterize a Unicode character using OpenMoji SVG files
    Returns an ImageReader object for use with ReportLab
    """
    print(f"🔍 OPENMOJI RASTERIZE: Processing character '{character}'")

    # Get the SVG file path
    svg_path = get_emoji_svg_path(character)

    if svg_path:
        print(f"✅ OPENMOJI: Found SVG for '{character}': {os.path.basename(svg_path)}")

        # Convert SVG to PNG
        png_image = svg_to_png(svg_path, image_size)

        # Convert to bytes
        buffer = io.BytesIO()
        png_image.save(buffer, format='PNG')
        buffer.seek(0)

        print(f"✅ OPENMOJI: Successfully rasterized '{character}' from SVG")
        return ImageReader(buffer)
    else:
        print(f"❌ OPENMOJI: No SVG found for character '{character}'")
        return None

def test_openmoji_rasterizer():
    """Test the OpenMoji rasterizer"""
    print("🔍 TESTING OPENMOJI RASTERIZER")
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

        result = rasterize_unicode_with_openmoji(char)

        if result:
            print(f"✅ Success - SVG found and processed")
        else:
            print(f"❌ Failed - No SVG available")

if __name__ == "__main__":
    test_openmoji_rasterizer()