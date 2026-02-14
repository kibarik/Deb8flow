# Research: PRD Completeness Validator

**Feature**: 010-prd-completeness-validator
**Date**: 2025-02-15
**Phase**: Phase 0 - Research & Unknowns Resolution

## Executive Summary

This document consolidates research findings for implementing the PRD Completeness Validator feature. All unknowns from the planning phase have been resolved through codebase analysis and best practices research.

## Decisions & Rationale

### 1. Markdown Structure Parsing

**Decision**: Use Python standard library `re` module with pattern `^##\s+(.+)$`

**Rationale**:
- Zero external dependency (aligns with constitution: minimal dependencies)
- Sufficient for detecting markdown level-2 headers which define PRD sections
- Can be extended with `^###\s+(.+)$` for subsection detection if needed
- Fallback: If regex fails to find structure, attempt keyword-based search

**Implementation Pattern**:
```python
import re
from pathlib import Path

def extract_sections(prd_path: Path) -> dict[str, str]:
    content = prd_path.read_text()
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        header_match = re.match(r'^##\s+(.+)$', line)
        if header_match:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = header_match.group(1)
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections
```

### 2. Scoring Algorithm

**Decision**: Hybrid approach combining LLM qualitative assessment with quantitative metrics

**Rationale**:
- LLM provides nuanced evaluation of content quality and coherence
- Quantitative metrics (word count, bullet density) provide baseline scoring
- Aligns with FR-002 scoring rubric (Presence 40%, Depth 40%, Coherence 20%)

**Implementation Components**:

**Quantitative Metrics** (Python):
```python
def calculate_quantitative_score(sections: dict, template: dict) -> dict:
    """Calculate presence and basic depth scores"""
    total_sections = len(template)
    present_sections = sum(1 for s in template if s in sections)

    presence_score = (present_sections / total_sections) * 4  # Max 4 points (40%)

    depth_scores = {}
    for section_name, content in sections.items():
        word_count = len(content.split())
        bullet_count = content.count('-') + content.count('*')

        # Depth heuristic: 100+ words or 5+ bullets = good depth
        if word_count >= 100 or bullet_count >= 5:
            depth_scores[section_name] = 1.0
        elif word_count >= 50 or bullet_count >= 2:
            depth_scores[section_name] = 0.6
        else:
            depth_scores[section_name] = 0.3

    avg_depth = sum(depth_scores.values()) / len(depth_scores) if depth_scores else 0
    depth_score = avg_depth * 4  # Max 4 points (40%)

    return {
        "presence_score": presence_score,
        "depth_score": depth_score,
        "present_sections": present_sections,
        "total_sections": total_sections
    }
```

**Qualitative Assessment** (LLM via BaseComponent):
- Use structured output chain for consistency
- Evaluate coherence between sections
- Identify underdeveloped sections
- Generate actionable recommendations

### 3. Console Output Formatting

**Decision**: Use Rich library's markup syntax with emoji rendering

**Rationale**:
- Rich already in project for existing logging
- Supports color, emojis, and structured formatting
- Cross-platform compatible (aligns with constitution)

**Implementation Pattern**:
```python
from rich.console import Console
from rich.panel import Panel

console = Console()

def format_validation_report(result: PRDValidationResult, prd_path: str):
    console.print(Panel.fit(
        f"[bold]📋 PRD Validation Report[/]\n"
        f"{'=' * 40}\n"
        f"File: {prd_path}\n"
        f"Score: [bold]{result.overall_score}/10[/]",
        title="PRD Validator"
    ))

    # Present sections
    console.print(f"\n[green]✅ Present Sections ({len(result.present_sections)}/{result.total_sections}):[/]")
    for section in result.present_sections:
        console.print(f"  • {section}")

    # Missing sections
    if result.missing_sections:
        console.print(f"\n[red]❌ Missing Sections ({len(result.missing_sections)}):[/]")
        for section in result.missing_sections:
            console.print(f"  • {section}")

    # Recommendations
    console.print(f"\n[yellow]💡 Top Recommendations:[/]")
    for i, rec in enumerate(result.recommendations[:5], 1):
        console.print(f"  {i}. {rec}")
```

## Best Practices Reference

### Industry-Standard PRD Templates

Based on spec.md FR-001, the predefined template aligns with:

1. **Marty Cagan's PRD Structure** (from "INSPIRED"):
   - Problem statement
   - Target audience
   - Success metrics
   - Solutions/requirements
   - Open questions

2. **Silicon Valley Product Group template**:
   - Background
   - Goals
   - User stories
   - Functional requirements
   - Non-functional requirements
   - Release criteria

Our template (10 sections) covers all essential areas while maintaining focus.

### LangGraph Node Integration Pattern

**Analysis of existing codebase**:

From `workflow/debate_workflow.py`:
```python
# Existing pattern: Nodes are LangGraph callables
workflow.add_node("topic_generator", topic_generator_node)
workflow.add_edge(START, "topic_generator")
```

**For PRD validator standalone usage**:
```python
# Direct instantiation (not in LangGraph workflow)
from nodes.prd_validator_node import PRDValidatorNode
from configurations.llm_config import OpenAILLMConfig

node = PRDValidatorNode(llm_config=OpenAILLMConfig(...))
result = node.validate_prd(prd_path="path/to/prd.md")
```

This approach allows:
- Standalone CLI usage (primary use case)
- Future integration into debate workflow (optional)
- Consistent pattern with existing nodes

## Technical Patterns from Codebase

### BaseComponent Usage Pattern

From `nodes/base_component.py`:
- All nodes inherit from `BaseComponent`
- Pass `llm_config` to constructor
- Use `create_chain()` for unstructured output
- Use `create_structured_output_chain()` for structured output (Pydantic models)
- Use `execute_chain()` to invoke with retry logic
- Token tracking via `get_openai_callback()`

**PRD Validator Implementation**:
```python
class PRDValidatorNode(BaseComponent):
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config, temperature=0.0)
        self.prd_template = PRD_TEMPLATE

    def validate_prd(self, prd_path: str, output_format: str = "both") -> dict:
        # Extract sections
        sections = self._extract_sections(prd_path)

        # Quantitative scoring
        quant_scores = self._calculate_quantitative_scores(sections)

        # Qualitative assessment via LLM
        result = self._get_llm_assessment(sections, quant_scores)

        # Generate report
        report_path = None
        if output_format in ["file", "both"]:
            report_path = self._generate_report(prd_path, result)

        # Console output
        if output_format in ["console", "both"]:
            self._print_console_report(result, prd_path)

        return {
            "validation_result": result,
            "report_file_path": report_path,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens
        }
```

### Error Handling Pattern

From existing nodes (e.g., `fact_checker_node.py`):
- Use `self.logger.error()` for error logging
- Retry on API rate limits (429 errors) via `execute_chain()`
- Return structured errors in state when possible
- Use try-except with specific error types

**PRD Validator Error Handling**:
```python
def validate_prd(self, prd_path: str, output_format: str = "both") -> dict:
    try:
        prd_file = Path(prd_path)
        if not prd_file.exists():
            raise FileNotFoundError(f"PRD file not found: {prd_path}")
        if not prd_file.suffix == ".md":
            self.logger.warning(f"Non-markdown file: {prd_path}")
        # ... validation logic
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/]")
        raise
    except Exception as e:
        self.logger.error(f"Validation failed: {e}")
        # Fallback to basic structural validation
        return self._fallback_validation(prd_path)
```

## Unknowns Resolved

| Unknown | Resolution | Status |
|---------|-----------|--------|
| Markdown parsing | Use `re` module with `^##\s+(.+)$` pattern | ✅ Resolved |
| Scoring algorithm | Hybrid: LLM qualitative + quantitative metrics | ✅ Resolved |
| Console formatting | Rich markup with emoji rendering | ✅ Resolved |

## Next Steps

Proceed to **Phase 1: Design & Contracts**:
1. Create `data-model.md` with Pydantic models
2. Create `contracts/` directory with interface definitions
3. Create `quickstart.md` with usage examples
4. Re-evaluate Constitution Check

## References

1. **Existing Codebase**:
   - `nodes/base_component.py` - Base class for all nodes
   - `nodes/fact_checker_node.py` - Example of structured output usage
   - `main.py` - CLI integration pattern
   - `workflow/debate_workflow.py` - LangGraph workflow patterns

2. **External References**:
   - Marty Cagan, "INSPIRED: How to Create Tech Products Customers Love"
   - Rich Python library documentation: https://rich.readthedocs.io/
   - LangChain structured outputs: https://python.langchain.com/docs/modules/model_io/outputs/structured/
