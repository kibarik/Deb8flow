---
work_package_id: WP02
title: Core Validation Logic
lane: "planned"
dependencies: []
base_branch: 010-prd-completeness-validator-WP01
base_commit: 97e639587932c9507ab0fec2614bb3e422b7847a
created_at: '2026-02-15T10:01:30.816581+00:00'
subtasks: [T006, T007, T008, T009, T010, T011, T012]
shell_pid: "94064"
agent: "claude"
history:
- date: 2025-02-15
  action: Created
  reason: Initial task breakdown
---

# Work Package: Core Validation Logic

**Work Package ID**: WP02
**Feature**: 010-prd-completeness-validator
**Status**: Planned
**Estimated Size**: ~450 lines

## Objective

Implement the PRDValidatorNode class with all validation logic including section extraction, quantitative scoring, LLM assessment, and overall score calculation. This is the core of the PRD validation feature.

## Context

You are building the main validation node that uses AI to analyze PRD completeness. This node will:
1. Extract sections from markdown PRD files
2. Calculate quantitative scores (presence, depth)
3. Use LLM to assess coherence and quality
4. Generate actionable recommendations
5. Return structured validation results

**Key References**:
- Data Model: `kitty-specs/010-prd-completeness-validator/data-model.md`
- Research: `kitty-specs/010-prd-completeness-validator/research.md`
- BaseComponent: `nodes/base_component.py`

**Dependencies**:
- WP01: Needs models (PRDValidationResult), parser (extract_sections), template (PRD_TEMPLATE)

**Technical Context**:
- Inherit from `BaseComponent` for LLM integration
- Use structured output chain for consistent LLM responses
- Implement fallback validation when LLM fails
- Token tracking for cost monitoring

## Subtasks

### T006: Create PRDValidatorNode Class

**Purpose**: Create the main node class that orchestrates PRD validation.

**Implementation Steps**:

1. **Create new file**: `nodes/prd_validator_node.py`

2. **Import dependencies**:
   ```python
   import logging
   from pathlib import Path
   from typing import Optional, Literal
   from nodes.base_component import BaseComponent
   from configurations.llm_config import LLMConfig
   from nodes.prd_template import PRD_TEMPLATE
   from nodes.models import PRDValidationResult, SectionAnalysis
   from utils.markdown_parser import extract_sections, count_words, count_bullets
   from utils.console_formatter import console, print_error
   ```

3. **Create PRDValidatorNode class**:
   ```python
   class PRDValidatorNode(BaseComponent):
       """Node for validating PRD documents against a template."""

       def __init__(self, llm_config: LLMConfig, temperature: float = 0.0):
           """
           Initialize the PRD validator node.

           Args:
               llm_config: LLM configuration for AI assessment
               temperature: Temperature for LLM responses (default: 0.0 for consistency)
           """
           super().__init__(llm_config, temperature)
           self.prd_template = PRD_TEMPLATE
           self.logger = logging.getLogger(self.__class__.__name__)

       def validate_prd(
           self,
           prd_path: str,
           output_format: Literal["console", "file", "both"] = "both"
       ) -> dict:
           """
           Validate a PRD document against the template.

           Args:
               prd_path: Path to the PRD markdown file
               output_format: Output format for results

           Returns:
               Dictionary with validation_result, report_file_path, and token counts
           """
           self.logger.info(f"Starting PRD validation for: {prd_path}")

           # Validate file exists
           prd_file = Path(prd_path)
           if not prd_file.exists():
               raise FileNotFoundError(f"PRD file not found: {prd_path}")

           # Extract sections
           sections = self._extract_sections(prd_file)

           # Calculate quantitative scores
           quant_scores = self._calculate_quantitative_scores(sections)

           # Get LLM assessment
           llm_result = self._get_llm_assessment(sections, quant_scores)

           # Calculate overall score
           overall_score = self._calculate_overall_score(
               quant_scores["presence_score"],
               quant_scores["depth_score"],
               llm_result.get("coherence_score", 0.0)
           )

           # Build validation result
           validation_result = self._build_validation_result(
               overall_score, sections, quant_scores, llm_result
           )

           # Generate reports (will be implemented in WP03)
           report_path = None  # TODO: Implement in WP03

           # Console output (will be implemented in WP03)
           # TODO: Implement in WP03

           return {
               "validation_result": validation_result,
               "report_file_path": report_path,
               "prompt_tokens": self.prompt_tokens,
               "completion_tokens": self.completion_tokens
           }
   ```

**Files Created**:
- `nodes/prd_validator_node.py` (~150 lines scaffold)

**Validation**:
- [ ] Class can be instantiated with LLM config
- [ ] validate_prd() method accepts prd_path and output_format
- [ ] FileNotFoundError raised for non-existent files
- [ ] Method returns dict with correct structure
- [ ] Token tracking initialized from BaseComponent

**Notes**:
- This is the scaffold; methods will be implemented in subsequent subtasks
- Report generation (T013-T016) will be implemented in WP03
- Follow existing node patterns (e.g., FactCheckNode)

---

### T007: Implement _extract_sections Method

**Purpose**: Extract sections from markdown PRD file using the parser from WP01.

**Implementation Steps**:

1. **Add method to PRDValidatorNode**:
   ```python
   def _extract_sections(self, prd_file: Path) -> dict[str, str]:
       """
       Extract sections from PRD markdown file.

       Args:
           prd_file: Path to the PRD file

       Returns:
           Dictionary mapping section names to content
       """
       try:
           sections = extract_sections(prd_file)
           self.logger.info(f"Extracted {len(sections)} sections from PRD")
           return sections
       except Exception as e:
           self.logger.error(f"Failed to extract sections: {e}")
           raise
   ```

2. **Add section normalization**:
   ```python
   def _normalize_section_name(self, name: str) -> str:
       """
       Normalize section name for matching.

       Removes extra whitespace, special characters, etc.
       """
       return name.strip().rstrip(':')
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Method uses extract_sections from utils.markdown_parser
- [ ] Returns dictionary with section names as keys
- [ ] Handles PRDs with no sections (returns empty dict)
- [ ] Logs number of sections extracted
- [ ] Exception handling prevents crashes

**Notes**:
- Reuses parser from WP01 (T004)
- Section normalization helps match template names

---

### T008: Implement _calculate_quantitative_scores Method

**Purpose**: Calculate presence (40%) and depth (40%) scores using quantitative metrics.

**Implementation Steps**:

1. **Add method to PRDValidatorNode**:
   ```python
   def _calculate_quantitative_scores(self, sections: dict[str, str]) -> dict:
       """
       Calculate quantitative scores for PRD completeness.

       Args:
           sections: Dictionary of section names to content

       Returns:
           Dictionary with presence_score, depth_score, and metadata
       """
       total_sections = len(self.prd_template)
       present_sections = sum(
           1 for name in self.prd_template
           if self._normalize_section_name(name) in
              [self._normalize_section_name(s) for s in sections.keys()]
       )

       # Presence score: 40% (max 4 points)
       presence_score = (present_sections / total_sections) * 4.0

       # Depth score: 40% (max 4 points)
       depth_scores = []
       for section_name, config in self.prd_template.items():
           normalized_name = self._normalize_section_name(section_name)
           matching_sections = [
               (k, v) for k, v in sections.items()
               if self._normalize_section_name(k) == normalized_name
           ]

           if not matching_sections:
               depth_scores.append(0.0)
               continue

           content = matching_sections[0][1]
           word_count = count_words(content)
           bullet_count = count_bullets(content)
           min_words = config.get("min_words", 50)

           # Depth heuristic
           if word_count >= min_words * 2 or bullet_count >= 5:
               depth_scores.append(1.0)
           elif word_count >= min_words or bullet_count >= 2:
               depth_scores.append(0.6)
           else:
               depth_scores.append(0.3)

       avg_depth = sum(depth_scores) / len(depth_scores) if depth_scores else 0
       depth_score = avg_depth * 4.0  # Max 4 points

       return {
           "presence_score": presence_score,
           "depth_score": depth_score,
           "present_sections": present_sections,
           "total_sections": total_sections,
           "depth_scores": dict(zip(self.prd_template.keys(), depth_scores))
       }
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Presence score ranges 0-4 (40% of total)
- [ ] Depth score ranges 0-4 (40% of total)
- [ ] All sections present = 4.0 presence score
- [ ] No sections present = 0.0 presence score
- [ ] Depth scoring uses min_words from template
- [ ] Returns metadata for debugging

**Notes**:
- Scoring algorithm from research.md and spec.md FR-002
- Depth heuristic: 2x min_words or 5+ bullets = full points
- Section name normalization handles "Section:" vs "Section"

---

### T009: Create System Prompt for PRD Validation

**Purpose**: Create the system prompt that guides the LLM in assessing PRD quality and coherence.

**Implementation Steps**:

1. **Create new file**: `prompts/prd_validator_system.md`

2. **Write system prompt**:
   ```markdown
   You are an expert Product Manager and Technical Writer specializing in Product Requirements Documents (PRDs). Your task is to analyze a PRD and assess its completeness, quality, and coherence.

   # PRD Template

   The PRD should contain the following 10 sections:
   1. Executive Summary - Problem, Solution, Success Criteria
   2. Background & Context - Market situation, User pain points
   3. Goals & Success Metrics - SMART objectives, Key metrics
   4. User Personas - Target users, Use cases
   5. Functional Requirements - Core features, User stories
   6. Non-Functional Requirements - Performance, Security, Scalability
   7. Technical Constraints - Tech stack, Integrations
   8. Risks & Mitigations - Known risks, Contingency plans
   9. Timeline & Milestones - Phases, Key dates
   10. Open Questions - Unresolved items, Decision points

   # Your Task

   Given the extracted sections from a PRD, provide:

   1. **Coherence Score** (0-2 points):
      - 2.0: Excellent flow, clear connections between sections
      - 1.0: Adequate flow, some connections unclear
      - 0.0: Poor flow, sections seem disconnected

   2. **Section Analysis**: For each section in the template, provide:
      - Status: "present", "missing", or "underdeveloped"
      - Content Quality: Brief assessment (2-3 sentences)
      - Suggestions: 2-3 specific improvement suggestions

   3. **Top Recommendations**: 3-5 actionable recommendations for improving the PRD, prioritized by impact

   # Assessment Criteria

   - **Present**: Section exists with sufficient content (meets minimum word count)
   - **Underdeveloped**: Section exists but lacks detail (below minimum word count or vague)
   - **Missing**: Section not found in PRD

   - **Content Quality**: Assess based on:
     - Clarity and specificity
     - Use of data/metrics where appropriate
     - Actionable language
     - Completeness for the given section type

   # Output Format

   Provide your analysis in a structured, concise format that can be easily parsed.
   Focus on actionable feedback that will help the author improve their PRD.
   ```

**Files Created**:
- `prompts/prd_validator_system.md` (~80 lines)

**Validation**:
- [ ] Prompt clearly defines assessment criteria
- [ ] Scoring rubric is explicit (0-2 for coherence)
- [ ] Section status definitions match spec
- [ ] Requested output format is structured
- [ ] Prompt is concise enough for LLM context

**Notes**:
- Keep prompt under 1000 tokens to leave room for PRD content
- Focus on structure over style (per spec non-goals)
- Emphasize actionable feedback

---

### T010: Implement _get_llm_assessment Method

**Purpose**: Use LLM to assess PRD coherence, quality, and generate recommendations via structured output.

**Implementation Steps**:

1. **Load system prompt**:
   ```python
   def _load_system_prompt(self) -> str:
       """Load the system prompt for PRD validation."""
       prompt_path = Path(__file__).parent.parent / "prompts" / "prd_validator_system.md"
       return prompt_path.read_text(encoding='utf-8')
   ```

2. **Create Pydantic model for LLM output**:
   ```python
   from pydantic import BaseModel

   class LLMAssessmentResult(BaseModel):
       """Structured output from LLM assessment."""

       coherence_score: float = Field(..., ge=0.0, le=2.0)
       section_assessments: list[dict] = Field(..., description="Section analysis results")
       recommendations: list[str] = Field(..., min_length=3, max_length=10)
   ```

3. **Implement _get_llm_assessment method**:
   ```python
   def _get_llm_assessment(self, sections: dict, quant_scores: dict) -> dict:
       """
       Get LLM assessment of PRD quality and coherence.

       Args:
           sections: Extracted PRD sections
           quant_scores: Quantitative scoring results

       Returns:
           Dictionary with coherence_score, section_assessments, recommendations
       """
       system_prompt = self._load_system_prompt()

       # Build human prompt with PRD content
       sections_text = "\n\n".join([
           f"## {name}\n{content[:500]}..."  # Truncate for token limits
           for name, content in sections.items()
       ])

       human_prompt = f"""Analyze the following PRD sections:

   {sections_text}

   Quantitative Assessment:
   - Present Sections: {quant_scores['present_sections']}/{quant_scores['total_sections']}
   - Presence Score: {quant_scores['presence_score']:.1f}/4.0
   - Depth Score: {quant_scores['depth_score']:.1f}/4.0

   Provide your structured assessment."""

       try:
           # Create structured output chain
           chain = self.create_structured_output_chain(
               system_template=system_prompt,
               human_template=human_prompt,
               output_model=LLMAssessmentResult
           )

           # Execute chain
           result: LLMAssessmentResult = self.execute_chain({"prd_content": sections_text})

           return {
               "coherence_score": result.coherence_score,
               "section_assessments": result.section_assessments,
               "recommendations": result.recommendations,
               "llm_success": True
           }

       except Exception as e:
           self.logger.error(f"LLM assessment failed: {e}")
           # Return fallback assessment
           return self._fallback_assessment(sections, quant_scores)
   ```

4. **Implement fallback assessment**:
   ```python
   def _fallback_assessment(self, sections: dict, quant_scores: dict) -> dict:
       """
       Provide basic assessment when LLM fails.

       Uses quantitative metrics only.
       """
       # Basic coherence based on section count
       section_ratio = quant_scores['present_sections'] / quant_scores['total_sections']
       coherence_score = min(2.0, section_ratio * 2.0)

       # Generate basic recommendations
       recommendations = []
       missing = quant_scores['total_sections'] - quant_scores['present_sections']
       if missing > 0:
           recommendations.append(f"Add {missing} missing required sections")
       if quant_scores['depth_score'] < 2.0:
           recommendations.append("Expand sections with more detail and specifics")

       return {
           "coherence_score": coherence_score,
           "section_assessments": [],  # Skip detailed assessment in fallback
           "recommendations": recommendations,
           "llm_success": False
       }
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] LLM chain created with structured output
- [ ] System prompt loaded from file
- [ ] LLM returns LLMAssessmentResult successfully
- [ ] Coherence score in range 0-2
- [ ] Recommendations list has 3-10 items
- [ ] Fallback assessment works when LLM fails
- [ ] Token counts tracked correctly

**Notes**:
- Uses BaseComponent.create_structured_output_chain()
- Truncates section content for token limits
- Fallback ensures feature works even if LLM fails
- Per spec.md FR-007: AI API failure must have fallback

---

### T011: Implement _calculate_overall_score Method

**Purpose**: Calculate the final 0-10 score from presence, depth, and coherence components.

**Implementation Steps**:

1. **Add method to PRDValidatorNode**:
   ```python
   def _calculate_overall_score(
       self,
       presence_score: float,
       depth_score: float,
       coherence_score: float
   ) -> int:
       """
       Calculate overall PRD completeness score.

       Scoring rubric (from FR-002):
       - Presence (40%): 0-4 points
       - Depth (40%): 0-4 points
       - Coherence (20%): 0-2 points
       - Total: 0-10 points

       Score bands:
       - 9-10: Excellent (all sections, comprehensive)
       - 7-8: Good (all sections, some gaps)
       - 5-6: Adequate (most sections, significant gaps)
       - 3-4: Poor (many missing, minimal content)
       - 0-2: Fail (essentially empty)

       Args:
           presence_score: Presence component (0-4)
           depth_score: Depth component (0-4)
           coherence_score: Coherence component (0-2)

       Returns:
           Overall score from 0-10
       """
       raw_score = presence_score + depth_score + coherence_score
       rounded_score = round(raw_score)

       # Ensure score is in valid range
       return max(0, min(10, rounded_score))

   def get_score_band(self, score: int) -> str:
       """Get descriptive score band."""
       if score >= 9:
           return "Excellent"
       elif score >= 7:
           return "Good"
       elif score >= 5:
           return "Adequate"
       elif score >= 3:
           return "Poor"
       else:
           return "Fail"
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Score ranges 0-10
- [ ] Correct weighting: Presence 40%, Depth 40%, Coherence 20%
- [ ] Score bands match spec.md FR-002
- [ ] Rounding handles edge cases (e.g., 6.5 → 7)
- [ ] get_score_band() returns correct labels

**Notes**:
- Scoring algorithm from spec.md FR-002
- Round to nearest integer for final score
- Clamp to 0-10 range to handle edge cases

---

### T012: Add Error Handling and Fallback Validation

**Purpose**: Implement comprehensive error handling for file operations, API failures, and edge cases.

**Implementation Steps**:

1. **Wrap validate_prd with error handling**:
   ```python
   def validate_prd(self, prd_path: str, output_format: str = "both") -> dict:
       """Validate PRD with comprehensive error handling."""
       prd_file = Path(prd_path)

       # Validate file exists
       if not prd_file.exists():
           print_error(f"PRD file not found: {prd_path}")
           raise FileNotFoundError(f"PRD file not found: {prd_path}")

       # Validate file is readable
       if not prd_file.is_file():
           print_error(f"Path is not a file: {prd_path}")
           raise ValueError(f"Path is not a file: {prd_path}")

       # Warn on non-markdown files
       if prd_file.suffix != ".md":
           from utils.console_formatter import print_warning
           print_warning(f"File is not markdown (.md): {prd_path}")
           self.logger.warning(f"Non-markdown file: {prd_path}")

       # Check for empty file
       if prd_file.stat().st_size == 0:
           self.logger.error(f"PRD file is empty: {prd_path}")
           return self._empty_prd_result(prd_path)

       try:
           # Main validation logic...
           # (existing implementation)

       except UnicodeDecodeError as e:
           self.logger.error(f"Failed to read file (encoding): {e}")
           print_error(f"Failed to read file: {prd_path}")
           raise

       except Exception as e:
           self.logger.error(f"Validation failed: {e}", exc_info=True)
           print_error(f"Validation failed: {str(e)}")
           raise
   ```

2. **Add helper methods for edge cases**:
   ```python
   def _empty_prd_result(self, prd_path: str) -> dict:
       """Return result for empty PRD file."""
       from nodes.models import PRDValidationResult, SectionAnalysis

       result = PRDValidationResult(
           overall_score=0,
           section_analysis=[],
           recommendations=["PRD file is empty. Add content before validating."],
           missing_sections=list(self.prd_template.keys()),
           underdeveloped_sections=[],
           present_sections=[],
           total_sections=len(self.prd_template),
           coherence_score=0.0
       )

       return {
           "validation_result": result,
           "report_file_path": None,
           "prompt_tokens": 0,
           "completion_tokens": 0
       }
   ```

3. **Add validation for large files**:
   ```python
   MAX_PRD_SIZE = 1024 * 1024  # 1MB

   def _check_file_size(self, prd_file: Path) -> None:
       """Warn if PRD file is unusually large."""
       size = prd_file.stat().st_size
       if size > self.MAX_PRD_SIZE:
           from utils.console_formatter import print_warning
           print_warning(f"PRD file is large ({size/1024/1024:.1f}MB). Validation may be slow.")
           self.logger.warning(f"Large PRD file: {size} bytes")
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] FileNotFoundError raised with clear message for missing files
- [ ] ValueError raised for non-file paths
- [ ] Warning logged for non-markdown files
- [ ] Empty PRD returns score 0 with specific recommendation
- [ ] UnicodeDecodeError handled gracefully
- [ ] Large files trigger warning but still process
- [ ] All exceptions logged with full context

**Notes**:
- Error handling per spec.md FR-007
- Edge cases from spec.md user scenarios
- File size check prevents memory issues
- Preserve original error messages in logs

---

## Implementation Notes

**Order of Implementation**:
1. T006 first (class scaffold)
2. T007 second (simple extraction)
3. T008 third (quantitative scoring)
4. T009 fourth (system prompt - can parallel with T008)
5. T010 fifth (LLM integration - most complex)
6. T011 sixth (scoring helper)
7. T012 last (error handling - ties everything together)

**Testing Strategy**:
- Unit tests for each method
- Mock LLM responses for consistent testing
- Test with various PRD files (complete, incomplete, empty, malformed)
- Verify fallback behavior when LLM fails

**Integration Points**:
- Uses models from WP01 (T003)
- Uses parser from WP01 (T004)
- Uses template from WP01 (T002)
- Uses console formatter from WP01 (T005)
- Will be integrated by WP04 (main.py)
- Will generate reports for WP03

## Definition of Done

- [ ] All 7 subtasks completed
- [ ] PRDValidatorNode can be instantiated
- [ ] validate_prd() returns structured result
- [ ] Quantitative scoring matches rubric
- [ ] LLM assessment generates recommendations
- [ ] Overall score calculation correct
- [ ] Error handling covers all edge cases
- [ ] Fallback validation works without LLM
- [ ] Token tracking operational
- [ ] Code follows existing BaseComponent patterns

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM structured output inconsistent | Medium | High | Use Pydantic with strict validation, test extensively |
| Token limits for large PRDs | Medium | Medium | Truncate content in prompts, warn on large files |
| Fallback logic insufficient | Low | Medium | Ensure fallback provides basic scoring |
| Section name matching fails | Medium | Low | Normalization function handles variations |

## Reviewer Guidance

**What to Verify**:
1. PRDValidatorNode inherits from BaseComponent correctly
2. validate_prd() returns dict with correct structure
3. Scoring algorithm matches spec.md FR-002 exactly
4. LLM chain uses structured output with Pydantic
5. Error handling covers all edge cases from spec
6. Fallback validation works without LLM
7. Token tracking is implemented

**Common Issues to Check**:
- Scoring weights correct (40%, 40%, 20%)
- Coherence score in range 0-2, not 0-4
- Section name normalization handles variations
- Fallback assessment doesn't crash when sections empty
- Error messages are user-friendly

**Testing Checklist**:
- [ ] Test with complete PRD (all sections, good depth)
- [ ] Test with incomplete PRD (missing sections)
- [ ] Test with empty PRD file
- [ ] Test with non-existent file
- [ ] Test with non-markdown file
- [ ] Mock LLM failure and verify fallback works
- [ ] Verify token counts are tracked

## Next Steps

After completing this work package:
1. Run `spec-kitty review WP02` to mark as ready for review
2. Proceed to WP03: Report Generation (depends on this WP)
3. Implementation command: `spec-kitty implement WP02 --base WP01`

## Activity Log

- 2026-02-15T10:01:31Z – claude – shell_pid=94064 – lane=doing – Assigned agent via workflow command
- 2026-02-15T10:02:06Z – claude – shell_pid=94064 – lane=planned – Wrong feature selected, reassigning to correct feature
