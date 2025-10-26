#!/usr/bin/env python3
"""
Apply volume display updates to the main application
"""

import re

def update_display_results_function():
    """Update the display_results function with enhanced volume display logic"""

    # Read the current app file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Add import for enhanced volume display
    import_pattern = r'(from mangadex_cover_fetcher import MangaDexCoverFetcher)'
    import_replacement = r'\1\nfrom enhanced_volume_display import format_volume_range, display_enhanced_volume_info, create_volume_range_summary'
    content = re.sub(import_pattern, import_replacement, content)

    # Find the display_results function and update it
    results_function_start = content.find('def display_results():')
    if results_function_start == -1:
        print("❌ Could not find display_results function")
        return False

    # Find the end of the function (next function definition)
    next_function_start = content.find('\ndef ', results_function_start + 1)
    if next_function_start == -1:
        next_function_start = len(content)

    # Extract the current function
    current_function = content[results_function_start:next_function_start]

    # Create enhanced version
    enhanced_function = '''def display_results():
    """Step 7: Results display"""
    st.header("Processing Complete!")

    # Results table with series headers and detailed information
    if not st.session_state.all_books:
        st.info("No books were processed")
        return

    # Enhanced: Display volume range summary
    st.subheader("📊 Processing Summary")
    summary = create_volume_range_summary(st.session_state.series_entries)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Series", summary['total_series'])
    with col2:
        st.metric("Total Volumes", summary['total_volumes'])
    with col3:
        st.metric("Barcode Range", f"{st.session_state.series_entries[0]['barcodes'][0]} - {st.session_state.series_entries[-1]['barcodes'][-1]}")

    # Group books by series
    series_groups = defaultdict(list)
    for book in st.session_state.all_books:
        series_groups[book.series_name].append(book)

    # Display each series with header and volume details
    for series_name in sorted(series_groups.keys()):
        books = sorted(series_groups[series_name], key=lambda x: x.volume_number)

        # Enhanced: Display enhanced volume info with cache data
        processed_volumes = [book.volume_number for book in books]
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

    # Export options
    st.divider()
    st.subheader("Export Options")

    col1, col2 = st.columns(2)

    with col1:
        try:
            marc_data = export_books_to_marc(st.session_state.all_books)

            # Generate filename with date/time and sanitized series names
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

            # Prepare data for label generation in the format expected by generate_pdf_labels
            label_data = []
            for book in st.session_state.all_books:
                label_data.append({
                    'Holdings Barcode': book.barcode,
                    'Title': book.book_title or f"{book.series_name} Vol. {book.volume_number}",
                    'Author': ', '.join(book.authors) if book.authors else "Unknown Author",
                    'Copyright Year': str(book.copyright_year) if book.copyright_year else "",
                    'Series Info': book.series_name,
                    'Series Number': str(book.volume_number),
                    'Call Number': "",  # Empty for manga
                    'spine_label_id': "M"  # M for manga
                })

            if label_data:
                # Convert to DataFrame as expected by generate_pdf_labels
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
'''

    # Replace the function
    content = content[:results_function_start] + enhanced_function + content[next_function_start:]

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Successfully updated display_results function with enhanced volume display")
    return True

if __name__ == "__main__":
    update_display_results_function()