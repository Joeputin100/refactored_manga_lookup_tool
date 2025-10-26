#!/usr/bin/env python3
"""
Updated Label Generator for Manga Collection
This is the version that should replace the original label_generator.py
Changes:
- Label 3: "Manga Collection" on two lines instead of one
- Label 1: Add MSRP ($0.00) to Line 3 after holding barcode text
"""

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap

# Label dimensions (in inches)
LABEL_WIDTH = 2.625
LABEL_HEIGHT = 1.0
LABELS_PER_ROW = 3
LABELS_PER_COLUMN = 10
MARGIN_LEFT = 0.15625
MARGIN_TOP = 0.5

# Font sizes
FONT_SIZE_SMALL = 6
FONT_SIZE_MEDIUM = 8
FONT_SIZE_LARGE = 10

def generate_pdf_labels(books_data, output_stream=None):
    """
    Generate PDF labels for manga books

    Args:
        books_data: List of dictionaries with book information
        output_stream: Optional output stream (default: creates BytesIO)

    Returns:
        BytesIO object with PDF content
    """
    if output_stream is None:
        output_stream = io.BytesIO()

    # Create PDF canvas
    c = canvas.Canvas(output_stream, pagesize=letter)

    # Calculate positions
    page_width, page_height = letter
    label_width_points = LABEL_WIDTH * inch
    label_height_points = LABEL_HEIGHT * inch

    # Process each book
    for i, book in enumerate(books_data):
        # Calculate position
        row = i // LABELS_PER_ROW
        col = i % LABELS_PER_ROW

        # Check if we need a new page
        if row >= LABELS_PER_COLUMN:
            c.showPage()
            row = 0
            col = i % LABELS_PER_ROW

        x = MARGIN_LEFT * inch + col * label_width_points
        y = page_height - (MARGIN_TOP * inch + (row + 1) * label_height_points)

        # Draw label border (for debugging)
        # c.rect(x, y, label_width_points, label_height_points)

        # Draw label content
        draw_label(c, book, x, y, label_width_points, label_height_points)

    c.save()
    return output_stream

def draw_label(c, book, x, y, width, height):
    """Draw a single label"""
    # Extract book data with defaults
    title = book.get('title', 'Unknown Title')
    volume = book.get('volume', '')
    barcode = book.get('barcode', 'NOBARCODE')
    holding = book.get('holding', 'MANGA')

    # Calculate positions
    padding = 0.05 * inch
    line_height = 0.12 * inch

    # Line 1: Title (truncated if too long)
    title_y = y + height - padding - line_height
    title_text = truncate_text(title, FONT_SIZE_MEDIUM, width - 2*padding)
    c.setFont("Helvetica-Bold", FONT_SIZE_MEDIUM)
    c.drawString(x + padding, title_y, title_text)

    # Line 2: Volume
    volume_y = title_y - line_height
    volume_text = f"Vol. {volume}" if volume else ""
    c.setFont("Helvetica", FONT_SIZE_MEDIUM)
    c.drawString(x + padding, volume_y, volume_text)

    # Line 3: Holding and Barcode with MSRP
    holding_y = volume_y - line_height

    # MODIFICATION: Add MSRP ($0.00) after holding barcode
    holding_text = f"{holding} {barcode} - $0.00"
    c.setFont("Helvetica", FONT_SIZE_SMALL)
    c.drawString(x + padding, holding_y, holding_text)

    # Line 4 & 5: "Manga Collection" - MODIFIED to be two lines
    collection_y1 = holding_y - line_height
    collection_y2 = collection_y1 - line_height * 0.8

    # MODIFICATION: Split "Manga Collection" into two lines
    c.setFont("Helvetica-Oblique", FONT_SIZE_SMALL)
    c.drawString(x + padding, collection_y1, "Manga")
    c.drawString(x + padding, collection_y2, "Collection")

def truncate_text(text, font_size, max_width):
    """Truncate text to fit within max_width"""
    if len(text) <= 20:  # Reasonable limit for manga titles
        return text

    # Simple truncation for now
    if len(text) > 25:
        return text[:22] + "..."
    return text