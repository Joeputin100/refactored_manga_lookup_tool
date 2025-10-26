#!/usr/bin/env python3
"""
Manga Lookup Tool - Enhanced Version with Volume Range Display

This version includes enhanced volume range display logic that shows:
- Formatted volume ranges (e.g., "1-10" instead of "1-10")
- Cache coverage information
- Series metadata from BigQuery cache
- Volume range summaries
"""

import re
import sys
import time
import warnings
from collections import defaultdict

# Suppress warnings before importing other modules
from warning_suppressor import configure_warnings
configure_warnings()

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import requests

# Import existing core logic
from manga_lookup import (
    DeepSeekAPI,
    GoogleBooksAPI,
    VertexAIAPI,
    ProjectState,
    generate_sequential_general_barcodes,
    parse_volume_range,
    validate_barcode,
    validate_general_barcode,
    validate_series_name,
    sanitize_series_name,
)
from marc_exporter import export_books_to_marc
from mal_cover_fetcher import MALCoverFetcher
from mangadex_cover_fetcher import MangaDexCoverFetcher
from enhanced_volume_display import (
    format_volume_range,
    display_enhanced_volume_info,
    create_volume_range_summary
)


# Copy all existing functions from app_new_workflow.py
# (This would normally be done by importing, but for simplicity we'll copy key functions)

# ... [All the existing functions from app_new_workflow.py would be here] ...


def display_results_enhanced():
    """
    Enhanced results display with volume range information
    """
    st.header("Processing Complete!")

    # Results table with series headers and detailed information
    if not st.session_state.all_books:
        st.info("No books were processed")
        return

    # Create volume range summary
    summary = create_volume_range_summary(st.session_state.series_entries)

    # Display summary
    st.subheader("📊 Processing Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Series", summary['total_series'])
    with col2:
        st.metric("Total Volumes", summary['total_volumes'])
    with col3:
        st.metric("Barcode Range",
                 f"{st.session_state.series_entries[0]['barcodes'][0]} - {st.session_state.series_entries[-1]['barcodes'][-1]}")

    # Display volume ranges summary
    st.subheader("📚 Volume Ranges by Series")
    for range_info in summary['volume_ranges']:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
        with col1:
            st.write(f"**{range_info['series_name']}**")
        with col2:
            st.write(f"Volumes: {range_info['volume_range']}")
        with col3:
            st.write(f"Count: {range_info['volume_count']}")
        with col4:
            st.write(f"Barcodes: {range_info['barcode_range']}")

    st.divider()

    # Group books by series
    series_groups = defaultdict(list)
    for book in st.session_state.all_books:
        series_groups[book.series_name].append(book)

    # Display each series with enhanced volume information
    for series_name in sorted(series_groups.keys()):
        books = sorted(series_groups[series_name], key=lambda x: x.volume_number)

        # Get processed volume numbers
        processed_volumes = [book.volume_number for book in books]

        # Display enhanced volume info
        cache_info = display_enhanced_volume_info(series_name, processed_volumes)

        # Volume details table
        st.subheader("Volume Details")

        # Table header
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 2])
        col1.write("**Cover**")
        col2.write("**Title**")
        col3.write("**Vol**")
        col4.write("**Barcode**")
        col5.write("**MSRP**")
        col6.write("**Physical Desc**")
        col7.write("**Summary**")

        # Volume rows
        for book in books:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 2])

            # Cover image
            with col1:
                if hasattr(book, 'cover_image_url') and book.cover_image_url:
                    st.image(book.cover_image_url, width=50)
                else:
                    st.write("📚")

            # Title
            with col2:
                st.write(book.book_title or f"{series_name} Vol. {book.volume_number}")

            # Volume number
            with col3:
                st.write(str(book.volume_number))

            # Barcode
            with col4:
                st.write(book.barcode)

            # MSRP
            with col5:
                st.write(f"${float(book.msrp_cost):.2f}" if book.msrp_cost else "N/A")

            # Physical description
            with col6:
                st.write(book.physical_description or "N/A")

            # Summary description (truncated)
            with col7:
                desc = book.description or "No description"
                if len(desc) > 100:
                    st.write(f"{desc[:100]}...")
                    st.caption("Hover for full description")
                else:
                    st.write(desc)

        st.divider()

    # Export options (same as original)
    st.divider()
    st.subheader("Export Options")

    col1, col2 = st.columns(2)

    with col1:
        try:
            marc_data = export_books_to_marc(st.session_state.all_books)
            filename = generate_marc_filename(st.session_state.all_books)
            st.download_button(
                "Download MARC File",
                data=marc_data,
                file_name=filename,
                mime="application/marc",
            )
        except Exception as e:
            st.error("Sorry! An error occurred while exporting the file.")
            print(f"Error exporting MARC: {e!s}")

    with col2:
        try:
            from label_generator import generate_pdf_labels
            import pandas as pd

            label_data = []
            for book in st.session_state.all_books:
                label_data.append({
                    'Holdings Barcode': book.barcode,
                    'Title': book.book_title or f"{book.series_name} Vol. {book.volume_number}",
                    'Author': ', '.join(book.authors) if book.authors else "Unknown Author",
                    'Copyright Year': str(book.copyright_year) if book.copyright_year else "",
                    'Series Info': book.series_name,
                    'Series Number': str(book.volume_number),
                    'Call Number': "",
                    'spine_label_id': "M"
                })

            if label_data:
                df = pd.DataFrame(label_data)
                pdf_data = generate_pdf_labels(df, library_name="Manga Collection")
                st.download_button(
                    "Print Labels",
                    data=pdf_data,
                    file_name="manga_labels.pdf",
                    mime="application/pdf",
                )
            else:
                st.button("Print Labels", disabled=True, help="No books to generate labels for")

        except Exception as e:
            st.error("Sorry! An error occurred while generating labels.")
            print(f"Error generating labels: {e!s}")


# Main function to run the enhanced app
def main():
    """Main function for the enhanced app"""
    # This would normally integrate with the existing app structure
    # For now, we'll just show that the enhanced display is available
    st.title("Manga Lookup Tool - Enhanced Volume Display")
    st.info("This is the enhanced version with volume range display logic. Use app_new_workflow.py for the main application.")


if __name__ == "__main__":
    main()