"""
Gap & Recommendation Generator for Enhanced Committee Conclusion.

This module implements Stage 2 of the enhanced conclusion pipeline:
- Identifies critical gaps from cross-role weaknesses
- Generates actionable recommendations with problem→action→metric format
- Ranks gaps by severity (number of sources × argument strength × judge emphasis)
"""

import json
import logging
from typing import List, Dict, Any, Tuple

from src.analyzers.base_analyzer import EnhancedAnalyzer
from src.types.enhanced_conclusion_types import (
    IntermediateConclusionSchema,
    CriticalGap,
    Recommendation,
    EvidenceReference,
    Weakness,
)


class GapRecommendationGenerator(EnhancedAnalyzer):
    """Generate critical gaps and recommendations from intermediate schema.

    Takes Stage 1 output (verdict + role analyses) and generates:
    - Critical gaps identified from cross-role weaknesses
    - Actionable recommendations with problem→action→metric format

    Example:
        >>> generator = GapRecommendationGenerator(llm_config=None)
        >>> gaps, recommendations = generator(intermediate_schema)
        >>> print(f"Found {len(gaps)} critical gaps")
    """

    def __init__(self, llm_config=None):
        """Initialize GapRecommendationGenerator.

        Args:
            llm_config: LLM configuration (optional, uses default if None)
        """
        super().__init__(llm_config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(
        self, intermediate_schema: IntermediateConclusionSchema
    ) -> Tuple[List[CriticalGap], List[Recommendation]]:
        """Generate gaps and recommendations from intermediate schema.

        Args:
            intermediate_schema: Stage 1 output (verdict + role analyses)

        Returns:
            Tuple of (critical_gaps, recommendations)
        """
        self.logger.info("Generating gaps and recommendations from intermediate schema")

        # Identify critical gaps
        gaps = self._identify_critical_gaps(intermediate_schema)

        # Generate recommendations
        recommendations = self._generate_recommendations(intermediate_schema, gaps)

        self.logger.info(f"Generated {len(gaps)} gaps and {len(recommendations)} recommendations")
        return gaps, recommendations

    def _identify_critical_gaps(
        self, schema: IntermediateConclusionSchema
    ) -> List[CriticalGap]:
        """Identify critical gaps from role analyses.

        Analyzes weaknesses across all RoleAnalysis objects to find patterns
        (same weakness mentioned by multiple roles).

        Args:
            schema: Intermediate conclusion schema

        Returns:
            List of critical gaps (max 5)
        """
        self.logger.info("Identifying critical gaps from role analyses")

        # Extract all weaknesses from role analyses
        all_weaknesses = []
        for role_analysis in schema.role_analyses:
            for weakness in role_analysis.weaknesses:
                all_weaknesses.append({
                    "description": weakness.description,
                    "role": role_analysis.role_name,
                    "evidence": weakness.evidence,
                })

        if not all_weaknesses:
            self.logger.warning("No weaknesses found in role analyses")
            return []

        # Use LLM to identify gaps from weaknesses
        gaps_data = self._extract_gaps_with_llm(all_weaknesses, schema.verdict)

        # Rank gaps by severity
        ranked_gaps = self._rank_gaps_by_severity(gaps_data, schema.verdict)

        # Limit to top 5
        top_gaps = ranked_gaps[:5]

        # Convert to CriticalGap objects
        critical_gaps = []
        for gap_data in top_gaps:
            try:
                gap = CriticalGap(**gap_data)
                critical_gaps.append(gap)
            except Exception as e:
                self.logger.warning(f"Failed to create CriticalGap: {e}")

        return critical_gaps

    def _extract_gaps_with_llm(
        self, weaknesses: List[Dict[str, Any]], verdict
    ) -> List[Dict[str, Any]]:
        """Extract gaps from weaknesses using LLM.

        Args:
            weaknesses: List of weakness data
            verdict: Verdict object for context

        Returns:
            List of gap dictionaries
        """
        # Load prompt template
        prompt_template = self._load_prompt("gap_recommendation_prompt.md")

        # Format prompt with weaknesses and verdict
        weaknesses_json = json.dumps(weaknesses, ensure_ascii=False)
        formatted_prompt = self._format_prompt(
            prompt_template,
            weaknesses=weaknesses_json,
            verdict_rationale=verdict.rationale
        )

        # Invoke LLM with retry
        llm_response = self._invoke_with_retry(
            self._create_text_chain(), {"input": formatted_prompt}
        )

        # Parse response
        return self._parse_gap_response(llm_response)

    def _parse_gap_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into gap data.

        Args:
            response: JSON response from LLM

        Returns:
            List of gap dictionaries
        """
        # Clean response (remove markdown code blocks)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse gap response: {e}")
            # Return empty list on parse error
            return []

        # Extract gaps from response
        if "gaps" not in data:
            self.logger.warning("No 'gaps' field in LLM response")
            return []

        return data["gaps"]

    def _rank_gaps_by_severity(
        self, gaps: List[Dict[str, Any]], verdict
    ) -> List[Dict[str, Any]]:
        """Rank gaps by severity score.

        Severity = number of sources × argument strength × judge emphasis

        Args:
            gaps: List of gap data
            verdict: Verdict for judge emphasis check

        Returns:
            Sorted list of gaps (highest severity first)
        """
        def calculate_severity(gap: Dict[str, Any]) -> int:
            """Calculate severity score for a gap."""
            # Number of sources (roles who mentioned this gap)
            num_sources = len(gap.get("sources", []))

            # Argument strength (based on description quality)
            description = gap.get("description", "")
            strength_score = 1  # Default: Low
            if len(description) > 100:
                strength_score = 2  # Medium
            if len(description) > 200:
                strength_score = 3  # High

            # Judge emphasis (mentioned in verdict = 2x)
            judge_emphasis = 1
            if verdict and any(
                source.lower() in verdict.rationale.lower() or
                gap.get("title", "").lower() in verdict.rationale.lower()
                for source in gap.get("sources", [])
            ):
                judge_emphasis = 2

            return num_sources * strength_score * judge_emphasis

        # Sort by severity descending
        sorted_gaps = sorted(gaps, key=calculate_severity, reverse=True)
        return sorted_gaps

    def _generate_recommendations(
        self,
        schema: IntermediateConclusionSchema,
        gaps: List[CriticalGap]
    ) -> List[Recommendation]:
        """Generate recommendations from gaps.

        Each recommendation follows problem→action→metric format (FR-014).

        Args:
            schema: Intermediate conclusion schema
            gaps: List of critical gaps

        Returns:
            List of recommendations (max 5 high-priority)
        """
        self.logger.info("Generating recommendations from gaps")

        if not gaps:
            self.logger.warning("No gaps provided, cannot generate recommendations")
            return []

        # Use LLM to generate recommendations
        recommendations_data = self._generate_recommendations_with_llm(gaps, schema.verdict)

        # Limit high-priority recommendations to 5
        high_priority_count = sum(
            1 for r in recommendations_data if r.get("priority") == "High"
        )

        final_recommendations = []
        high_priority_added = 0

        for rec_data in recommendations_data:
            if rec_data.get("priority") == "High":
                if high_priority_added < 5:
                    try:
                        rec = Recommendation(**rec_data)
                        final_recommendations.append(rec)
                        high_priority_added += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to create Recommendation: {e}")
            else:
                # Medium/Low priority recommendations are unlimited
                try:
                    rec = Recommendation(**rec_data)
                    final_recommendations.append(rec)
                except Exception as e:
                    self.logger.warning(f"Failed to create Recommendation: {e}")

        return final_recommendations

    def _generate_recommendations_with_llm(
        self, gaps: List[CriticalGap], verdict
    ) -> List[Dict[str, Any]]:
        """Generate recommendations from gaps using LLM.

        Args:
            gaps: List of critical gaps
            verdict: Verdict object for context

        Returns:
            List of recommendation dictionaries
        """
        # Load prompt template
        prompt_template = self._load_prompt("gap_recommendation_prompt.md")

        # Format gaps for prompt
        gaps_json = json.dumps(
            [
                {
                    "title": g.title,
                    "severity": g.severity,
                    "description": g.description,
                    "sources": g.sources,
                }
                for g in gaps
            ],
            ensure_ascii=False
        )

        # Format prompt
        formatted_prompt = self._format_prompt(
            prompt_template,
            mode="recommendations",
            gaps=gaps_json,
            verdict_rationale=verdict.rationale if verdict else ""
        )

        # Invoke LLM with retry
        llm_response = self._invoke_with_retry(
            self._create_text_chain(), {"input": formatted_prompt}
        )

        # Parse response
        return self._parse_recommendation_response(llm_response)

    def _parse_recommendation_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into recommendation data.

        Args:
            response: JSON response from LLM

        Returns:
            List of recommendation dictionaries
        """
        # Clean response (remove markdown code blocks)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse recommendation response: {e}")
            return []

        # Extract recommendations from response
        if "recommendations" not in data:
            self.logger.warning("No 'recommendations' field in LLM response")
            return []

        return data["recommendations"]
