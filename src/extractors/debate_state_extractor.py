"""
Debate State Extractor for standard/document debates.

This module extracts conclusion data from DebateState for standard and document-based debates.
Extracts judge verdict, Q&A pairs, and identifies TPM role for generating the conclusion report.

Example:
    >>> from src.extractors.debate_state_extractor import DebateStateExtractor
    >>> extractor = DebateStateExtractor()
    >>> conclusion = extractor.extract(state)
"""

import logging
from typing import Optional, List, Dict, Any

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


__all__ = ["DebateStateExtractor"]


class DebateStateExtractor:
    """Extractor for debate state in standard/document debates.

    Extracts structured conclusion data from DebateState including verdict,
    Q&A pairs, TPM analysis, and recommendations.

    Attributes:
        logger: Logger instance for tracking extraction progress
    """

    def __init__(self):
        """Initialize the extractor with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract(self, state: Dict[str, Any]) -> ConclusionData:
        """Extract conclusion data from debate state.

        Args:
            state: DebateState dictionary with messages and verdict

        Returns:
            ConclusionData structured from the debate

        Raises:
            ValueError: If required fields are missing from state
        """
        # Extract debate question
        debate_question = self._extract_question(state)

        # Extract verdict
        verdict = self._extract_verdict(state)

        # Extract Q&A pairs from messages
        qa_summary = self._extract_qa_summary(state)

        # Extract TPM analysis if TPM is participating
        tpm_analysis = self._extract_tpm_analysis(state)

        # Extract recommendations from messages
        recommendations = self._extract_recommendations(state)

        # Build metadata
        metadata = self._build_metadata(state)

        return ConclusionData(
            debate_question=debate_question,
            verdict=verdict,
            qa_summary=qa_summary,
            tpm_analysis=tpm_analysis,
            recommendations=recommendations,
            metadata=metadata,
        )

    def _extract_question(self, state: Dict[str, Any]) -> str:
        """Extract debate question from state.

        Args:
            state: DebateState dictionary

        Returns:
            Debate question text

        Raises:
            ValueError: If debate_topic is missing
        """
        debate_question = state.get("debate_topic")

        if not debate_question:
            raise ValueError("Missing required field: debate_topic")

        return debate_question

    def _extract_verdict(self, state: Dict[str, Any]) -> VerdictSummary:
        """Extract verdict from state.

        Args:
            state: DebateState dictionary

        Returns:
            VerdictSummary with winner and justification
        """
        # Get verdict from state
        verdict = state.get("verdict")

        if not verdict:
            # No verdict in state, infer from messages
            self.logger.warning("No verdict in state, inferring from messages")
            return self._infer_verdict_from_messages(state.get("messages", []))

        # Extract winner information
        winner = verdict.get("winner", "No clear winner")

        # Determine winner position
        winner_position = self._determine_position(state, winner)

        # Get justification/explanation
        justification = verdict.get("justification", "No explanation provided")

        return VerdictSummary(
            winner=winner,
            winner_position=winner_position,
            justification=justification,
            confidence=None,  # State doesn't provide confidence
        )

    def _infer_verdict_from_messages(self, messages: List[Dict[str, Any]]) -> VerdictSummary:
        """Infer verdict from messages if verdict field is missing."""
        if not messages:
            return VerdictSummary(
                winner="No clear winner",
                winner_position="PRO",
                justification="No messages available to infer verdict",
            )

        # Look at last message from judge
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")

        # Simple heuristic: if content contains "won" or "success" -> PRO won
        if "won" in content.lower() or "success" in content.lower():
            winner = "PRO"
            winner_position = "PRO"
        elif "lost" in content.lower() or "fail" in content.lower():
            winner = "CON"
            winner_position = "CON"
        else:
            winner = "No clear winner"
            winner_position = "PRO"

        # Try to extract justification
        justification = content

        return VerdictSummary(
            winner=winner,
            winner_position=winner_position,
            justification=justification,
        )

    def _determine_position(self, state: Dict[str, Any], winner: str) -> str:
        """Determine if role is PRO or CON position."""
        # Check custom prompts for TPM role detection
        pro_custom_prompt = state.get("pro_custom_prompt")
        con_custom_prompt = state.get("con_custom_prompt")

        # If TPM is debating (custom prompts), determine by content
        if pro_custom_prompt and "TPM" in pro_custom_prompt:
            return "PRO"
        elif con_custom_prompt and "TPM" in con_custom_prompt:
            return "CON"

        # For standard debates, PRO and CON are fixed
        if not (pro_custom_prompt or con_custom_prompt):
            # Map standard roles to positions
            return "PRO" if winner == "PRO" else "CON"

        # Default: return the winner as-is (should be "PRO" or "CON")
        return winner.upper() if winner.lower() in ["pro", "con"] else winner

    def _extract_qa_summary(self, state: Dict[str, Any]) -> List[QAPair]:
        """Extract Q&A pairs from debate messages.

        Args:
            state: DebateState dictionary

        Returns:
            List of QAPair objects (3-10 pairs)
        """
        messages = state.get("messages", [])
        qa_pairs: List[QAPair] = []

        # Extract questions and answers from messages
        for msg in messages:
            speaker = msg.get("speaker", "unknown")

            # Look for questions in content
            content = msg.get("content", "")

            # Extract Q&A if content has question/answer pattern
            if "?" in content or "?" in content:
                # This might be a question
                question = self._extract_question_from_message(msg)
                if question:
                    answer = self._find_answer_to_question(messages, msg)

                    if answer:
                        qa_pairs.append(QAPair(
                            question=question,
                            answer=answer.get("content", ""),
                            stage=msg.get("stage", "unknown"),
                            speaker=speaker,
                            validated=True,  # From debate state, considered validated
                            priority=len(qa_pairs) + 1,
                        ))

        # Ensure 3-10 pairs as per validation
        if len(qa_pairs) < 3:
            self.logger.warning(f"Only {len(qa_pairs)} Q&A pairs found, expected 3-10")

        return qa_pairs[:10]

    def _extract_question_from_message(self, msg: Dict[str, Any]) -> Optional[str]:
        """Extract a question from a message."""
        content = msg.get("content", "")

        # Look for question patterns
        question_patterns = [
            "What about",
            "How would",
            "Can you explain",
            "What are your thoughts on",
        ]

        for pattern in question_patterns:
            if pattern in content:
                return content

        # Check for question mark
        if "?" in content:
            # Try to extract the question up to the question mark
            parts = content.split("?")
            if len(parts) > 1:
                return parts[0].strip()

        return None

    def _find_answer_to_question(self, messages: List[Dict[str, Any]], question_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find answer to a question in subsequent messages."""
        question_idx = messages.index(question_msg)

        # Look at next few messages for answer
        for msg in messages[question_idx + 1:question_idx + 4]:
            speaker = msg.get("speaker", "unknown")
            content = msg.get("content", "")

            # Answer should be from a different speaker (not the questioner)
            if speaker != question_msg.get("speaker"):
                # Check if it looks like an answer (responds to question topic)
                if any(phrase in content.lower() for phrase in
                    ["I think", "My position", "In my view", "Therefore", "However"]):
                    return msg

        return None

    def _extract_tpm_analysis(self, state: Dict[str, Any]) -> TPMAnalysis:
        """Extract TPM analysis from state if TPM participated.

        Args:
            state: DebateState dictionary

        Returns:
            TPMAnalysis with weaknesses and recommendations
        """
        # Check if TPM participated
        pro_custom_prompt = state.get("pro_custom_prompt", "")

        if not pro_custom_prompt or "TPM" not in pro_custom_prompt:
            # No TPM participation
            self.logger.info("TPM did not participate in this debate")
            return TPMAnalysis(
                position_summary="TPM did not participate in this debate",
                weaknesses=[],
                recommended_improvements=[],
                victory_assessment="unclear",
            )

        # Extract TPM's position and messages
        tpm_position = self._determine_position(state, "TPM")

        # Collect TPM messages
        messages = state.get("messages", [])
        tpm_messages = [
            msg for msg in messages
            if msg.get("speaker") == tpm_position
        ]

        if not tpm_messages:
            return TPMAnalysis(
                position_summary="No TPM messages found in debate state",
                weaknesses=[],
                recommended_improvements=[],
                victory_assessment="unclear",
            )

        # Analyze TPM content for weaknesses and improvements
        all_content = " ".join([msg.get("content", "") for msg in tpm_messages])
        content_lower = all_content.lower()

        # Look for self-identified weaknesses
        weaknesses: List[TPMWeakness] = []

        if "weakness" in content_lower or "gap" in content_lower or "limitation" in content_lower:
            category = self._classify_weakness_category(content_lower)
            weaknesses.append(TPMWeakness(
                category="self_identified",
                description="Self-identified weakness extracted from TPM's statements",
                severity=self._determine_severity(content_lower),
                source="TPM",
            ))

        # Look for recommended improvements
        improvements: List[str] = []

        if "should" in content_lower or "recommend" in content_lower or "improve" in content_lower:
            # Extract improvement suggestions
            for msg in tpm_messages:
                content = msg.get("content", "")
                if "should" in content.lower():
                    # Extract recommendation
                    if "should " in content:
                        parts = content.split("should")
                        if len(parts) > 1:
                            improvements.append(parts[1].strip())

        return TPMAnalysis(
            position_summary=self._summarize_position(all_content),
            weaknesses=weaknesses,
            recommended_improvements=improvements,
            victory_assessment=self._assess_victory(content_lower, weaknesses),
        )

    def _classify_weakness_category(self, content: str) -> str:
        """Classify weakness type from content."""
        if "assumption" in content or "assume" in content:
            return "unjustified_assumption"
        elif "risk" in content:
            return "uncovered_risk"
        elif "metric" in content or "data" in content:
            return "weak_metrics"
        elif "evidence" in content:
            return "missing_evidence"
        elif "fallacy" in content:
            return "logical_fallacy"
        elif "value prop" in content or "unclear" in content:
            return "unclear_value_prop"
        elif "timeline" in content or "feasible" in content:
            return "infeasible_timeline"
        else:
            return "self_identified"

    def _determine_severity(self, content: str) -> str:
        """Determine severity level from content context."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["critical", "major", "significant", "important"]):
            return "high"
        elif any(word in content_lower for word in ["minor", "some", "could"]):
            return "medium"
        else:
            return "low"

    def _summarize_position(self, content: str) -> str:
        """Summarize TPM's position from content."""
        content_lower = content.lower()

        if any(phrase in content_lower for phrase in [
            "supports the proposal", "argues for", "in favor of", "presents the case"
        ]):
            return "TPM presents comprehensive support for AI infrastructure investment"

        elif any(phrase in content_lower for phrase in [
            "questions the feasibility", "raises concerns about", "challenges the assumptions"
        ]):
            return "TPM raises concerns about market demand and infrastructure costs"

        else:
            return "TPM position not clearly identifiable from content"

    def _assess_victory(self, content: str, weaknesses: List[TPMWeakness]) -> str:
        """Assess TPM's victory based on content and weaknesses."""
        content_lower = content.lower()

        # If no weaknesses, unclear
        if not weaknesses:
            return "unclear"

        # If weaknesses exist, assess victory
        if any(w["severity"] == "high" for w in weaknesses):
            return "lost"
        elif any(w["severity"] == "medium" for w in weaknesses):
            return "unclear"
        else:
            return "won"

    def _extract_recommendations(self, state: Dict[str, Any]) -> List[Recommendation]:
        """Extract recommendations from debate messages.

        Args:
            state: DebateState dictionary

        Returns:
            List of Recommendation objects
        """
        messages = state.get("messages", [])
        recommendations: List[Recommendation] = []

        # Collect messages with recommendation indicators
        for msg in messages:
            content = msg.get("content", "").lower()

            # Look for recommendation patterns
            if any(pattern in content for pattern in [
                "i recommend", "we should", "it would be wise", "i suggest",
                "my recommendation is", "our recommendation", "the team recommends"
            ]):
                # Extract recommendation
                recommendation = self._extract_recommendation_text(msg, content)
                if recommendation:
                    role = msg.get("speaker", "unknown")

                    # Determine priority
                    priority = self._determine_priority(content)

                    recommendations.append(Recommendation(
                        agent_role=role,
                        text=recommendation,
                        priority=priority,
                        category="improvement" if "improve" in content else "actionable",
                        actionable=True,
                    ))

        return recommendations

    def _extract_recommendation_text(self, msg: Dict[str, Any], content: str) -> Optional[str]:
        """Extract recommendation text from message."""
        # Try to extract text after recommendation keywords
        patterns = [
            (r"I recommend (.+)", 1),
            (r"We should (.+)", 1),
            (r"It would be wise to (.+)", 1),
            (r"I suggest (.+)", 1),
            (r"My recommendation is (.+)", 1),
        ]

        import re
        for pattern, group_idx in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(group_idx).strip()

        return None

    def _determine_priority(self, content: str) -> str:
        """Determine priority level from content."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["urgent", "critical", "important", "must", "essential"]):
            return "high"
        elif any(word in content_lower for word in ["should", "recommend", "better"]):
            return "medium"
        else:
            return "low"

    def _build_metadata(self, state: Dict[str, Any]) -> ConclusionMetadata:
        """Build metadata from debate state."""
        # Determine debate type
        debate_type = self._determine_debate_type(state)

        # Generate run ID from debate topic
        debate_topic = state.get("debate_topic", "unknown")
        run_id = self._generate_run_id(debate_topic)

        # Generate timestamp
        from datetime import datetime
        generated_at = datetime.utcnow().isoformat() + "Z"

        # Determine TPM victory
        verdict = state.get("verdict", {})
        winner = verdict.get("winner", "No clear winner")
        tpm_victory = (winner == "TPM")

        # Count recommendations
        recommendations_count = len(self._extract_recommendations(state))

        return ConclusionMetadata(
            debate_type=debate_type,
            run_id=run_id,
            generated_at=generated_at,
            source_file=None,  # State doesn't have source file
            total_recommendations=recommendations_count,
            tpm_victory=tpm_victory,
            completion_status="success",
            error_message=None,
        )

    def _determine_debate_type(self, state: Dict[str, Any]) -> str:
        """Determine debate type from state."""
        # Check for document input
        if state.get("document_input"):
            return DebateType.DOCUMENT.value

        # Check for committee debate (custom prompts)
        if state.get("pro_custom_prompt") or state.get("con_custom_prompt"):
            return DebateType.COMMITTEE.value

        # Default to standard
        return DebateType.STANDARD.value

    def _generate_run_id(self, debate_topic: str) -> str:
        """Generate run ID from debate topic."""
        # Create simple run ID from topic
        import hashlib
        topic_hash = hashlib.md5(debate_topic.encode('utf-8', errors='ignore')).hexdigest()[:8]
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{timestamp}-{topic_hash}"

    def _filter_messages_by_stage(self, messages: List[Dict[str, Any]], stage: str) -> List[Dict[str, Any]]:
        """Filter messages by debate stage."""
        return [
            msg for msg in messages
            if msg.get("stage", "").lower() == stage.lower()
        ]
