---
work_package_id: WP03
title: Report Generation
lane: planned
dependencies: []
subtasks: [T013, T014, T015, T016]
history:
- date: 2025-02-15
  action: Created
  reason: Initial task breakdown
---

# Work Package: Report Generation

**Work Package ID**: WP03
**Feature**: 010-prd-completeness-validator
**Status**: Planned
**Estimated Size**: ~250 lines

## Objective

Implement console and markdown report generation with proper formatting, section-by-section analysis, and actionable recommendations. This completes the user-facing output for the PRD validator.

## Context

You are implementing the output layer of the PRD validator. This work package takes the validation results from WP02 and formats them for user consumption via:
1. Rich console output with emojis and colors
2. Detailed markdown report file (prd_review.md)

**Key References**:
- Console Format: spec.md FR-003
- Report Format: spec.md FR-004
- CLI Contract: `kitty-specs/010-prd-completeness-validator/contracts/cli-interface.md`

**Dependencies**:
- WP02: Needs validation result data structure (PRDValidationResult)
- WP01: Uses console formatter from T005

**Technical Context**:
- Rich library for console formatting (already in project)
- Markdown file writing alongside source PRD
- Report structure matches spec.md FR-004 exactly

## Subtasks

### T013: Implement _print_console_report Method

**Purpose**: Display formatted validation results to console using Rich library.

**Implementation Steps**:

1. **Add method to PRDValidatorNode**:
   ```python
   def _print_console_report(
       self,
       result: PRDValidationResult,
       prd_path: str
   ) -> None:
       """
       Print validation report to console.

       Format matches spec.md FR-003 exactly.

       Args:
           result: Validation result from LLM assessment
           prd_path: Path to the validated PRD file
       """
       from utils.console_formatter import (
           print_validation_header,
           print_section_list,
           print_recommendations,
           print_warning
       )

       # Print header with score
       score_band = self.get_score_band(result.overall_score)
       print_validation_header(prd_path, result.overall_score, score_band)

       # Print present sections
       if result.present_sections:
           print_section_list(result.present_sections, "present", "✅")
           console.print(f"  ({len(result.present_sections)}/{result.total_sections})")

       # Print missing sections
       if result.missing_sections:
           print_section_list(result.missing_sections, "missing", "❌")

       # Print underdeveloped sections with details
       if result.underdeveloped_sections:
           console.print("\n[yellow]⚠️  Underdeveloped Sections:[/]")
           for section in result.underdeveloped_sections:
               # Find the analysis for this section
               analysis = next(
                   (a for a in result.section_analysis if a.section_name == section),
                   None
               )
               if analysis and analysis.suggestions:
                   console.print(f"  • {section} ({analysis.suggestions[0][:50]}...)")
               else:
                   console.print(f"  • {section}")

       # Print top recommendations
       if result.recommendations:
           print_recommendations(result.recommendations)

       # Print score band interpretation
       console.print(f"\n[dim]Score Interpretation: {score_band}[/]")
       if result.overall_score >= 7:
           console.print("[dim]✓ PRD is ready for committee debate[/]")
       elif result.overall_score >= 5:
           print_warning("PRD needs improvements before debate")
       else:
           console.print("[red]PRD requires significant work[/]")
   ```

2. **Update validate_prd to call console output**:
   ```python
   def validate_prd(self, prd_path: str, output_format: str = "both") -> dict:
       # ... existing validation logic ...

       # Console output
       if output_format in ["console", "both"]:
           self._print_console_report(validation_result, prd_path)

       return {
           "validation_result": validation_result,
           "report_file_path": report_path,
           "prompt_tokens": self.prompt_tokens,
           "completion_tokens": self.completion_tokens
       }
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Console output matches spec.md FR-003 format exactly
- [ ] Header shows PRD path and score
- [ ] Present sections listed with ✅ emoji
- [ ] Missing sections listed with ❌ emoji
- [ ] Underdeveloped sections listed with ⚠️ emoji
- [ ] Top recommendations numbered 1-5
- [ ] Score interpretation shown at bottom
- [ ] Colors work correctly (green, red, yellow)

**Notes**:
- Format must match spec.md FR-003 character-for-character
- Use Rich markup: [green], [red], [yellow], [dim]
- Emojis: 📋 ✅ ❌ ⚠️ 💡 📄
- Limit underdeveloped section details to 50 chars

---

### T014: Implement _generate_markdown_report Method

**Purpose**: Generate detailed markdown report file with section-by-section analysis.

**Implementation Steps**:

1. **Add method to PRDValidatorNode**:
   ```python
   from datetime import datetime, timezone

   def _generate_markdown_report(
       self,
       result: PRDValidationResult,
       prd_path: str
   ) -> str:
       """
       Generate detailed markdown validation report.

       Creates prd_review.md adjacent to source PRD file.

       Args:
           result: Validation result from assessment
           prd_path: Path to the validated PRD file

       Returns:
           Path to the generated report file
       """
       from pathlib import Path

       prd_file = Path(prd_path)
       report_path = prd_file.parent / "prd_review.md"

       # Get score band
       score_band = self.get_score_band(result.overall_score)

       # Build report content
       content = self._build_markdown_content(result, prd_path, score_band)

       # Write report
       try:
           report_path.write_text(content, encoding='utf-8')
           self.logger.info(f"Generated report: {report_path}")
           return str(report_path)
       except Exception as e:
           self.logger.error(f"Failed to write report: {e}")
           return None
   ```

2. **Add _build_markdown_content helper**:
   ```python
   def _build_markdown_content(
       self,
       result: PRDValidationResult,
       prd_path: str,
       score_band: str
   ) -> str:
       """Build the markdown report content."""

       lines = [
           "# PRD Validation Report",
           "",
           f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d at %H:%M UTC')}",
           f"**Source File**: {prd_path}",
           f"**Validator**: Deb8flow PRD Completeness Validator v1.0",
           "",
           "## Executive Summary",
           "",
           f"**Overall Score**: {result.overall_score}/10 ({score_band})",
           "",
           self._generate_assessment_paragraph(result),
           "",
           "## Section-by-Section Analysis",
           ""
       ]

       # Add each section's analysis
       for analysis in result.section_analysis:
           lines.extend(self._format_section_analysis(analysis))

       # Add recommendations
       lines.extend(self._format_recommendations(result))

       # Add scoring breakdown
       lines.extend(self._format_scoring_breakdown(result))

       # Add next steps
       lines.extend([
           "",
           "## Next Steps",
           "",
           "1. Address the missing and underdeveloped sections above",
           f"2. Re-run validation: `python main.py --check-prd {prd_path}`",
           "3. Aim for score 8+ before using this PRD for committee debate"
       ])

       return "\n".join(lines)
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Report created in same directory as PRD
- [ ] Report named "prd_review.md"
- [ ] Report contains all sections from spec.md FR-004
- [ ] Executive Summary shows score and assessment
- [ ] Section analysis includes status, quality, suggestions
- [ ] Recommendations grouped by priority
- [ ] File write errors handled gracefully

**Notes**:
- Report structure from spec.md FR-004
- Always overwrite existing prd_review.md
- Use UTC timestamp for consistency

---

### T015: Create Report Template with All Required Sections

**Purpose**: Implement helper methods that format each section of the markdown report.

**Implementation Steps**:

1. **Add helper methods to PRDValidatorNode**:
   ```python
   def _generate_assessment_paragraph(self, result: PRDValidationResult) -> str:
       """Generate one-paragraph assessment for executive summary."""
       if result.overall_score >= 8:
           return (f"The PRD is comprehensive with {len(result.present_sections)}/{result.total_sections} "
                   f"sections present. Content quality is strong throughout.")
       elif result.overall_score >= 6:
           return (f"The PRD covers most required sections ({len(result.present_sections)}/{result.total_sections}) "
                   f"but has some content gaps that should be addressed.")
       elif result.overall_score >= 4:
           return (f"The PRD has significant gaps with {len(result.missing_sections)} missing sections "
                   f"and several underdeveloped areas.")
       else:
           return (f"The PRD is substantially incomplete with only {len(result.present_sections)}/"
                   f"{result.total_sections} sections present. Major revision needed.")

   def _format_section_analysis(self, analysis: SectionAnalysis) -> list[str]:
       """Format a single section's analysis for markdown report."""
       status_emoji = {
           "present": "✅",
           "missing": "❌",
           "underdeveloped": "⚠️"
       }

       lines = [
           f"### {analysis.section_name}",
           f"- **Status**: {status_emoji.get(analysis.status, analysis.status)} "
           f"{analysis.status.capitalize()}",
           f"- **Word Count**: {analysis.word_count}",
       ]

       if analysis.status != "missing":
           lines.append(f"- **Quality**: {analysis.content_quality or 'Not assessed'}")

       if analysis.suggestions:
           lines.append("- **Suggestions**:")
           for suggestion in analysis.suggestions[:3]:  # Max 3 suggestions
               lines.append(f"  - {suggestion}")

       lines.append("")
       return lines

   def _format_recommendations(self, result: PRDValidationResult) -> list[str]:
       """Format recommendations by priority."""
       lines = [
           "",
           "## Recommendations by Priority",
           ""
       ]

       # Group recommendations by priority (simple heuristic)
       high_priority = [r for r in result.recommendations[:3] if "add" in r.lower() or "missing" in r.lower()]
       medium_priority = [r for r in result.recommendations if r not in high_priority]

       if high_priority:
           lines.extend([
               "### High Priority",
               ""
           ])
           for rec in high_priority:
               lines.append(f"- [ ] {rec}")
           lines.append("")

       if medium_priority:
           lines.extend([
               "### Medium Priority",
               ""
           ])
           for rec in medium_priority[:5]:
               lines.append(f"- [ ] {rec}")
           lines.append("")

       return lines

   def _format_scoring_breakdown(self, result: PRDValidationResult) -> list[str]:
       """Format the scoring breakdown section."""
       # Calculate component scores (stored during validation)
       presence_pct = (len(result.present_sections) / result.total_sections) * 40
       depth_pct = result.coherence_score * 10  # Approximate

       lines = [
           "",
           "## Scoring Breakdown",
           "",
           f"- **Presence (40%)**: {presence_pct:.1f}% "
           f"({len(result.present_sections)}/{result.total_sections} sections present)",
           f"- **Depth (40%)**: {depth_pct:.1f}% (based on content quality)",
           f"- **Coherence (20%)**: {result.coherence_score * 10:.1f}% "
           f"(logical flow between sections)",
           "",
           f"**Total**: {result.overall_score}/10",
           ""
       ]
       return lines
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Assessment paragraph varies by score range
- [ ] Section analysis includes status emoji
- [ ] Suggestions formatted as bullet list
- [ ] Recommendations grouped by priority
- [ ] Scoring breakdown shows percentages
- [ ] All sections from spec.md FR-004 present

**Notes**:
- Assessment should be 1-2 sentences max
- Limit suggestions to top 3 per section
- Priority grouping is heuristic-based
- Percentages help users understand scoring

---

### T016: Add Report File Writing with Error Handling

**Purpose**: Implement robust file writing with error handling and user feedback.

**Implementation Steps**:

1. **Update _generate_markdown_report with error handling**:
   ```python
   def _generate_markdown_report(
       self,
       result: PRDValidationResult,
       prd_path: str
   ) -> Optional[str]:
       """
       Generate markdown report with comprehensive error handling.

       Returns None if report generation fails.
       """
       from pathlib import Path
       import errno

       prd_file = Path(prd_path)
       report_path = prd_file.parent / "prd_review.md"

       try:
           # Check if directory is writable
           if not prd_file.parent.exists():
               self.logger.error(f"Directory does not exist: {prd_file.parent}")
               return None

           if not os.access(prd_file.parent, os.W_OK):
               self.logger.error(f"Directory not writable: {prd_file.parent}")
               from utils.console_formatter import print_error
               print_error(f"Cannot write report to {prd_file.parent}")
               return None

           # Build content
           content = self._build_markdown_content(result, prd_path,
                                                   self.get_score_band(result.overall_score))

           # Write atomically (write to temp, then rename)
           temp_path = report_path.with_suffix('.tmp')
           temp_path.write_text(content, encoding='utf-8')

           # Replace existing report
           temp_path.replace(report_path)

           self.logger.info(f"Generated report: {report_path}")
           return str(report_path)

       except PermissionError as e:
           self.logger.error(f"Permission denied writing report: {e}")
           from utils.console_formatter import print_error
           print_error(f"Permission denied: {report_path}")
           return None

       except OSError as e:
           self.logger.error(f"OS error writing report: {e}")
           from utils.console_formatter import print_error
           print_error(f"Failed to write report: {str(e)}")
           return None

       except Exception as e:
           self.logger.error(f"Unexpected error writing report: {e}", exc_info=True)
           return None
   ```

2. **Add report path display to console output**:
   ```python
   def _print_console_report(self, result: PRDValidationResult, prd_path: str,
                            report_path: Optional[str] = None) -> None:
       """Print console report with optional report path."""
       # ... existing console output ...

       # Print report path if available
       if report_path:
           from utils.console_formatter import print_report_path
           print_report_path(report_path)
   ```

3. **Update validate_prd to pass report path**:
   ```python
   def validate_prd(self, prd_path: str, output_format: str = "both") -> dict:
       # ... validation logic ...

       report_path = None
       if output_format in ["file", "both"]:
           report_path = self._generate_markdown_report(validation_result, prd_path)

       # Console output
       if output_format in ["console", "both"]:
           self._print_console_report(validation_result, prd_path, report_path)

       return {
           "validation_result": validation_result,
           "report_file_path": report_path,
           "prompt_tokens": self.prompt_tokens,
           "completion_tokens": self.completion_tokens
       }
   ```

**Files Modified**:
- `nodes/prd_validator_node.py`

**Validation**:
- [ ] Report written to correct location
- [ ] Existing prd_review.md overwritten
- [ ] Permission errors handled gracefully
- [ ] Non-existent directory handled
- [ ] Report path shown in console output
- [ ] Returns None on failure (not crash)
- [ ] Atomic write prevents partial files

**Notes**:
- Atomic write: write to .tmp then rename
- Check directory writability before attempting
- User-friendly error messages
- Report path only shown if file output requested

---

## Implementation Notes

**Order of Implementation**:
1. T013 first (console output - immediate feedback)
2. T014 second (markdown generation - core logic)
3. T015 third (formatting helpers - can parallel with T014)
4. T016 last (error handling - ties everything together)

**Testing Strategy**:
- Visual inspection of console output
- Read generated markdown file
- Test error conditions (read-only dir, full disk)
- Verify format matches spec exactly

**Integration Points**:
- Uses validation result from WP02
- Uses console formatter from WP01 (T005)
- Called by validate_prd in WP02
- Results consumed by WP04 (CLI)

## Definition of Done

- [ ] All 4 subtasks completed
- [ ] Console output matches spec.md FR-003 exactly
- [ ] Markdown report matches spec.md FR-004 exactly
- [ ] Report created in correct location
- [ ] Error handling covers all file operations
- [ ] Report path shown in console when generated
- [ ] User-friendly error messages
- [ ] Atomic write prevents data loss

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Console format doesn't match spec | Medium | Low | Visual testing against spec.md FR-003 |
| Markdown report too verbose | Low | Low | Limit suggestions per section |
| File write failures | Low | Medium | Comprehensive error handling |
| Report path confusion | Low | Low | Show full path in console |

## Reviewer Guidance

**What to Verify**:
1. Console output matches spec.md FR-003 character-for-character
2. Markdown report has all sections from spec.md FR-004
3. Report created adjacent to source PRD
4. Error handling graceful for file operations
5. Report path shown correctly in console
6. Atomic write prevents partial files

**Common Issues to Check**:
- Emoji rendering in console
- Markdown formatting (headers, bullet lists)
- File path handling (absolute vs relative)
- Permission error messages
- Report overwrites existing file

**Testing Checklist**:
- [ ] Run with --output-format console (no file created)
- [ ] Run with --output-format file (no console output)
- [ ] Run with --output-format both (both shown)
- [ ] Test with read-only directory
- [ ] Verify report file contents
- [ ] Check console formatting colors

## Next Steps

After completing this work package:
1. Run `spec-kitty review WP03` to mark as ready for review
2. Proceed to WP04: CLI Integration (depends on this WP)
3. Implementation command: `spec-kitty implement WP03 --base WP02`
