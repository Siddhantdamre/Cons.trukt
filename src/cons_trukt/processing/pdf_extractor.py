"""PDF text extraction with OCR fallback."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from cons_trukt.config import ProcessingSettings
from cons_trukt.exceptions import ExtractionError
from cons_trukt.utils.logging import get_logger

logger = get_logger(__name__)


class PDFTextExtractor:
    """Extract text from a blueprint PDF, falling back to OCR when needed."""

    def __init__(self, settings: ProcessingSettings) -> None:
        self.settings = settings

    def extract(self, pdf_path: str | Path) -> str:
        path = Path(pdf_path)
        if not path.exists():
            raise ExtractionError(f"Blueprint file not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ExtractionError(f"Expected a PDF blueprint, got: {path}")

        logger.info("extracting_blueprint_text", path=str(path))
        content = self._extract_digital_text(path)
        if content.strip():
            return content

        logger.info("digital_text_empty_using_ocr", path=str(path))
        return self._extract_ocr_text(path)

    def _extract_digital_text(self, path: Path) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise ExtractionError("pdfplumber is required for digital PDF extraction.") from exc

        try:
            chunks: list[str] = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        chunks.append(page_text)
            return "\n".join(chunks)
        except Exception as exc:
            raise ExtractionError(f"Could not extract digital text from {path}: {exc}") from exc

    def _extract_ocr_text(self, path: Path) -> str:
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError as exc:
            raise ExtractionError(
                "pytesseract and pdf2image are required for OCR fallback."
            ) from exc

        if self.settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = str(self.settings.tesseract_cmd)

        try:
            if self.settings.poppler_path:
                images = convert_from_path(
                    path,
                    poppler_path=str(self.settings.poppler_path),
                )
            else:
                images = convert_from_path(path)
            workers = max(1, self.settings.ocr_workers)
            with ThreadPoolExecutor(max_workers=workers) as executor:
                results = list(
                    executor.map(
                        lambda image: self._ocr_page(pytesseract, image),
                        images,
                    )
                )
            content = "\n".join(results)
        except Exception as exc:
            raise ExtractionError(f"OCR extraction failed for {path}: {exc}") from exc

        if not content.strip():
            raise ExtractionError(f"No text could be extracted from {path}")
        return content

    @staticmethod
    def _ocr_page(pytesseract_module: Any, image: Any) -> str:
        return str(pytesseract_module.image_to_string(image))
