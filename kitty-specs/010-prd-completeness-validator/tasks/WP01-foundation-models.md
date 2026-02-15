---
work_package_id: WP01
title: Foundation & Data Models
lane: "doing"
dependencies: []
base_branch: main
base_commit: 97e639587932c9507ab0fec2614bb3e422b7847a
created_at: '2026-02-15T09:50:39.038604+00:00'
subtasks: [T001, T002, T003, T004, T005]
shell_pid: "90243"
agent: "claude"
history:
- date: 2025-02-15
  action: Created
  reason: Initial task breakdown
---

# Work Package: Foundation & Data Models

**Work Package ID**: WP01
**Feature**: 010-prd-completeness-validator
**Status**: Planned
**Estimated Size**: ~300 lines

## Objective

Set up the foundational infrastructure for PRD validation including CLI argument parsing, data models, and utility functions. This work package provides the building blocks that all other work packages depend on.

## Context

You are implementing the PRD Completeness Validator feature for the Deb8flow project. This feature adds a `--check-prd` CLI command that validates Product Requirements Documents against a predefined template using AI analysis.

**Key References**:
- Specification: `kitty-specs/010-prd-completeness-validator/spec.md`
- Data Model: `kitty-specs/010-prd-completeness-validator/data-model.md`
- CLI Contract: `kitty-specs/010-prd-completeness-validator/contracts/cli-interface.md`

**Technical Context**:
- Python 3.12+ with LangChain/LangGraph
- Uses existing `BaseComponent` from `nodes/base_component.py`
- Rich library for console output (already in project)
- Pydantic for data validation
- Standard library `re` for markdown parsing

## Subtasks

### T001: Add --check-prd CLI Arguments to main.py

**Purpose**: Extend the CLI argument parser to support PRD validation mode with all required options.

**Implementation Steps**:

1. **Locate argument parsing in main.py**:
   - Find the existing argument parser setup
   - Add new arguments for PRD validation mode

2. **Add --check-prd argument**:
   ```python
   parser.add_argument(
       "--check-prd",
       type=str,
       metavar="PATH",
       help="Validate a PRD document against the template"
   )
   ```

3. **Add --output-format argument**:
   ```python
   parser.add_argument(
       "--output-format",
       choices=["console", "file", "both"],
       default="both",
       help="Output format for validation results (default: both)"
   )
   ```

4. **Add --min-score argument**:
   ```python
   parser.add_argument(
       "--min-score",
       type=int,
       choices=range(0, 11),
       metavar="0-10",
       help="Minimum acceptable score for pipeline integration"
   )
   ```

**Files Modified**:
- `main.py` - Add 3 new arguments to parser

**Validation**:
- [ ] `python main.py --help` shows new arguments
- [ ] `--output-format` accepts only "console", "file", or "both"
- [ ] `--min-score` accepts only integers 0-10
- [ ] Arguments are parsed without errors

**Notes**:
- Don't implement the validation logic yet (that's WP04)
- Just add argument parsing; CLI will be wired up in WP04

---

### T002: Create PRD Template Constant

**Purpose**: Define the hardcoded PRD template with all 10 required sections from the specification.

**Implementation Steps**:

1. **Create new file**: `nodes/prd_template.py`

2. **Define PRD_TEMPLATE constant**:
   ```python
   from typing import Dict, Any

   PRD_TEMPLATE: Dict[str, Dict[str, Any]] = {
       "Executive Summary": {
           "required": True,
           "description": "Problem, Solution, Success Criteria",
           "keywords": ["problem", "solution", "summary"],
           "min_words": 50
       },
       "Background & Context": {
           "required": True,
           "description": "Market situation, User pain points",
           "keywords": ["background", "context", "market"],
           "min_words": 100
       },
       "Goals & Success Metrics": {
           "required": True,
           "description": "SMART objectives, Key metrics",
           "keywords": ["goals", "metrics", "success", "objectives"],
           "min_words": 50
       },
       "User Personas": {
           "required": True,
           "description": "Target users, Use cases",
           "keywords": ["personas", "users", "audience"],
           "min_words": 50
       },
       "Functional Requirements": {
           "required": True,
           "description": "Core features, User stories",
           "keywords": ["requirements", "features", "functionality"],
           "min_words": 100
       },
       "Non-Functional Requirements": {
           "required": True,
           "description": "Performance, Security, Scalability",
           "keywords": ["performance", "security", "scalability", "non-functional"],
           "min_words": 50
       },
       "Technical Constraints": {
           "required": True,
           "description": "Tech stack limitations, Integrations",
           "keywords": ["constraints", "technical", "stack", "integrations"],
           "min_words": 50
       },
       "Risks & Mitigations": {
           "required": True,
           "description": "Known risks, Contingency plans",
           "keywords": ["risks", "mitigations", "contingency"],
           "min_words": 50
       },
       "Timeline & Milestones": {
           "required": True,
           "description": "Phases, Key dates",
           "keywords": ["timeline", "milestones", "schedule", "phases"],
           "min_words": 50
       },
       "Open Questions": {
           "required": True,
           "description": "Unresolved items, Decision points",
           "keywords": ["questions", "unresolved", "decisions"],
           "min_words": 30
       }
   }
   ```

3. **Add helper function**:
   ```python
   def get_required_sections() -> list[str]:
       """Return list of required PRD section names."""
       return [name for name, config in PRD_TEMPLATE.items() if config["required"]]

   def get_total_section_count() -> int:
       """Return total number of sections in template."""
       return len(PRD_TEMPLATE)
   ```

**Files Created**:
- `nodes/prd_template.py` (~100 lines)

**Validation**:
- [ ] PRD_TEMPLATE has exactly 10 sections
- [ ] All sections match spec.md FR-001 exactly
- [ ] Each section has required, description, keywords, min_words
- [ ] `get_required_sections()` returns all 10 sections
- [ ] Template can be imported without errors

**Notes**:
- Template is hardcoded initially (per spec assumptions)
- Future versions may support custom templates

---

### T003: Create Pydantic Models

**Purpose**: Define the data structures for validation results using Pydantic for type safety and validation.

**Implementation Steps**:

1. **Create new file**: `nodes/models.py` (or `models/prd_validation.py`)

2. **Import required types**:
   ```python
   from typing import List, Optional, Literal
   from pydantic import BaseModel, Field
   ```

3. **Create SectionAnalysis model**:
   ```python
   class SectionAnalysis(BaseModel):
       """Analysis of a single PRD section."""

       section_name: str = Field(
           ...,
           description="Name of the section being analyzed"
       )

       status: Literal["present", "missing", "underdeveloped"] = Field(
           ...,
           description="Whether the section is present, missing, or needs more work"
       )

       content_quality: Optional[str] = Field(
           None,
           description="AI assessment of content quality (null if missing)"
       )

       word_count: int = Field(
           ...,
           ge=0,
           description="Number of words in the section content"
       )

       bullet_count: int = Field(
           ...,
           ge=0,
           description="Number of bullet points in the section"
       )

       suggestions: List[str] = Field(
           default_factory=list,
           description="Specific suggestions for improving this section"
       )

       required: bool = Field(
           ...,
           description="Whether this section is required or optional"
       )
   ```

4. **Create PRDValidationResult model**:
   ```python
   class PRDValidationResult(BaseModel):
       """Complete validation result for a PRD document."""

       overall_score: int = Field(
           ...,
           ge=0,
           le=10,
           description="Overall PRD completeness score from 0-10"
       )

       section_analysis: List[SectionAnalysis] = Field(
           ...,
           description="Analysis of each section in the PRD template"
       )

       recommendations: List[str] = Field(
           ...,
           description="Actionable recommendations for improving the PRD",
           min_length=1,
           max_length=10
       )

       missing_sections: List[str] = Field(
           default_factory=list,
           description="List of required sections not found in the PRD"
       )

       underdeveloped_sections: List[str] = Field(
           default_factory=list,
           description="List of sections present but needing more detail"
       )

       present_sections: List[str] = Field(
           default_factory=list,
           description="List of required sections found in the PRD"
       )

       total_sections: int = Field(
           ...,
           description="Total number of required sections in the template"
       )

       coherence_score: float = Field(
           ...,
           ge=0.0,
           le=2.0,
           description="Coherence score (0-2) measuring logical flow between sections"
       )
   ```

**Files Created**:
- `nodes/models.py` (~100 lines)

**Validation**:
- [ ] Models can be imported without errors
- [ ] SectionAnalysis validates with correct status values
- [ ] PRDValidationResult validates score range 0-10
- [ ] Pydantic raises ValidationError for invalid data
- [ ] Optional fields work correctly (content_quality can be None)

**Notes**:
- Use Pydantic v2 syntax (Field with description)
- Models match data-model.md specification exactly

---

### T004: Create Markdown Parser Utility

**Purpose**: Implement markdown section extraction using regex pattern to detect ## headers.

**Implementation Steps**:

1. **Create new file**: `utils/markdown_parser.py` (create utils/ directory if needed)

2. **Implement extract_sections function**:
   ```python
   import re
   from pathlib import Path
   from typing import Dict

   def extract_sections(prd_path: Path) -> Dict[str, str]:
       """
       Extract sections from a markdown PRD file.

       Args:
           prd_path: Path to the markdown file

       Returns:
           Dictionary mapping section names to content
       """
       content = prd_path.read_text(encoding='utf-8')
       sections = {}
       current_section = None
       current_content = []

       for line in content.split('\n'):
           # Match ## headers (level 2)
           header_match = re.match(r'^##\s+(.+)$', line.strip())
           if header_match:
               # Save previous section
               if current_section:
                   sections[current_section] = '\n'.join(current_content).strip()
               # Start new section
               current_section = header_match.group(1).strip()
               current_content = []
           elif current_section:
               current_content.append(line)

       # Save last section
       if current_section:
           sections[current_section] = '\n'.join(current_content).strip()

       return sections
   ```

3. **Add utility functions**:
   ```python
   def count_words(text: str) -> int:
       """Count words in a text string."""
       return len(text.split())

   def count_bullets(text: str) -> int:
       """Count bullet points in markdown text."""
       return text.count('- ') + text.count('* ')

   def detect_section_headers(prd_path: Path) -> List[str]:
       """
       Detect all ## level-2 headers in a markdown file.

       Returns:
           List of section header names in order
       """
       content = prd_path.read_text(encoding='utf-8')
       headers = []

       for line in content.split('\n'):
           header_match = re.match(r'^##\s+(.+)$', line.strip())
           if header_match:
               headers.append(header_match.group(1).strip())

       return headers
   ```

**Files Created**:
- `utils/__init__.py` (empty file)
- `utils/markdown_parser.py` (~80 lines)

**Validation**:
- [ ] Extracts sections from test PRD with ## headers
- [ ] Handles PRDs with no ## headers (returns empty dict)
- [ ] Preserves section content including newlines
- [ ] Handles empty sections (section name with no content)
- [ ] count_words() returns correct word count
- [ ] count_bullets() counts both - and * bullets
- [ ] detect_section_headers() returns list of headers in order

**Notes**:
- Uses pattern `^##\s+(.+)$` from research.md
- Falls back to empty dict if no headers found
- Preserves original whitespace in content

---

### T005: Add Rich Console Output Utilities

**Purpose**: Create utility functions for formatted console output using Rich library.

**Implementation Steps**:

1. **Create new file**: `utils/console_formatter.py`

2. **Implement console output helpers**:
   ```python
   from rich.console import Console
   from rich.panel import Panel

   console = Console()

   def print_validation_header(prd_path: str, score: int, score_band: str):
       """Print the validation report header."""
       console.print(Panel.fit(
           f"[bold]📋 PRD Validation Report[/]\n"
           f"{'═' * 40}\n"
           f"File: {prd_path}\n"
           f"Score: [bold]{score}/10 ({score_band})[/]",
           title="PRD Validator",
          border_style="bright_blue"
       ))

   def print_section_list(sections: list[str], status: str, emoji: str):
       """Print a list of sections with status indicator."""
       status_text = {
           "present": "[green]✅ Present Sections[/]",
           "missing": "[red]❌ Missing Sections[/]",
           "underdeveloped": "[yellow]⚠️  Underdeveloped Sections[/]"
       }
       console.print(f"\n{status_text.get(status, status)} ({len(sections)}):")
       for section in sections:
           console.print(f"  • {section}")

   def print_recommendations(recommendations: list[str]):
       """Print top recommendations."""
       console.print(f"\n[yellow]💡 Top Recommendations:[/]")
       for i, rec in enumerate(recommendations[:5], 1):
           console.print(f"  {i}. {rec}")

   def print_report_path(report_path: str):
       """Print the report file path."""
       console.print(f"\n📄 Detailed report: {report_path}")

   def print_error(message: str):
       """Print an error message."""
       console.print(f"[red]❌ Error: {message}[/]")

   def print_warning(message: str):
       """Print a warning message."""
       console.print(f"[yellow]⚠️  {message}[/]")
   ```

**Files Created**:
- `utils/console_formatter.py` (~60 lines)

**Validation**:
- [ ] Functions can be imported without errors
- [ ] Console output displays with colors and emojis
- [ ] Panel formatting looks correct
- [ ] Section lists display with proper indentation
- [ ] Error messages display in red

**Notes**:
- Rich is already in project (used by main.py)
- Use emoji characters directly in strings
- Follow color scheme: green (success), red (error), yellow (warning)

---

## Implementation Notes

**Order of Implementation**:
1. T001 first (CLI arguments - quick win)
2. T002 second (template - needed for other tasks)
3. T003 third (models - needed for validation)
4. T004 fourth (parser - independent but useful)
5. T005 last (formatter - can be developed in parallel with T004)

**Testing Strategy**:
- Manual testing for CLI arguments (run `--help`)
- Unit tests for template constant (verify structure)
- Pydantic validation tests for models
- Parser tests with sample PRD files
- Visual inspection for console output

**Integration Points**:
- T001: Modifies main.py (will be used by WP04)
- T002: Template used by WP02 scoring
- T003: Models used by WP02 validation result
- T004: Parser used by WP02 section extraction
- T005: Formatter used by WP03 console output

## Definition of Done

- [ ] All 5 subtasks completed
- [ ] CLI arguments parseable without errors
- [ ] PRD_TEMPLATE matches spec.md FR-001
- [ ] Pydantic models validate successfully
- [ ] Markdown parser extracts sections from test PRD
- [ ] Console formatter displays colored output
- [ ] All files created in correct locations
- [ ] Code follows existing patterns in codebase

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Pydantic version mismatch | Low | Use Pydantic v2 syntax (Field with description) |
| Regex pattern doesn't match all PRDs | Medium | Test with various PRD formats during WP02 |
| Rich formatting issues | Low | Copy existing patterns from main.py |

## Reviewer Guidance

**What to Verify**:
1. CLI arguments match CLI contract exactly
2. PRD_TEMPLATE has all 10 sections from spec.md FR-001
3. Pydantic models have correct field types and constraints
4. Markdown parser handles edge cases (empty PRD, no headers)
5. Console output uses Rich correctly

**Common Issues to Check**:
- Template sections match spec exactly (names, required flags, min_words)
- Pydantic Field() syntax is correct for v2
- Regex pattern uses raw string (r'...')
- Rich markup syntax is correct ([color]text[/])

**Testing Checklist**:
- [ ] Run `python main.py --help` and verify new arguments appear
- [ ] Import models and test with sample data
- [ ] Test parser with a simple markdown file
- [ ] Run console formatter functions and inspect output

## Next Steps

After completing this work package:
1. Run `spec-kitty review WP01` to mark as ready for review
2. Proceed to WP02: Core Validation Logic (depends on this WP)
3. Implementation command: `spec-kitty implement WP01 --base main`

## Activity Log

- 2026-02-15T09:50:39Z – claude – shell_pid=90243 – lane=doing – Assigned agent via workflow command
