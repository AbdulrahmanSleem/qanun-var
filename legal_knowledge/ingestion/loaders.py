"""
Document Loaders for Egyptian Legal Text.
Supports PDF, DOCX, and TXT formats with robust encoding detection and error handling.
"""

from pathlib import Path
from typing import Optional
import logging
import docx
import pypdf

logger = logging.getLogger(__name__)


class DocumentLoaderError(Exception):
    """Exception raised when document loading fails."""
    pass


class DocumentLoader:
    """Multi-format document loader for Egyptian legal files."""

    @staticmethod
    def load_txt(file_path: Path) -> str:
        """
        Load TXT document, attempting UTF-8 first, with Arabic fallback encodings
        (cp1256 / windows-1256, iso-8859-6).
        """
        encodings = ["utf-8", "utf-8-sig", "cp1256", "iso-8859-6", "latin1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                logger.debug(f"Loaded {file_path.name} with encoding: {enc}")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise DocumentLoaderError(f"Failed to read TXT file {file_path}: {e}") from e

        raise DocumentLoaderError(f"Unable to decode TXT file {file_path} with supported encodings.")

    @staticmethod
    def load_docx(file_path: Path) -> str:
        """Load DOCX document paragraph by paragraph, preserving table texts if present."""
        try:
            doc = docx.Document(file_path)
            paragraphs = []
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    paragraphs.append(text)

            # Also extract tables if any
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        paragraphs.append(" | ".join(row_texts))

            return "\n\n".join(paragraphs)
        except Exception as e:
            raise DocumentLoaderError(f"Failed to read DOCX file {file_path}: {e}") from e

    @staticmethod
    def load_pdf(file_path: Path) -> str:
        """
        Load PDF document using pypdf.
        Extracts textual content page by page and normalizes layout lines.
        """
        try:
            reader = pypdf.PdfReader(str(file_path))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(text.strip())

            if not pages_text:
                logger.warning(f"PDF {file_path.name} yielded empty text extraction.")
            return "\n\n".join(pages_text)
        except Exception as e:
            raise DocumentLoaderError(f"Failed to read PDF file {file_path}: {e}") from e

    @classmethod
    def load(cls, file_path: str | Path) -> str:
        """
        Main entry point: dynamically routes to appropriate loader based on file suffix.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentLoaderError(f"File does not exist: {path}")

        suffix = path.suffix.lower()
        if suffix in [".txt", ".text"]:
            return cls.load_txt(path)
        elif suffix in [".docx", ".doc"]:
            return cls.load_docx(path)
        elif suffix == ".pdf":
            return cls.load_pdf(path)
        else:
            # Fallback to plain text read
            logger.info(f"Unrecognized extension {suffix}, attempting TXT loader for {path.name}")
            return cls.load_txt(path)
