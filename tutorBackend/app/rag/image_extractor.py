import os
from pathlib import Path
import fitz


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> list[dict]:
    """Extract embedded images from a PDF and save them to output_dir."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pdf_base = Path(pdf_path).stem
    extracted = []

    for page_number, page in enumerate(doc, start=1):
        image_list = page.get_images(full=True)
        for image_index, image_info in enumerate(image_list, start=1):
            xref = image_info[0]
            image_data = doc.extract_image(xref)
            if not image_data:
                continue

            image_bytes = image_data["image"]
            image_ext = image_data["ext"]
            image_filename = f"{pdf_base}_p{page_number}_img{image_index}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)

            with open(image_path, "wb") as out_file:
                out_file.write(image_bytes)

            extracted.append({
                "page": page_number,
                "image_path": image_path,
            })

    return extracted
