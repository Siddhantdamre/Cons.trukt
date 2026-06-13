from __future__ import annotations

from cons_trukt.config import ProcessingSettings
from cons_trukt.processing.pdf_extractor import PDFTextExtractor


class FallbackExtractor(PDFTextExtractor):
    def __init__(self) -> None:
        super().__init__(ProcessingSettings())
        self.used_ocr = False

    def _extract_digital_text(self, path):
        return ""

    def _extract_ocr_text(self, path):
        self.used_ocr = True
        return "OCR text"


def test_pdf_extractor_uses_ocr_when_digital_text_is_empty(tmp_path):
    pdf = tmp_path / "plan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    extractor = FallbackExtractor()

    result = extractor.extract(pdf)

    assert result == "OCR text"
    assert extractor.used_ocr is True
