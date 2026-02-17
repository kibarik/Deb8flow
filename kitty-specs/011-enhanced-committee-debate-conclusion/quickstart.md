# Quickstart: Enhanced Committee Debate Conclusion Report

**Feature**: 011-enhanced-committee-debate-conclusion
**For**: Developers implementing the enhanced conclusion pipeline
**Prerequisites**: Python 3.12+, pytest, existing Deb8flow setup

---

## Overview

The enhanced conclusion report transforms debate outputs into actionable product improvement plans using a hybrid multi-step LLM pipeline.

**Key Concepts**:
- **Stage 1 (Extraction)**: Dedicated prompts extract verdict and role analyses
- **Stage 2 (Synthesis)**: Single prompt processes structured schema for gaps/recommendations
- **Intermediate Schema**: Pydantic models ensure type safety between stages

---

## Architecture Quick Reference

```
final_report.md
    │
    ├─► Stage 1A: VerdictExtractor ──► Verdict (confidence calculated)
    │
    └─► Stage 1B: RoleAnalyzer ────► RoleAnalysis[] (with evidence)
             │
             ▼
    IntermediateConclusionSchema (Pydantic)
             │
             ▼
    Stage 2: GapRecommendationGenerator
             │
             ├─► CriticalGap[] (max 5)
             └─► Recommendation[] (prioritized)
             │
             ▼
    EnhancedConclusion (Pydantic)
             │
             ▼
    EnhancedConclusionWriter
             │
             ▼
    committee_output/{run_id}/conclusion.md
```

---

## Development Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements (includes pydantic, langchain)
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov
```

### 2. Create New Analyzer

```bash
# Create analyzer file in src/analyzers/
touch src/analyzers/your_analyzer.py
```

**Template**:

```python
from src.nodes.base_component import BaseComponent
from src.types.conclusion_types import IntermediateConclusionSchema
from typing import Dict, Any

class YourAnalyzer(BaseComponent):
    """Brief description of what this analyzer does."""

    def __init__(self, llm_config=None):
        super().__init__(llm_config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, intermediate_schema: IntermediateConclusionSchema) -> Dict[str, Any]:
        """
        Process intermediate schema and return results.

        Args:
            intermediate_schema: Output from Stage 1

        Returns:
            Dictionary with analysis results
        """
        self.logger.info("Running YourAnalyzer")

        # Your analysis logic here

        return {"result": "your_result"}
```

### 3. Add Pydantic Model

Edit `src/types/conclusion_types.py`:

```python
from pydantic import BaseModel, Field
from typing import List

class YourNewModel(BaseModel):
    """Description of your model."""

    field_name: str = Field(..., description="Field description")

    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validation logic."""
        if not v:
            raise ValueError("field_name cannot be empty")
        return v
```

### 4. Create Prompt Template

Create file in `src/prompts/`:

```markdown
# Your Prompt Template

You are analyzing debate content to extract specific insights.

## Input Data
{input_data}

## Output Format
Provide a JSON response with the following structure:
{
  "field_name": "value"
}

## Instructions
1. Read the input data carefully
2. Extract the requested information
3. Output ONLY valid JSON
```

### 5. Write Tests

Create test file in `tests/test_enhanced_conclusion/`:

```python
import pytest
from src.analyzers.your_analyzer import YourAnalyzer
from src.types.conclusion_types import IntermediateConclusionSchema

def test_your_analyzer_basic():
    """Test basic functionality of YourAnalyzer."""
    analyzer = YourAnalyzer()

    # Create test input
    test_input = IntermediateConclusionSchema(
        verdict=...,
        role_analyses=[...]
    )

    # Run analyzer
    result = analyzer(test_input)

    # Assert results
    assert "result" in result
    assert result["result"] == "expected_value"
```

Run tests:

```bash
# Run specific test file
pytest tests/test_enhanced_conclusion/test_your_analyzer.py

# Run all enhanced conclusion tests
pytest tests/test_enhanced_conclusion/

# Run with coverage
pytest tests/test_enhanced_conclusion/ --cov=src/analyzers
```

---

## Key Implementation Points

### Confidence Calculation (FR-029)

```python
from src.utils.confidence_calculator import calculate_confidence

# In VerdictExtractor
room_outcomes = {"TPM_vs_CPO": "CON", "TPM_vs_CFO": "CON", ...}
judge_rationales = [judge1_rationale, judge2_rationale, ...]

confidence = calculate_confidence(room_outcomes, judge_rationales)
# Returns: "High", "Medium", or "Low"
```

### Evidence Extraction (FR-031)

All analyzers must extract evidence references:

```python
from src.types.conclusion_types import EvidenceReference

evidence = EvidenceReference(
    room_id="TPM_vs_CPO",
    speaker_role="CPO",
    turn_index=3,
    quote="The platform introduces significant risk..."
)
```

### Length Validation (FR-030)

```python
from src.types.conclusion_types import RoleAnalysis

# This will raise ValidationError if > 5 items
role_analysis = RoleAnalysis(
    role_name="TPM",
    strengths=[...],  # Max 5
    weaknesses=[...]  # Max 5
)
```

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
# Run debate with debug logging
python main.py --log-level DEBUG
```

### 2. Inspect Intermediate Schema

Add breakpoint in `ConclusionReportNode` after Stage 1:

```python
import pdb; pdb.set_trace()

# Inspect intermediate schema
print(intermediate_schema.verdict.confidence)
for analysis in intermediate_schema.role_analyses:
    print(f"{analysis.role_name}: {len(analysis.strengths)} strengths")
```

### 3. Validate LLM Output

```python
from src.types.conclusion_types import Verdict
import json

# Parse LLM output
llm_output = '{"answer": "...", "confidence": "High", ...}'
try:
    verdict = Verdict(**json.loads(llm_output))
    print("Valid:", verdict)
except ValidationError as e:
    print("Invalid:", e)
```

---

## Testing Against Real Data

### 1. Use Existing Committee Debates

```bash
# Run a committee debate
python product_committee.py --question "Test question"

# Check output
ls -la committee_output/

# Use for testing enhanced conclusion
pytest tests/test_enhanced_conclusion/test_integration.py --debate-path committee_output/RUN_*/
```

### 2. Test Evidence Traceability

```python
from tests.contract.test_evidence_references import test_evidence_completeness

# Verify all evidence references have required fields
test_evidence_completeness()
```

### 3. Validate Length Constraints

```python
from tests.test_enhanced_conclusion.test_role_analyzer import test_role_analysis_length_limits

# Verify 3-5 bullet limit enforcement
test_role_analysis_length_limits()
```

---

## Common Issues

### Issue 1: LLM Returns Invalid JSON

**Symptom**: `json.JSONDecodeError` in analyzer

**Solution**:
1. Check prompt template includes "Output ONLY valid JSON"
2. Add retry logic in analyzer
3. Use structured output if LLM supports it

### Issue 2: Pydantic Validation Error

**Symptom**: `ValidationError` on model instantiation

**Solution**:
1. Check field constraints (max_length, min_length)
2. Ensure all required fields are present
3. Verify custom validators logic

### Issue 3: Evidence Reference Missing Fields

**Symptom**: Test fails with "missing required field: room_id"

**Solution**:
1. Ensure LLM prompt explicitly requests all fields
2. Add validation logic in analyzer
3. Use default values only where appropriate

---

## Performance Optimization

### Target: < 10 seconds (FR-028)

**Bottlenecks**:
1. LLM API latency (typically 1-3 seconds per call)
2. File I/O for reading final_report.md
3. Pydantic validation overhead

**Optimization Strategies**:
- Run Stage 1A and 1B in parallel (asyncio)
- Cache parsed final_report.md if multiple stages need it
- Use streaming responses where supported

---

## Next Steps

1. **Implement Stage 1 Analyzers**:
   - `VerdictExtractor` with confidence calculation
   - `RoleAnalyzer` with evidence extraction

2. **Implement Stage 2 Analyzer**:
   - `GapRecommendationGenerator`

3. **Update ConclusionWriter**:
   - Format enhanced conclusion.md per spec

4. **Write Tests**:
   - Unit tests for each analyzer
   - Integration test for full pipeline
   - Contract tests for evidence/length compliance

---

## Resources

- **Feature Spec**: [spec.md](./spec.md) - Complete requirements (31 FRs, 7 SCs)
- **Data Model**: [data-model.md](./data-model.md) - Pydantic schema definitions
- **Implementation Plan**: [plan.md](./plan.md) - Architecture and phases
- **Existing Code**: `src/nodes/conclusion_report_node.py` - Current implementation
- **Test Examples**: `tests/` - Existing test patterns

---

*Quickstart: 2025-02-16*
