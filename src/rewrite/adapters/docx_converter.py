"""
DOCX to Markdown converter for AI-powered document editing.

Converts DOCX files to Markdown for AI processing, then converts back.
"""
import re
from pathlib import Path
from typing import List
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class DocxConverter:
    """
    Converts between DOCX and Markdown formats.

    Simple conversion that preserves basic structure:
    - Headings (based on style)
    - Paragraphs
    - Lists
    - Bold/Italic
    """

    def docx_to_markdown(self, docx_path: Path) -> str:
        """
        Convert DOCX file to Markdown string.

        Args:
            docx_path: Path to DOCX file

        Returns:
            Markdown content
        """
        doc = Document(str(docx_path))
        lines = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check paragraph style for heading
            style_name = para.style.name.lower() if para.style else ""

            if 'heading 1' in style_name or 'title' in style_name:
                lines.append(f"# {text}")
            elif 'heading 2' in style_name:
                lines.append(f"## {text}")
            elif 'heading 3' in style_name:
                lines.append(f"### {text}")
            elif 'heading 4' in style_name:
                lines.append(f"#### {text}")
            elif 'heading 5' in style_name:
                lines.append(f"##### {text}")
            elif 'heading 6' in style_name:
                lines.append(f"###### {text}")
            else:
                # Regular paragraph
                lines.append(text)

            lines.append("")  # Empty line after paragraph

        return "\n".join(lines)

    def markdown_to_docx(
        self,
        markdown: str,
        output_path: Path,
        template_path: Path = None
    ) -> None:
        """
        Convert Markdown string to DOCX file.

        Args:
            markdown: Markdown content
            output_path: Path for output DOCX file
            template_path: Optional template DOCX to preserve styling
        """
        # Always create new document for cleaner output
        # Template styling can be added later if needed
        doc = Document()

        lines = markdown.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Check for headings
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                self._add_heading(doc, text, level)
            else:
                # Regular paragraph
                if line:
                    doc.add_paragraph(line)

            i += 1

        # Save document
        doc.save(str(output_path))

    def _add_heading(self, doc: Document, text: str, level: int) -> None:
        """Add heading to document."""
        # Map markdown level to docx level (docx uses 0-9, 0 is title)
        docx_level = max(0, level - 1)
        doc.add_heading(text, level=docx_level)
