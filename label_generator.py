#!/usr/bin/env python3
"""
Label Generator for Manga Lookup Tool

Generates printable labels for manga volumes in PDF format.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests


def generate_pdf_sheet(label_data: list[dict]) -> bytes:
    """
    Generate a PDF sheet with labels for manga volumes.

    Args:
        label_data: List of dictionaries with label information

    Returns:
        PDF data as bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Label dimensions (Avery 5160 template)
    labels_per_row = 3
    labels_per_column = 10
    label_width = 2.625 * inch
    label_height = 1.0 * inch
    margin_left = 0.1875 * inch
    margin_top = 0.5 * inch
    horizontal_gap = 0.125 * inch
    vertical_gap = 0.0 * inch

    current_label = 0
    total_labels = len(label_data)

    for row in range(labels_per_column):
        for col in range(labels_per_row):
            if current_label >= total_labels:
                break

            # Calculate position
            x = margin_left + col * (label_width + horizontal_gap)
            y = letter[1] - margin_top - (row + 1) * label_height + vertical_gap

            # Draw label border (optional)
            # c.rect(x, y, label_width, label_height)

            # Draw label content
            draw_label(c, x, y, label_width, label_height, label_data[current_label])

            current_label += 1

        if current_label >= total_labels:
            break

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def draw_label(c, x: float, y: float, width: float, height: float, label_info: dict) -> None:
    """
    Draw a single label with manga information.

    Args:
        c: Canvas object
        x: X position
        y: Y position
        width: Label width
        height: Label height
        label_info: Dictionary with label data
    """
    # Label content margins
    margin = 0.05 * inch
    content_width = width - 2 * margin
    content_height = height - 2 * margin

    # Starting position for content
    content_x = x + margin
    content_y = y + margin

    # Get label information
    title = label_info.get("Title", "")
    author = label_info.get("Author's Name", "")
    pub_year = label_info.get("Publication Year", "")
    series_title = label_info.get("Series Title", "")
    series_volume = label_info.get("Series Volume", "")
    call_number = label_info.get("Call Number", "")
    barcode = label_info.get("Holdings Barcode", "")
    spine_label_id = label_info.get("spine_label_id", "A")
    clipart = label_info.get("clipart", "None")

    # Font sizes
    title_font_size = 8
    author_font_size = 7
    details_font_size = 6
    barcode_font_size = 8

    # Current y position for text
    current_y = content_y + content_height - 0.1 * inch

    # Draw clipart if specified
    if clipart != "None":
        clipart_path = get_clipart_path(clipart)
        if clipart_path:
            try:
                # Draw small clipart in top-right corner
                clipart_size = 0.25 * inch
                clipart_x = content_x + content_width - clipart_size
                clipart_y = current_y - clipart_size
                c.drawImage(clipart_path, clipart_x, clipart_y, clipart_size, clipart_size)
                # Adjust text area to avoid overlap
                content_width -= clipart_size + 0.05 * inch
            except:
                pass

    # Draw title (truncate if too long)
    c.setFont("Helvetica-Bold", title_font_size)
    title_lines = wrap_text(title, content_width, c, title_font_size)
    for line in title_lines:
        if current_y < content_y + 0.2 * inch:
            break
        c.drawString(content_x, current_y, line)
        current_y -= title_font_size + 1

    # Draw author
    if author:
        c.setFont("Helvetica", author_font_size)
        author_lines = wrap_text(author, content_width, c, author_font_size)
        for line in author_lines:
            if current_y < content_y + 0.2 * inch:
                break
            c.drawString(content_x, current_y, line)
            current_y -= author_font_size + 1

    # Draw series information
    if series_title and series_volume:
        c.setFont("Helvetica-Oblique", details_font_size)
        series_text = f"{series_title} Vol. {series_volume}"
        if current_y >= content_y + 0.2 * inch:
            c.drawString(content_x, current_y, series_text)
            current_y -= details_font_size + 1

    # Draw publication year
    if pub_year:
        c.setFont("Helvetica", details_font_size)
        if current_y >= content_y + 0.2 * inch:
            c.drawString(content_x, current_y, pub_year)
            current_y -= details_font_size + 1

    # Draw call number and barcode
    if call_number or barcode:
        c.setFont("Helvetica-Bold", barcode_font_size)

        # Call number
        if call_number and current_y >= content_y + 0.3 * inch:
            c.drawString(content_x, content_y + 0.2 * inch, call_number)

        # Barcode (simulated with text)
        if barcode and current_y >= content_y + 0.1 * inch:
            c.setFont("Helvetica", details_font_size)
            c.drawString(content_x, content_y + 0.05 * inch, f"Barcode: {barcode}")

    # Draw spine label identifier
    c.setFont("Helvetica-Bold", 10)
    c.drawString(content_x + content_width - 0.2 * inch, content_y + 0.1 * inch, spine_label_id)


def wrap_text(text: str, max_width: float, c, font_size: int) -> list[str]:
    """
    Wrap text to fit within specified width.

    Args:
        text: Text to wrap
        max_width: Maximum width in points
        c: Canvas object for measuring
        font_size: Font size

    Returns:
        List of wrapped lines
    """
    if not text:
        return []

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width = c.stringWidth(test_line, "Helvetica", font_size)

        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    # Truncate if too many lines
    if len(lines) > 2:
        lines = lines[:2]
        # Add ellipsis to last line if truncated
        last_line = lines[-1]
        while c.stringWidth(last_line + "...", "Helvetica", font_size) > max_width and len(last_line) > 3:
            last_line = last_line[:-1]
        lines[-1] = last_line + "..."

    return lines


def get_clipart_path(clipart_name: str) -> str | None:
    """
    Get path to clipart image.

    Args:
        clipart_name: Name of the clipart

    Returns:
        Path to clipart image or None if not found
    """
    # For Streamlit Cloud, we'll use placeholder approach
    # In a real implementation, you would have these images in your project
    clipart_urls = {
        "Duck": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
        "Mouse": "https://cdn-icons-png.flaticon.com/512/616/616430.png",
        "Cat": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
        "Dog": "https://cdn-icons-png.flaticon.com/512/616/616430.png",
        "Padlock": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
        "Chili Pepper": "https://cdn-icons-png.flaticon.com/512/616/616430.png",
        "Eyeglasses": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
        "Handcuffs": "https://cdn-icons-png.flaticon.com/512/616/616430.png",
    }

    return clipart_urls.get(clipart_name)


def download_image_to_buffer(url: str) -> io.BytesIO | None:
    """
    Download image from URL to buffer.

    Args:
        url: Image URL

    Returns:
        BytesIO buffer with image data or None if download fails
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except:
        return None


def create_sample_labels() -> bytes:
    """
    Create sample labels for testing.

    Returns:
        PDF data as bytes
    """
    sample_data = [
        {
            "Title": "Naruto Vol. 1",
            "Author's Name": "Kishimoto, Masashi",
            "Publication Year": "2003",
            "Series Title": "Naruto",
            "Series Volume": "1",
            "Call Number": "Manga T000001",
            "Holdings Barcode": "T000001",
            "spine_label_id": "A",
            "clipart": "Duck"
        },
        {
            "Title": "One Piece Vol. 1",
            "Author's Name": "Oda, Eiichiro",
            "Publication Year": "2003",
            "Series Title": "One Piece",
            "Series Volume": "1",
            "Call Number": "Manga T000002",
            "Holdings Barcode": "T000002",
            "spine_label_id": "B",
            "clipart": "Cat"
        }
    ]

    return generate_pdf_sheet(sample_data)


def main():
    """Test function for label generation"""
    print("Label Generator Test")
    print("Generating sample labels...")

    try:
        pdf_data = create_sample_labels()

        # Save sample PDF
        with open("sample_labels.pdf", "wb") as f:
            f.write(pdf_data)

        print("Sample labels generated successfully!")
        print("Saved as 'sample_labels.pdf'")

    except Exception as e:
        print(f"Error generating labels: {e}")


if __name__ == "__main__":
    main()