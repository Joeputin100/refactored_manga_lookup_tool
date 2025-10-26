import sys
import pandas as pd
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, VertexAIAPI, ProjectState, BookInfo
from label_generator import generate_pdf_labels

def run_e2e_test():
    """Runs an end-to-end test of the manga lookup tool."""

    print("Starting test...")
    test_data = {
        "Attack on Titan": list(range(1, 6)),
        "One Piece": list(range(1, 6)),
        "Naruto": list(range(1, 6)),
        "Vinland Saga": list(range(1, 6)),
        "Chainsaw Man": list(range(1, 6)),
    }

    all_books = []
    project_state = ProjectState()
    vertex_api = VertexAIAPI()

    for series_name, volumes in test_data.items():
        for volume_num in volumes:
            print(f"Processing {series_name} Vol. {volume_num}")
            book_data = vertex_api.get_book_info(series_name, volume_num, project_state)
            if book_data:
                book = BookInfo(
                    series_name=book_data.get("series_name", series_name),
                    volume_number=volume_num,
                    book_title=book_data.get("book_title", f"{series_name} Vol. {volume_num}"),
                    authors=book_data.get("authors", []),
                    msrp_cost=book_data.get("msrp_cost"),
                    isbn_13=book_data.get("isbn_13"),
                    publisher_name=book_data.get("publisher_name"),
                    copyright_year=book_data.get("copyright_year"),
                    description=book_data.get("description"),
                    physical_description=book_data.get("physical_description"),
                    genres=book_data.get("genres", []),
                    warnings=[],
                    barcode=f"TEST{series_name.replace(' ', '')[:5].upper()}{volume_num:03d}",
                    cover_image_url=book_data.get("cover_image_url")
                )
                all_books.append(book)

    print("Finished processing books.")
    if not all_books:
        print("No books were processed.")
        return

    label_data = []
    for book in all_books:
        label_data.append({
            'Holdings Barcode': book.barcode,
            'Title': book.book_title,
            'Author': ', '.join(book.authors) if book.authors else "Unknown Author",
            'Copyright Year': str(book.copyright_year) if book.copyright_year else "",
            'Series Info': book.series_name,
            'Series Number': str(book.volume_number),
            'Call Number': "",
            'spine_label_id': "M",
            'MSRP': book.msrp_cost
        })

    if label_data:
        print("Generating PDF...")
        df = pd.DataFrame(label_data)
        pdf_data = generate_pdf_labels(df, library_name="Manga Collection")
        with open("test_labels.pdf", "wb") as f:
            f.write(pdf_data)
        print("PDF generation complete.")
        print("Successfully generated test_labels.pdf")

if __name__ == "__main__":
    run_e2e_test()
