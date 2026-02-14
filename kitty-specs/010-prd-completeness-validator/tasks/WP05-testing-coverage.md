---
work_package_id: WP05
title: Testing Coverage
lane: planned
dependencies: []
subtasks: [T021, T022, T023, T024, T025, T026]
history:
- date: 2025-02-15
  action: Created
  reason: Initial task breakdown
---

# Work Package: Testing Coverage

**Work Package ID**: WP05
**Feature**: 010-prd-completeness-validator
**Status**: Planned
**Estimated Size**: ~350 lines

## Objective

Create comprehensive test coverage including unit tests for parser and scoring, contract tests for CLI interface, and integration tests for full validation flow. This ensures the feature works correctly and can be maintained.

## Context

You are implementing the test suite for the PRD Completeness Validator. This work package creates tests for all components built in WP01-WP04, following the project's pytest-based testing approach.

**Key References**:
- Existing Tests: `tests/test_*.py`
- Spec Success Criteria: `kitty-specs/010-prd-completeness-validator/spec.md`
- Test patterns from existing codebase

**Dependencies**:
- WP01-WP04: Needs complete implementation to test
- Follows existing test patterns in `tests/`

**Technical Context**:
- pytest framework (already in project)
- Mock LLM responses for consistent testing
- Test fixtures with sample PRDs
- Contract tests for CLI behavior
- Integration tests for end-to-end flows

## Subtasks

### T021: Create Test Fixtures Directory with Sample PRDs

**Purpose**: Set up test fixtures with various PRD samples for testing different scenarios.

**Implementation Steps**:

1. **Create fixtures directory**:
   ```bash
   mkdir -p tests/fixtures/prd_samples
   ```

2. **Create complete_prd.md** (all sections, good depth):
   ```markdown
   # Product Requirements Document

   ## Executive Summary
   This product addresses the problem of inefficient inventory management for small businesses.
   Current solutions are expensive and complex. Success: 1000 customers in year 1.

   ## Background & Context
   Small businesses struggle with inventory tracking using spreadsheets.
   Existing tools cost $500+/month, which is prohibitive for businesses with 10-50 employees.
   Market size: 100,000 small businesses in the US alone.

   ## Goals & Success Metrics
   - Acquire 1000 customers in year 1
   - Achieve 80% monthly active user rate
   - <5 minute onboarding time
   - <2 second page load time

   ## User Personas
   - Sarah: Small business owner, 10-50 employees, needs simple inventory tracking
   - Mike: Inventory manager, needs real-time data and alerts

   ## Functional Requirements
   - Users can add/edit inventory items
   - System sends low-stock alerts via email
   - Dashboard shows inventory trends over time
   - Users can export inventory data as CSV

   ## Non-Functional Requirements
   - Performance: Dashboard loads in under 2 seconds
   - Security: Data encrypted at rest and in transit
   - Scalability: System supports 10,000 concurrent users
   - Availability: 99.9% uptime SLA

   ## Technical Constraints
   - Built with Python 3.12+
   - Uses PostgreSQL for data storage
   - Integrates with Shopify API
   - Must work on mobile browsers

   ## Risks & Mitigations
   - Risk: Shopify API changes
     Mitigation: Version pinning and monitoring
   - Risk: Data loss
     Mitigation: Daily backups with 30-day retention
   - Risk: Slow performance with large datasets
     Mitigation: Database indexing and caching

   ## Timeline & Milestones
   - Month 1-2: MVP development
   - Month 3: Beta testing with 10 users
   - Month 4: Public launch

   ## Open Questions
   - Should we support multi-currency?
   - What's the pricing model (freemium vs paid)?
   - Should we integrate with QuickBooks?
   ```

3. **Create incomplete_prd.md** (missing sections):
   ```markdown
   # Product Requirements Document

   ## Executive Summary
   Building an inventory app.

   ## Goals
   Help users track inventory.

   ## Features
   - Add items
   - Delete items
   ```

4. **Create empty_prd.md** (empty file):
   ```markdown
   ```

5. **Create malformed_prd.md** (no ## headers):
   ```markdown
   This is just some text without proper markdown headers.

   It talks about a product but has no structure.
   ```

6. **Create multilingual_prd.md** (mixed languages):
   ```markdown
   # Product Requirements Document

   ## Executive Summary
   This product helps small businesses with inventory management.
   Este producto ayuda a las pequeñas empresas.

   ## Background & Context
   Small businesses need better tools.
   Les petites entreprises ont besoin de meilleurs outils.
   ```

**Files Created**:
- `tests/fixtures/prd_samples/complete_prd.md`
- `tests/fixtures/prd_samples/incomplete_prd.md`
- `tests/fixtures/prd_samples/empty_prd.md`
- `tests/fixtures/prd_samples/malformed_prd.md`
- `tests/fixtures/prd_samples/multilingual_prd.md`

**Validation**:
- [ ] Fixtures directory created
- [ ] complete_prd.md has all 10 sections
- [ ] incomplete_prd.md missing multiple sections
- [ ] empty_prd.md is truly empty
- [ ] malformed_prd.md has no ## headers
- [ ] multilingual_prd.md has mixed languages

**Notes**:
- Fixtures should be realistic PRD examples
- Cover edge cases from spec.md user scenarios
- Include PRDs that score 0, 5, 10

---

### T022: Write Unit Tests for Markdown Parser

**Purpose**: Test the markdown parser utility with various PRD formats.

**Implementation Steps**:

1. **Create test file**: `tests/test_markdown_parser.py`

2. **Write tests for extract_sections**:
   ```python
   import pytest
   from pathlib import Path
   from utils.markdown_parser import extract_sections, count_words, count_bullets

   class TestMarkdownParser:
       """Test markdown parsing utilities."""

       def test_extract_sections_from_complete_prd(self):
           """Test extracting sections from a complete PRD."""
           prd_path = Path("tests/fixtures/prd_samples/complete_prd.md")
           sections = extract_sections(prd_path)

           assert len(sections) == 10
           assert "Executive Summary" in sections
           assert "Background & Context" in sections
           assert "Open Questions" in sections

       def test_extract_sections_from_incomplete_prd(self):
           """Test extracting sections from an incomplete PRD."""
           prd_path = Path("tests/fixtures/prd_samples/incomplete_prd.md")
           sections = extract_sections(prd_path)

           assert len(sections) < 10
           assert "Executive Summary" in sections
           # Many sections missing

       def test_extract_sections_from_empty_prd(self):
           """Test extracting sections from an empty PRD."""
           prd_path = Path("tests/fixtures/prd_samples/empty_prd.md")
           sections = extract_sections(prd_path)

           assert len(sections) == 0

       def test_extract_sections_from_malformed_prd(self):
           """Test extracting sections from a PRD with no ## headers."""
           prd_path = Path("tests/fixtures/prd_samples/malformed_prd.md")
           sections = extract_sections(prd_path)

           assert len(sections) == 0

       def test_extract_sections_preserves_content(self):
           """Test that section content is preserved correctly."""
           prd_path = Path("tests/fixtures/prd_samples/complete_prd.md")
           sections = extract_sections(prd_path)

           executive_summary = sections["Executive Summary"]
           assert "inventory management" in executive_summary
           assert "small businesses" in executive_summary

       def test_count_words(self):
           """Test word counting function."""
           assert count_words("Hello world") == 2
           assert count_words("One two three four") == 4
           assert count_words("") == 0
           assert count_words("  Multiple   spaces  ") == 2

       def test_count_bullets(self):
           """Test bullet counting function."""
           assert count_bullets("- Item 1\n- Item 2") == 2
           assert count_bullets("* Item 1\n* Item 2") == 2
           assert count_bullets("- Mixed\n* Bullets") == 2
           assert count_bullets("No bullets here") == 0
   ```

**Files Created**:
- `tests/test_markdown_parser.py` (~80 lines)

**Validation**:
- [ ] All tests pass
- [ ] Covers complete, incomplete, empty, malformed PRDs
- [ ] Tests edge cases (empty strings, multiple spaces)
- [ ] Word counting accurate
- [ ] Bullet counting accurate

**Notes**:
- Test with all fixture files
- Cover parser edge cases
- Test section name normalization

---

### T023: Write Unit Tests for Scoring Algorithm

**Purpose**: Test the quantitative scoring logic with known inputs and expected outputs.

**Implementation Steps**:

1. **Create test file**: `tests/test_scoring.py`

2. **Write tests for scoring methods**:
   ```python
   import pytest
   from nodes.prd_validator_node import PRDValidatorNode
   from nodes.models import PRDValidationResult
   from configurations.llm_config import OpenAILLMConfig

   class TestScoringAlgorithm:
       """Test PRD scoring algorithm."""

       @pytest.fixture
       def validator(self):
           """Create a validator instance for testing."""
           config = OpenAILLMConfig(
               model_name="gpt-4",
               openai_api_key="test-key"
           )
           return PRDValidatorNode(llm_config=config)

       def test_presence_score_all_sections_present(self, validator):
           """Test presence score when all sections present."""
           sections = {name: "Some content" for name in validator.prd_template.keys()}
           scores = validator._calculate_quantitative_scores(sections)

           assert scores["presence_score"] == 4.0
           assert scores["present_sections"] == 10

       def test_presence_score_half_sections_present(self, validator):
           """Test presence score when half sections present."""
           sections = {name: "Content" for name in list(validator.prd_template.keys())[:5]}
           scores = validator._calculate_quantitative_scores(sections)

           assert scores["presence_score"] == 2.0
           assert scores["present_sections"] == 5

       def test_presence_score_no_sections_present(self, validator):
           """Test presence score when no sections present."""
           sections = {}
           scores = validator._calculate_quantitative_scores(sections)

           assert scores["presence_score"] == 0.0
           assert scores["present_sections"] == 0

       def test_depth_score_comprehensive_content(self, validator):
           """Test depth score with comprehensive content."""
           # Create content with 200+ words and 10+ bullets
           long_content = "Word " * 200 + "\n- Point 1\n- Point 2\n" * 5
           sections = {name: long_content for name in validator.prd_template.keys()}
           scores = validator._calculate_quantitative_scores(sections)

           assert scores["depth_score"] >= 3.5  # High depth

       def test_depth_score_minimal_content(self, validator):
           """Test depth score with minimal content."""
           short_content = "Brief text."
           sections = {name: short_content for name in validator.prd_template.keys()}
           scores = validator._calculate_quantitative_scores(sections)

           assert scores["depth_score"] < 2.0  # Low depth

       def test_calculate_overall_score_excellent(self, validator):
           """Test overall score calculation for excellent PRD."""
           score = validator._calculate_overall_score(
               presence_score=4.0,
               depth_score=4.0,
               coherence_score=2.0
           )

           assert score == 10
           assert validator.get_score_band(score) == "Excellent"

       def test_calculate_overall_score_good(self, validator):
           """Test overall score calculation for good PRD."""
           score = validator._calculate_overall_score(
               presence_score=3.2,
               depth_score=2.8,
               coherence_score=1.0
           )

           assert 7 <= score <= 8
           assert validator.get_score_band(score) in ["Good", "Excellent"]

       def test_calculate_overall_score_fail(self, validator):
           """Test overall score calculation for failing PRD."""
           score = validator._calculate_overall_score(
               presence_score=0.0,
               depth_score=0.0,
               coherence_score=0.0
           )

           assert score == 0
           assert validator.get_score_band(score) == "Fail"

       def test_calculate_overall_score_clamping(self, validator):
           """Test that scores are clamped to 0-10 range."""
           # Test with values that would exceed 10
           score = validator._calculate_overall_score(
               presence_score=5.0,  # Over max
               depth_score=5.0,    # Over max
               coherence_score=3.0  # Over max
           )

           assert score == 10  # Clamped to max

   # Add more tests for edge cases, section name normalization, etc.
   ```

**Files Created**:
- `tests/test_scoring.py` (~100 lines)

**Validation**:
- [ ] Presence score accurate for all, half, no sections
- [ ] Depth score reflects content quality
- [ ] Overall score calculation correct
- [ ] Score bands match spec.md FR-002
- [ ] Score clamping works
- [ ] Edge cases covered

**Notes**:
- Test scoring algorithm from spec.md FR-002
- Use fixture for validator setup
- Test with various input combinations
- Verify score band thresholds

---

### T024: Write Unit Tests for Report Generation

**Purpose**: Test console and markdown report generation formatting.

**Implementation Steps**:

1. **Create test file**: `tests/test_report_generation.py`

2. **Write tests for report formatting**:
   ```python
   import pytest
   from pathlib import Path
   from nodes.prd_validator_node import PRDValidatorNode
   from nodes.models import PRDValidationResult, SectionAnalysis
   from configurations.llm_config import OpenAILLMConfig
   import tempfile
   import os

   class TestReportGeneration:
       """Test report generation functionality."""

       @pytest.fixture
       def validator(self):
           """Create a validator instance for testing."""
           config = OpenAILLMConfig(
               model_name="gpt-4",
               openai_api_key="test-key"
           )
           return PRDValidatorNode(llm_config=config)

       @pytest.fixture
       def sample_validation_result(self):
           """Create a sample validation result for testing."""
           return PRDValidationResult(
               overall_score=7,
               section_analysis=[
                   SectionAnalysis(
                       section_name="Executive Summary",
                       status="present",
                       content_quality="Well-written",
                       word_count=50,
                       bullet_count=0,
                       suggestions=[],
                       required=True
                   ),
                   SectionAnalysis(
                       section_name="Risks & Mitigations",
                       status="missing",
                       content_quality=None,
                       word_count=0,
                       bullet_count=0,
                       suggestions=["Add this section"],
                       required=True
                   )
               ],
               recommendations=[
                   "Add missing sections",
                   "Expand underdeveloped sections"
               ],
               missing_sections=["Risks & Mitigations"],
               underdeveloped_sections=[],
               present_sections=["Executive Summary"],
               total_sections=10,
               coherence_score=1.0
           )

       def test_generate_markdown_report_creates_file(self, validator, sample_validation_result):
           """Test that markdown report file is created."""
           with tempfile.TemporaryDirectory() as tmpdir:
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test PRD\n\n## Executive Summary\nTest content")

               report_path = validator._generate_markdown_report(
                   sample_validation_result,
                   str(prd_path)
               )

               assert report_path is not None
               assert Path(report_path).exists()
               assert Path(report_path).name == "prd_review.md"

       def test_markdown_report_contains_required_sections(self, validator, sample_validation_result):
           """Test that markdown report contains all required sections."""
           with tempfile.TemporaryDirectory() as tmpdir:
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test PRD")

               report_path = validator._generate_markdown_report(
                   sample_validation_result,
                   str(prd_path)
               )

               content = Path(report_path).read_text()
               assert "# PRD Validation Report" in content
               assert "## Executive Summary" in content
               assert "## Section-by-Section Analysis" in content
               assert "## Recommendations by Priority" in content
               assert "## Next Steps" in content

       def test_markdown_report_includes_score(self, validator, sample_validation_result):
           """Test that markdown report includes the score."""
           with tempfile.TemporaryDirectory() as tmpdir:
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test PRD")

               report_path = validator._generate_markdown_report(
                   sample_validation_result,
                   str(prd_path)
               )

               content = Path(report_path).read_text()
               assert "7/10" in content
               assert "Score" in content

       def test_console_output_format(self, validator, sample_validation_result, capsys):
           """Test that console output is formatted correctly."""
           # Mock the console output method
           validator._print_console_report(sample_validation_result, "test_prd.md")

           # In a real test, you'd capture and verify Rich output
           # For now, we just ensure it doesn't crash
           assert True  # Placeholder

       def test_report_overwrites_existing(self, validator, sample_validation_result):
           """Test that existing report is overwritten."""
           with tempfile.TemporaryDirectory() as tmpdir:
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test PRD")

               # Create existing report
               report_path = Path(tmpdir) / "prd_review.md"
               report_path.write_text("Old content")

               # Generate new report
               new_report_path = validator._generate_markdown_report(
                   sample_validation_result,
                   str(prd_path)
               )

               content = Path(new_report_path).read_text()
               assert "Old content" not in content
               assert "# PRD Validation Report" in content
   ```

**Files Created**:
- `tests/test_report_generation.py` (~100 lines)

**Validation**:
- [ ] Report file created in correct location
- [ ] Report contains all required sections
- [ ] Score included in report
- [ ] Existing report overwritten
- [ ] File write errors handled

**Notes**:
- Use tempfile for isolated testing
- Test report structure matches spec.md FR-004
- Verify file operations handle errors

---

### T025: Write Contract Tests for CLI Interface

**Purpose**: Test CLI argument parsing and behavior per the CLI contract.

**Implementation Steps**:

1. **Create test file**: `tests/contract/test_prd_validator_contract.py`

2. **Write contract tests**:
   ```python
   import pytest
   import subprocess
   import sys
   from pathlib import Path

   class TestPRDValidatorCLIContract:
       """Test CLI interface contracts."""

       def test_cli_accepts_prd_path_argument(self):
           """Test that CLI accepts PRD path argument."""
           result = subprocess.run(
               [sys.executable, "main.py", "--help"],
               capture_output=True,
               text=True
           )

           assert "--check-prd" in result.stdout
           assert "PATH" in result.stdout

       def test_cli_accepts_output_format_argument(self):
           """Test that CLI accepts output format option."""
           result = subprocess.run(
               [sys.executable, "main.py", "--help"],
               capture_output=True,
               text=True
           )

           assert "--output-format" in result.stdout
           assert "console" in result.stdout
           assert "file" in result.stdout
           assert "both" in result.stdout

       def test_cli_accepts_min_score_argument(self):
           """Test that CLI accepts min score option."""
           result = subprocess.run(
               [sys.executable, "main.py", "--help"],
               capture_output=True,
               text=True
           )

           assert "--min-score" in result.stdout
           assert "0-10" in result.stdout

       def test_cli_rejects_invalid_output_format(self):
           """Test that CLI rejects invalid output format."""
           # This would be tested by actually running the CLI
           # For now, we verify the argument parser limits choices
           # (Implementation would test with subprocess.run)
           pass

       def test_exit_code_zero_on_success(self):
           """Test exit code 0 on successful validation."""
           prd_path = Path("tests/fixtures/prd_samples/complete_prd.md")
           if not prd_path.exists():
               pytest.skip("Test fixture not found")

           # Note: This test would require mocking the LLM
           # or using a test-specific LLM config
           pass

       def test_exit_code_one_on_file_not_found(self):
           """Test exit code 1 when file not found."""
           result = subprocess.run(
               [sys.executable, "main.py", "--check-prd", "nonexistent.md"],
               capture_output=True,
               text=True
           )

           assert result.returncode == 1
           assert "not found" in result.stderr.lower()

       def test_cli_preserves_existing_functionality(self):
           """Test that existing debate workflow still works."""
           result = subprocess.run(
               [sys.executable, "main.py", "--help"],
               capture_output=True,
               text=True
           )

           # Verify existing arguments still present
           assert "--debate-mode" in result.stdout or result.returncode == 0

       # Add more contract tests as needed
   ```

**Files Created**:
- `tests/contract/test_prd_validator_contract.py` (~80 lines)

**Validation**:
- [ ] CLI arguments documented in help
- [ ] Invalid arguments rejected
- [ ] Exit codes match contract
- [ ] File not found returns exit code 1
- [ ] Existing functionality preserved

**Notes**:
- Contract tests verify interface, not internals
- Test actual CLI via subprocess.run
- Verify exit codes per CLI contract

---

### T026: Write Integration Test for Full Validation Flow

**Purpose**: Test end-to-end PRD validation with real LLM or comprehensive mocking.

**Implementation Steps**:

1. **Create test file**: `tests/integration/test_prd_validation_flow.py`

2. **Write integration tests**:
   ```python
   import pytest
   from pathlib import Path
   from nodes.prd_validator_node import PRDValidatorNode
   from nodes.models import PRDValidationResult
   from configurations.llm_config import OpenAILLMConfig
   from unittest.mock import Mock, patch

   class TestPRDValidationFlow:
       """Test end-to-end PRD validation flow."""

       @pytest.fixture
       def validator(self):
           """Create a validator instance for testing."""
           config = OpenAILLMConfig(
               model_name="gpt-4",
               openai_api_key="test-key"
           )
           return PRDValidatorNode(llm_config=config)

       @pytest.fixture
       def mock_llm_response(self):
           """Mock LLM response for testing."""
           from nodes.prd_validator_node import LLMAssessmentResult
           return LLMAssessmentResult(
               coherence_score=1.5,
               section_assessments=[
                   {
                       "section_name": "Executive Summary",
                       "status": "present",
                       "content_quality": "Good overview",
                       "suggestions": ["Add more metrics"]
                   }
               ],
               recommendations=[
                   "Add missing sections",
                   "Expand content"
               ]
           )

       def test_full_validation_flow_complete_prd(self, validator, mock_llm_response):
           """Test complete validation flow with a complete PRD."""
           prd_path = "tests/fixtures/prd_samples/complete_prd.md"

           if not Path(prd_path).exists():
               pytest.skip("Test fixture not found")

           # Mock the LLM chain to return consistent results
           with patch.object(validator, 'execute_chain', return_value=mock_llm_response):
               result = validator.validate_prd(
                   prd_path=prd_path,
                   output_format="console"
               )

               # Verify result structure
               assert "validation_result" in result
               assert "report_file_path" in result
               assert "prompt_tokens" in result
               assert "completion_tokens" in result

               # Verify validation result
               validation_result = result["validation_result"]
               assert isinstance(validation_result, PRDValidationResult)
               assert 0 <= validation_result.overall_score <= 10
               assert len(validation_result.recommendations) > 0

       def test_full_validation_flow_incomplete_prd(self, validator, mock_llm_response):
           """Test validation flow with an incomplete PRD."""
           prd_path = "tests/fixtures/prd_samples/incomplete_prd.md"

           if not Path(prd_path).exists():
               pytest.skip("Test fixture not found")

           with patch.object(validator, 'execute_chain', return_value=mock_llm_response):
               result = validator.validate_prd(
                   prd_path=prd_path,
                   output_format="file"
               )

               validation_result = result["validation_result"]
               assert len(validation_result.missing_sections) > 0
               assert validation_result.overall_score < 7

       def test_full_validation_flow_empty_prd(self, validator):
           """Test validation flow with an empty PRD."""
           prd_path = "tests/fixtures/prd_samples/empty_prd.md"

           if not Path(prd_path).exists():
               pytest.skip("Test fixture not found")

           result = validator.validate_prd(
               prd_path=prd_path,
               output_format="console"
           )

           validation_result = result["validation_result"]
           assert validation_result.overall_score == 0
           assert len(validation_result.present_sections) == 0

       def test_validation_with_file_output(self, validator, mock_llm_response):
           """Test that file output is generated correctly."""
           import tempfile

           with tempfile.TemporaryDirectory() as tmpdir:
               # Create test PRD
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test\n\n## Executive Summary\nTest content")

               with patch.object(validator, 'execute_chain', return_value=mock_llm_response):
                   result = validator.validate_prd(
                       prd_path=str(prd_path),
                       output_format="file"
                   )

                   # Verify report file created
                   report_path = result.get("report_file_path")
                   assert report_path is not None
                   assert Path(report_path).exists()

                   # Verify report content
                   content = Path(report_path).read_text()
                   assert "# PRD Validation Report" in content

       def test_validation_with_console_output(self, validator, mock_llm_response):
           """Test that console output works."""
           prd_path = "tests/fixtures/prd_samples/complete_prd.md"

           if not Path(prd_path).exists():
               pytest.skip("Test fixture not found")

           # Mock console output to verify it's called
           with patch.object(validator, '_print_console_report') as mock_console:
               with patch.object(validator, 'execute_chain', return_value=mock_llm_response):
                   result = validator.validate_prd(
                       prd_path=prd_path,
                       output_format="console"
                   )

                   # Verify console output was called
                   mock_console.assert_called_once()

       def test_validation_with_both_outputs(self, validator, mock_llm_response):
           """Test that both console and file outputs are generated."""
           import tempfile

           with tempfile.TemporaryDirectory() as tmpdir:
               prd_path = Path(tmpdir) / "test_prd.md"
               prd_path.write_text("# Test\n\n## Executive Summary\nTest content")

               with patch.object(validator, '_print_console_report') as mock_console:
                   with patch.object(validator, 'execute_chain', return_value=mock_llm_response):
                       result = validator.validate_prd(
                           prd_path=str(prd_path),
                           output_format="both"
                       )

                       # Verify both outputs were generated
                       mock_console.assert_called_once()
                       assert result.get("report_file_path") is not None
   ```

**Files Created**:
- `tests/integration/test_prd_validation_flow.py` (~150 lines)

**Validation**:
- [ ] Full flow works with complete PRD
- [ ] Full flow works with incomplete PRD
- [ ] Empty PRD handled correctly
- [ ] File output generated
- [ ] Console output generated
- [ ] Both outputs work together
- [ ] Result structure correct

**Notes**:
- Use mocking for LLM to avoid API calls
- Test with real fixture files
- Verify end-to-end data flow
- Test all output format combinations

---

## Implementation Notes

**Order of Implementation**:
1. T021 first (fixtures - needed by all tests)
2. T022 second (parser tests - independent)
3. T023 third (scoring tests - independent)
4. T024 fourth (report tests - can parallel with T022/T023)
5. T025 fifth (contract tests - independent)
6. T026 last (integration tests - needs all components)

**Parallel Opportunities**:
- T022, T023, T024, T025 can be developed in parallel
- Each test file is independent
- T026 must come last (integration)

**Testing Strategy**:
- Unit tests for individual components
- Contract tests for CLI interface
- Integration tests for full flow
- Mock LLM responses for consistency
- Use fixtures for test data

## Definition of Done

- [ ] All 6 subtasks completed
- [ ] Test fixtures created with sample PRDs
- [ ] Unit tests for parser pass
- [ ] Unit tests for scoring pass
- [ ] Unit tests for report generation pass
- [ ] Contract tests for CLI pass
- [ ] Integration tests pass
- [ ] Test coverage >80% for new code
- [ ] All tests can be run with `pytest`

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM mocking complexity | Medium | Medium | Use patch.object for consistent mocking |
| Test fixture maintenance | Low | Low | Keep fixtures simple and documented |
| Integration test flakiness | Low | Medium | Use tempfile for isolated testing |

## Reviewer Guidance

**What to Verify**:
1. All test files created in correct locations
2. Tests cover all components from WP01-WP04
3. Edge cases from spec.md are tested
4. Mocking strategy is appropriate
5. Tests follow existing test patterns
6. Fixtures are realistic and well-documented

**Common Issues to Check**:
- Missing test for empty PRD
- LLM not mocked (causes API calls in tests)
- Test fixtures don't exist
- Tests not following pytest conventions
- Integration tests missing

**Testing Checklist**:
- [ ] `pytest tests/test_markdown_parser.py` passes
- [ ] `pytest tests/test_scoring.py` passes
- [ ] `pytest tests/test_report_generation.py` passes
- [ ] `pytest tests/contract/test_prd_validator_contract.py` passes
- [ ] `pytest tests/integration/test_prd_validation_flow.py` passes
- [ ] All tests pass together: `pytest tests/`
- [ ] Coverage >80% for new code

## Next Steps

After completing this work package:
1. Run `spec-kitty review WP05` to mark as ready for review
2. All work packages complete - ready for implementation
3. Implementation command: `spec-kitty implement WP05 --base WP04`

**Feature Complete**: After WP05, the PRD Completeness Validator feature is fully specified and ready for implementation!
