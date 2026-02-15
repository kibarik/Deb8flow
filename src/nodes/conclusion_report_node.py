"""
Conclusion Report Node for LangGraph.

This node generates conclusion reports after debate completion by extracting
structured data from debate state and using LLM to create comprehensive reports.

Example:
    >>> from src.nodes.conclusion_report_node import ConclusionReportNode
    >>> node = ConclusionReportNode()
    >>> result = node(state)
"""

import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

from nodes.base_component import BaseComponent
from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
    DebateType,
)
from src.extractors.debate_state_extractor import DebateStateExtractor
from src.utils.conclusion_writer import ConclusionWriter


__all__ = ["ConclusionReportNode"]


class ConclusionReportNode(BaseComponent):
    """LangGraph node for generating conclusion reports.

    Extracts conclusion data from debate state and generates
    comprehensive markdown report using LLM with structured prompt.

    Attributes:
        logger: Logger instance for tracking node execution
        extractor: DebateStateExtractor for data extraction
        writer: ConclusionWriter for markdown output
    """

    def __init__(self):
        """Initialize conclusion report node."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.extractor = DebateStateExtractor()
        self.writer = ConclusionWriter()

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conclusion report from debate state.

        Args:
            state: DebateState dictionary with messages and verdict

        Returns:
            Updated state with conclusion_report_path added

        Raises:
            ValueError: If required state fields are missing
        """
        self.logger.info("Generating conclusion report from debate state")

        # Extract conclusion data using extractor
        try:
            conclusion_data = self.extractor.extract(state)
        except ValueError as e:
            self.logger.error(f"Failed to extract conclusion data: {e}")
            raise

        # Detect debate type and route to appropriate prompt
        debate_type = self._detect_debate_type(state)
        self.logger.info(f"Detected debate type: {debate_type.value}")

        # Get appropriate prompt
        prompt = self._get_prompt_for_debate_type(debate_type)

        # Generate conclusion using LLM
        llm_response = self._generate_conclusion_with_llm(conclusion_data, prompt)

        # Parse and validate LLM response
        parsed_conclusion = self._parse_llm_response(llm_response)

        # Write conclusion report using writer
        output_path = self._write_conclusion_report(
            conclusion_data,
            parsed_conclusion,
            state
        )

        # Update state with output path
        return {"conclusion_report_path": output_path}

    def _detect_debate_type(self, state: Dict[str, Any]) -> DebateType:
        """Detect debate type from state.

        Args:
            state: DebateState dictionary

        Returns:
            Detected debate type (committee, standard, or document)
        """
        # Check for document input
        if state.get("document_input"):
            return DebateType.DOCUMENT

        # Check for custom prompts (committee debate)
        if state.get("pro_custom_prompt") or state.get("con_custom_prompt"):
            return DebateType.COMMITTEE

        # Default to standard debate
        return DebateType.STANDARD

    def _get_prompt_for_debate_type(self, debate_type: DebateType) -> str:
        """Get appropriate conclusion prompt for debate type.

        Args:
            debate_type: Type of debate

        Returns:
            Prompt text for LLM
        """
        from src.prompts.conclusion_report_prompt import get_conclusion_report_prompt

        return get_conclusion_report_prompt(debate_type)

    def _generate_conclusion_with_llm(
        self,
        conclusion_data: ConclusionData,
        prompt: str
    ) -> str:
        """Generate conclusion text using LLM.

        Args:
            conclusion_data: Extracted conclusion data
            prompt: Formatted prompt for LLM

        Returns:
            Generated conclusion text as JSON string
        """
        self.logger.info("Calling LLM to generate conclusion report")

        # Use structured output chain for JSON response
        chain = self.get_structured_output_chain(
            output_schema={
                "debate_question": "string",
                "verdict": {
                    "winner": "string",
                    "winner_position": "string",
                    "justification": "string",
                },
                "qa_summary": [{
                    "question": "string",
                    "answer": "string",
                    "stage": "string",
                    "speaker": "string",
                    "validated": "boolean",
                    "priority": "integer",
                }],
                "tpm_analysis": {
                    "position_summary": "string",
                    "weaknesses": [{
                        "category": "string",
                        "description": "string",
                        "severity": "string",
                        "source": "string",
                        "context": "string or null",
                    }],
                    "recommended_improvements": ["string"],
                    "victory_assessment": "string",
                },
                "recommendations": [{
                    "agent_role": "string",
                    "text": "string",
                    "priority": "string or null",
                    "category": "string or null",
                    "actionable": "boolean",
                }],
                "metadata": {
                    "debate_type": "string",
                    "run_id": "string",
                    "generated_at": "string",
                    "source_file": "string or null",
                    "total_recommendations": "integer",
                    "tpm_victory": "boolean",
                    "completion_status": "string",
                    "error_message": "string or null",
                },
            }
        )

        # Format prompt with conclusion data
        formatted_prompt = prompt.format(**conclusion_data)

        # Invoke LLM chain
        try:
            response = chain.invoke(
                input=formatted_prompt,
                config={"run_name": "conclusion_report_generation"}
            )
            return response.get("conclusion", "")
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse and validate LLM response.

        Args:
            llm_response: Raw JSON response from LLM

        Returns:
            Parsed conclusion dictionary

        Raises:
            ValueError: If response is invalid or missing required fields
        """
        self.logger.info("Parsing LLM response")

        try:
            import json
            parsed = json.loads(llm_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {e}")

        # Validate required fields
        required_fields = [
            "debate_question",
            "verdict",
            "qa_summary",
            "tpm_analysis",
            "recommendations",
            "metadata",
        ]

        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field in LLM response: {field}")

        self.logger.info("Successfully parsed LLM response")
        return parsed

    def _write_conclusion_report(
        self,
        conclusion_data: ConclusionData,
        parsed_conclusion: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """Write conclusion report to markdown file.

        Args:
            conclusion_data: Original extracted conclusion data
            parsed_conclusion: Parsed conclusion from LLM
            state: DebateState dictionary

        Returns:
            Path to generated conclusion report file
        """
        self.logger.info("Writing conclusion report to markdown file")

        # Determine output directory from state or default
        output_dir = state.get("output_dir", "conclusion_reports")
        output_dir_path = Path(output_dir)

        # Create directory if it doesn't exist
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate filename from debate question or timestamp
        debate_question = conclusion_data.get("debate_question", "debate")
        safe_filename = re.sub(r"[^\w\s-]", "", debate_question)[:50]
        timestamp = parsed_conclusion.get("metadata", {}).get("generated_at", "")
        safe_timestamp = re.sub(r"[^\w\s-:]", "", timestamp)[:20]

        filename = f"{safe_filename}_{safe_timestamp}.md"
        output_path = output_dir_path / filename

        # Write conclusion using writer
        self.writer.write(
            output_path=str(output_path),
            conclusion_data=conclusion_data,
            parsed_conclusion=parsed_conclusion,
        )

        self.logger.info(f"Conclusion report written to: {output_path}")
        return str(output_path)
