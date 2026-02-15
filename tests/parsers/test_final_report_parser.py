"""Unit tests for FinalReportParser.

Tests parsing of final_report.md files from committee debates.
"""

import unittest
import tempfile
from pathlib import Path

from src.parsers.final_report_parser import FinalReportParser
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


class TestFinalReportParser(unittest.TestCase):
    """Test cases for FinalReportParser."""

    def setUp(self):
        """Set up test parser."""
        self.parser = FinalReportParser()
        self.sample_report = """# Product Committee Report

**Run ID:** RUN_20260214_112438
**Generated:** 2026-02-14T11:26:45.480653+00:00

---

## Committee Question
Should we invest in AI infrastructure for our platform?

---

## Executive Summary
This report synthesizes debate results from 4 committee rooms.

---

## Room-by-Room Analysis

### TPM_vs_CPO
**Status:** success
**Winner:** CON
**Judge Explanation:** CPO demonstrated stronger market understanding.

**Key Takeaways:**
- Market demand is uncertain
- User adoption risks are significant
- Infrastructure costs are high

**Full Dialogue:**
**PRO** (opening) ✓: TPM presents position on AI infrastructure investment
**CON** (rebuttal) ✓: CPO challenges market assumptions

### TPM_vs_CFO
**Status:** success
**Winner:** PRO
**Judge Explanation:** TPM shows clear ROI path.

**Key Takeaways:**
- ROI can be achieved in 18 months
- Cost savings are substantial
- Efficiency gains are proven

---

## TPM Reflection

### Learned Insights
- TPM position strength: Clear ROI model
- TPM position weakness: Overestimated market demand

### Potential Assessment
**Overall:** medium
**Confidence:** 0.7

### Recommendations
1. Validate market demand assumptions
2. Build incremental MVP
3. Defer full infrastructure investment

---

## Metadata
- **PRD:** /path/to/prd.md
- **Roles directory:** /path/to/roles/
- **Model:** gpt-4
- **Start time:** 2026-02-14T11:26:45.480653+00:00
- **End time:** 2026-02-14T11:26:45.480653+00:00
"""

    def test_parse_basic_structure(self):
        """Test that parser can extract basic ConclusionData structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        # Verify ConclusionData structure
        self.assertIsInstance(result, dict)
        self.assertIn('debate_question', result)
        self.assertIn('verdict', result)
        self.assertIn('qa_summary', result)
        self.assertIn('tpm_analysis', result)
        self.assertIn('recommendations', result)
        self.assertIn('metadata', result)

    def test_parse_debate_question(self):
        """Test extraction of Committee Question."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        self.assertEqual(
            result['debate_question'],
            "Should we invest in AI infrastructure for our platform?"
        )

    def test_parse_verdict(self):
        """Test extraction of verdict information."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        verdict = result['verdict']
        self.assertEqual(verdict['winner'], 'CON')
        self.assertEqual(verdict['winner_position'], 'CON')
        self.assertIn('CPO demonstrated', verdict['justification'])

    def test_determine_position(self):
        """Test role to position mapping."""
        self.assertEqual(self.parser._determine_position('TPM'), 'PRO')
        self.assertEqual(self.parser._determine_position('BDM'), 'PRO')
        self.assertEqual(self.parser._determine_position('PRO'), 'PRO')
        self.assertEqual(self.parser._determine_position('CON'), 'CON')
        self.assertEqual(self.parser._determine_position('CPO'), 'CON')
        self.assertEqual(self.parser._determine_position('CFO'), 'CON')
        self.assertEqual(self.parser._determine_position('CTO'), 'CON')

    def test_parse_qa_summary(self):
        """Test extraction of Q&A summary."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        qa_summary = result['qa_summary']
        self.assertIsInstance(qa_summary, list)
        self.assertGreaterEqual(len(qa_summary), 0)

        # Check first Q&A pair structure
        if qa_summary:
            first_qa = qa_summary[0]
            self.assertIn('question', first_qa)
            self.assertIn('answer', first_qa)
            self.assertIn('stage', first_qa)
            self.assertIn('speaker', first_qa)
            self.assertIn('validated', first_qa)
            self.assertIn('priority', first_qa)

    def test_parse_tpm_analysis(self):
        """Test extraction of TPM analysis."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        tpm_analysis = result['tpm_analysis']
        self.assertIn('position_summary', tpm_analysis)
        self.assertIn('weaknesses', tpm_analysis)
        self.assertIn('recommended_improvements', tpm_analysis)
        self.assertIn('victory_assessment', tpm_analysis)

    def test_parse_recommendations(self):
        """Test extraction of recommendations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        recommendations = result['recommendations']
        self.assertIsInstance(recommendations, list)

        # Check recommendation structure
        if recommendations:
            first_rec = recommendations[0]
            self.assertIn('agent_role', first_rec)
            self.assertIn('text', first_rec)
            self.assertIn('actionable', first_rec)

    def test_parse_metadata(self):
        """Test extraction of metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            f.flush()

            result = self.parser.parse(f.name)

        metadata = result['metadata']
        self.assertEqual(metadata['debate_type'], DebateType.COMMITTEE.value)
        self.assertEqual(metadata['run_id'], 'RUN_20260214_112438')
        self.assertIn('generated_at', metadata)
        self.assertIn('completion_status', metadata)
        self.assertEqual(metadata['completion_status'], 'success')

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse('/nonexistent/path/to/report.md')

    def test_extract_sections(self):
        """Test section extraction from markdown content."""
        content = """
## Section One
Content of section one.

## Section Two
Content of section two.

## Section Three
Content of section three.
"""

        sections = self.parser._extract_sections(content)

        self.assertEqual(len(sections), 3)
        self.assertIn('Section One', sections)
        self.assertIn('Section Two', sections)
        self.assertIn('Section Three', sections)
        self.assertEqual(sections['Section One'].strip(), 'Content of section one.')

    def test_extract_subsection(self):
        """Test subsection extraction."""
        content = """
Some leading content.

### Subsection Title
Subsection content here.

### Another Subsection
Other content here.
"""

        result = self.parser._extract_subsection(content, 'Subsection Title')

        self.assertEqual(result.strip(), 'Subsection content here.')

    def test_empty_report_handling(self):
        """Test handling of report with missing critical sections."""
        empty_report = """# Empty Report

No content here.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(empty_report)
            f.flush()

            with self.assertRaises(ValueError):
                self.parser.parse(f.name)


class TestFinalReportParserEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test parser."""
        self.parser = FinalReportParser()

    def test_missing_committee_question(self):
        """Test error when Committee Question section is missing."""
        report_without_question = """# Report

## Room-by-Room Analysis
No room data.

"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(report_without_question)
            f.flush()

            with self.assertRaises(ValueError) as cm:
                self.parser.parse(f.name)
            self.assertIn('Committee Question', str(cm.exception))

    def test_malformed_room_result(self):
        """Test handling of malformed room result section."""
        malformed_report = """# Report

## Committee Question
Test question?

## Room-by-Room Analysis
Malformed content without proper structure.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(malformed_report)
            f.flush()

            # Should not crash, but handle gracefully
            result = self.parser.parse(f.name)
            self.assertIsNotNone(result)

    def test_unicode_content(self):
        """Test handling of Unicode content in report."""
        unicode_report = """# Report

## Committee Question
Should we invest in AI? Тестовый текст.

## Executive Summary
Summary with émojis 🎉 and spëcial çharacters.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                      encoding='utf-8') as f:
            f.write(unicode_report)
            f.flush()

            result = self.parser.parse(f.name)
            self.assertIsNotNone(result)
            self.assertIn('Тестовый текст', result['debate_question'])


if __name__ == '__main__':
    unittest.main()
