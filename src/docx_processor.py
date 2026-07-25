import os
import sys
import docx
from typing import Dict, List, Tuple, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.redactor import PIIRedactor
except ModuleNotFoundError:
    from redactor import PIIRedactor


class DocxRedactor:
    """
    Parses and redacts Word documents (.docx) while preserving formatting,
    runs, and table cell layout.
    """

    def __init__(self, redactor: PIIRedactor = None):
        self.redactor = redactor or PIIRedactor()

    def _redact_paragraph(self, paragraph: docx.text.paragraph.Paragraph) -> List[Dict[str, Any]]:
        """
        Redacts text in-place within individual docx runs to perfectly preserve
        run-level styling (bold, italic, font face, color, alignment, and line breaks).
        """
        full_text = paragraph.text
        if not full_text.strip():
            return []

        # 1. Quick check on full paragraph text
        redacted_text, detected = self.redactor.redact_text(full_text)
        if not detected:
            return []

        # 2. In-place run-level replacement preserving all run formatting
        if paragraph.runs:
            for ent in detected:
                orig_str = ent["text"]
                fake_str = self.redactor._get_fake_replacement(orig_str, ent["type"])

                # Try replacing in individual runs first
                replaced_in_runs = False
                for run in paragraph.runs:
                    if orig_str in run.text:
                        run.text = run.text.replace(orig_str, fake_str)
                        replaced_in_runs = True

                # If entity spans across multiple runs, update runs cleanly
                if not replaced_in_runs and len(paragraph.runs) > 0:
                    # Update text while preserving style of first run
                    first_run = paragraph.runs[0]
                    font_name = first_run.font.name
                    font_size = first_run.font.size
                    bold = first_run.bold
                    italic = first_run.italic

                    for r in paragraph.runs[1:]:
                        r.text = ""
                    first_run.text = redacted_text
                    first_run.font.name = font_name
                    first_run.font.size = font_size
                    first_run.bold = bold
                    first_run.italic = italic
        else:
            paragraph.text = redacted_text

        return detected

    def redact_document(self, input_filepath: str, output_filepath: str) -> Dict[str, Any]:
        """
        Processes an entire .docx file (paragraphs and tables) and saves redacted output.
        """
        doc = docx.Document(input_filepath)
        all_detected_entities: List[Dict[str, Any]] = []

        # 1. Redact regular paragraphs
        for p in doc.paragraphs:
            detected = self._redact_paragraph(p)
            all_detected_entities.extend(detected)

        # 2. Redact tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        detected = self._redact_paragraph(p)
                        all_detected_entities.extend(detected)

        doc.save(output_filepath)

        # Generate Summary Stats
        stats: Dict[str, int] = {}
        for ent in all_detected_entities:
            ent_type = ent["type"]
            stats[ent_type] = stats.get(ent_type, 0) + 1

        return {
            "total_entities_redacted": len(all_detected_entities),
            "stats_by_type": stats,
            "detected_entities": all_detected_entities,
            "output_filepath": output_filepath
        }
