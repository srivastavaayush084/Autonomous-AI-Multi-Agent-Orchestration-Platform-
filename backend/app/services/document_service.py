import os
import logging
from typing import Dict, Any, Optional
from PIL import Image
import pypdf
import docx

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Multimodal Document & Image Parser Service.
    Extracts text, metadata, and structure from PDF, DOCX, TXT, and Image files.
    """

    @staticmethod
    def extract_text_from_pdf(file_path: str, max_pages: int = 50) -> Dict[str, Any]:
        """Extracts text and page metadata from a PDF file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)
        extracted_text = []

        for idx in range(min(total_pages, max_pages)):
            page = reader.pages[idx]
            text = page.extract_text() or ""
            extracted_text.append(f"--- Page {idx + 1} ---\n{text.strip()}")

        full_content = "\n\n".join(extracted_text)
        return {
            "file_type": "pdf",
            "total_pages": total_pages,
            "processed_pages": min(total_pages, max_pages),
            "text": full_content,
            "char_count": len(full_content)
        }

    @staticmethod
    def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
        """Extracts text and headings from a DOCX file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_content = "\n\n".join(paragraphs)
        return {
            "file_type": "docx",
            "paragraph_count": len(paragraphs),
            "text": full_content,
            "char_count": len(full_content)
        }

    @staticmethod
    def extract_text_from_txt(file_path: str) -> Dict[str, Any]:
        """Extracts plain text from TXT/MD file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return {
            "file_type": "text",
            "text": content,
            "char_count": len(content)
        }

    @staticmethod
    def inspect_image(file_path: str) -> Dict[str, Any]:
        """Inspects image dimensions, color mode, format, and metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            file_size_bytes = os.path.getsize(file_path)

        summary_text = (
            f"Image Analysis: {os.path.basename(file_path)}\n"
            f"- Dimensions: {width} x {height} px\n"
            f"- Format: {format_name}\n"
            f"- Color Mode: {mode}\n"
            f"- File Size: {round(file_size_bytes / 1024, 1)} KB"
        )

        return {
            "file_type": "image",
            "dimensions": {"width": width, "height": height},
            "format": format_name,
            "mode": mode,
            "file_size_bytes": file_size_bytes,
            "text": summary_text
        }

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Routes file to appropriate extractor based on extension."""
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        elif ext in [".txt", ".md", ".csv", ".json", ".log"]:
            return self.extract_text_from_txt(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]:
            return self.inspect_image(file_path)
        else:
            # Fallback to plain text read
            return self.extract_text_from_txt(file_path)


document_service = DocumentService()
