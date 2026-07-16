from pypdf import PdfReader


def load_pdf_text(file_path: str) -> str:
    """Read all text from a PDF and return it as one concatenated string."""
    reader = PdfReader(file_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n\n".join(text_parts)
