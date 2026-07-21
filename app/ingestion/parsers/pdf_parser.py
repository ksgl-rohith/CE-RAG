from pypdf import PdfReader
from typing import List, Dict, Any

class PDFParser:
    @staticmethod
    def extract_pages(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from a PDF file page-by-page.
        Returns a list of dicts, each with 'page_number' and 'text'.
        """
        pages = []
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned_text = text.replace("\x00", "").strip()
                pages.append({
                    "page_number": i + 1,
                    "text": cleaned_text
                })
        except Exception as e:
            print(f"Error parsing PDF file {file_path}: {e}")
            raise e
        return pages
