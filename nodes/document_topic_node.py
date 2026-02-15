"""
Document Topic Node - Generates debate topics from .docx documents.

This node replaces GenerateTopicNode to support document-based debates. It reads .docx files,
extracts text content, and generates debate topics from the document using LLM.
"""

from typing import Dict, Any
from docx import Document as DocxDocument
from nodes.base_component import BaseComponent
from prompts.topic_generator_prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from debate_state import DebateState


class DocumentTopicNode(BaseComponent):
    """
    Node that generates a debate topic from a .docx document.

    This node replaces GenerateTopicNode to support document-based debates.
    It handles both file paths (to .docx files) and pre-extracted text.
    """

    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        # Reuse existing topic generator prompts - they work for documents too
        self.chain = self.create_chain(SYSTEM_PROMPT, HUMAN_PROMPT)

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        """
        Generates a debate topic from document input or uses direct topic.

        Args:
            state: DebateState containing document_input or direct_topic field

        Returns:
            Dict with:
                - debate_topic: Generated topic from document or direct topic
                - positions: PRO/CON position labels
                - stage: Set to "opening"
                - speaker: Set to "pro"
        """
        super().__call__(state)

        # Check for direct topic (from --text or --request argument)
        direct_topic = state.get("direct_topic")
        document_context = state.get("document_context")

        if direct_topic and direct_topic.strip():
            if document_context:
                self.logger.info(f"📋 Debate topic: {direct_topic.strip()}")
                self.logger.info(f"📄 Document context provided: {len(document_context)} chars")
            else:
                self.logger.info(f"📋 Using direct topic: {direct_topic.strip()}")
            return {
                "debate_topic": direct_topic.strip(),
                "positions": {"pro": "In favor", "con": "Against"},
                "stage": "opening",
                "speaker": "pro"
            }

        doc_text = state.get("document_input", "")

        # Check if the input is a file path to .docx
        if doc_text and doc_text.strip().endswith(".docx"):
            # Read .docx file and extract text
            try:
                doc = DocxDocument(doc_text)
                doc_text = "\n".join(p.text for p in doc.paragraphs)
                self.logger.info(f"📄 Extracting text from .docx file")
            except Exception as e:
                self.logger.error(f"❌ Failed to read .docx file: {doc_text}")
                raise ValueError(f"Unable to read .docx file: {doc_text}")
        elif doc_text and doc_text.strip():
            # Input is pre-extracted text content - generate topic from it
            self.logger.info("📄 Generating topic from document text")
        else:
            # Empty or whitespace-only input
            self.logger.warning("⚠️ Empty document input provided")
            raise ValueError("Document input is required for topic generation")

        # Pass extracted/pre-provided text to LLM for topic generation
        topic_text = self.execute_chain({"document_text": doc_text})

        # Log the generated topic
        self.logger.info(f"📋 Generated debate topic: {topic_text.strip()}")

        return {
            "debate_topic": topic_text.strip(),
            "positions": {"pro": "In favor", "con": "Against"},
            "stage": "opening",
            "speaker": "pro"
        }

    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text content from a .docx file.

        Args:
            file_path: Path to the .docx file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file cannot be read or is empty
        """
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
