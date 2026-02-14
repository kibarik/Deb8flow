"""
Unit tests for Product Committee Orchestrator (WP06).

Tests cover:
- T031: CLI argument parsing (all flags)
- T032: Subprocess wrapper and retry logic
- T033: Room execution and status handling
- T034: Metadata generation
- T035: Reflection integration
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from product_committee import (
    DebateRoom,
    create_debate_room,
    parse_arguments,
    validate_arguments,
    read_prd_text,
    setup_logging,
    parse_debate_output,
    run_debate_room_with_retry,
    validate_role_prompts,
    generate_run_id,
    create_metadata,
    run_all_rooms,
    generate_reflection_prompt,
    generate_final_report,
    DEFAULT_MAX_RETRIES,
    ROOM_ORDER
)


class TestCLIArgumentParsing(unittest.TestCase):
    """T031: Test CLI argument parsing (all flags)."""

    def test_required_arguments_present(self):
        """Test that --prd and --question are required."""
        with patch('sys.argv', ['product_committee.py']):
            with self.assertRaises(SystemExit) as ctx:
                parse_arguments()
            self.assertEqual(ctx.exception.code, 2)

    def test_all_optional_flags_have_defaults(self):
        """Test that optional flags have correct defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prd_file:
            prd_file.write("Test PRD content that is long enough")

        with tempfile.TemporaryDirectory() as roles_dir:
            # Create required TPM prompt
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            try:
                with patch('sys.argv', [
                    'product_committee.py',
                    '--prd', prd_file.name,
                    '--question', 'What is the potential?'
                ]):
                    args = parse_arguments()

                self.assertEqual(args.max_retries, DEFAULT_MAX_RETRIES)
                self.assertEqual(args.output_dir, './committee_output')
                self.assertEqual(args.roles_dir, 'prompts/roles/')
                self.assertIsNone(args.model)
                self.assertIsNone(args.run_id)
                self.assertFalse(args.allow_short_prd)
                self.assertFalse(args.verbose)
                self.assertFalse(args.quiet)
            finally:
                os.unlink(prd_file.name)

    def test_verbose_and_quiet_mutually_exclusive(self):
        """Test that --verbose and --quiet cannot be used together."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prd_file:
            prd_file.write("Test PRD content that is long enough")

        with tempfile.TemporaryDirectory() as roles_dir:
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            try:
                with patch('sys.argv', [
                    'product_committee.py',
                    '--prd', prd_file.name,
                    '--question', 'What is the potential?',
                    '--verbose',
                    '--quiet'
                ]):
                    with self.assertRaises(SystemExit) as ctx:
                        parse_arguments()
                    self.assertEqual(ctx.exception.code, 1)
            finally:
                os.unlink(prd_file.name)

    def test_negative_max_retries_rejected(self):
        """Test that negative --max-retries is rejected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prd_file:
            prd_file.write("Test PRD content that is long enough")

        with tempfile.TemporaryDirectory() as roles_dir:
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            try:
                with patch('sys.argv', [
                    'product_committee.py',
                    '--prd', prd_file.name,
                    '--question', 'What is the potential?',
                    '--max-retries', '-1'
                ]):
                    with self.assertRaises(SystemExit) as ctx:
                        parse_arguments()
                    self.assertEqual(ctx.exception.code, 1)
            finally:
                os.unlink(prd_file.name)


class TestSubprocessWrapper(unittest.TestCase):
    """T032: Test subprocess wrapper and retry logic."""

    def test_parse_debate_output_extracts_winner(self):
        """Test that output parser correctly extracts winner."""
        stdout = "Some debate content\nWINNER: PRO\nMore content"
        result = parse_debate_output(stdout, "")
        self.assertEqual(result["judge_verdict"]["winner"], "TPM")

    def test_parse_debate_output_handles_con_winner(self):
        """Test that CON winner is parsed correctly."""
        stdout = "Some debate content\nWINNER: CON\nMore content"
        result = parse_debate_output(stdout, "")
        self.assertEqual(result["judge_verdict"]["winner"], "CON")

    def test_parse_debate_output_extracts_takeaways(self):
        """Test that takeaways are extracted from output."""
        stdout = """
        Some debate content
        WINNER: PRO
        The project should be recommended
        We suggest investing more resources
        """
        result = parse_debate_output(stdout, "")
        self.assertGreater(len(result["takeaways"]), 0)

    def test_debate_room_creation(self):
        """Test DebateRoom dataclass creation."""
        room = create_debate_room("TPM_vs_CPO", "CPO")
        self.assertEqual(room.room_id, "TPM_vs_CPO")
        self.assertEqual(room.status, "failed")
        self.assertIsInstance(room.timestamp, str)

    def test_debate_room_to_json(self):
        """Test DebateRoom JSON serialization."""
        room = create_debate_room("TPM_vs_CPO", "CPO")
        room.status = "success"
        room.tpm_position = "TPM position"
        room.opponent_position = "CPO position"
        room.judge_verdict = {"winner": "TPM", "explanation": "Test"}
        room.takeaways = ["Takeaway 1", "Takeaway 2"]

        json_str = room.to_json()
        parsed = json.loads(json_str)

        self.assertEqual(parsed["room_id"], "TPM_vs_CPO")
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(len(parsed["takeaways"]), 2)


class TestRoomExecution(unittest.TestCase):
    """T033: Test room execution and status handling."""

    def test_validate_role_prompts_fails_without_tpm(self):
        """Test that missing TPM prompt causes exit."""
        with tempfile.TemporaryDirectory() as roles_dir:
            with self.assertRaises(SystemExit) as ctx:
                validate_role_prompts(Path(roles_dir))
            self.assertEqual(ctx.exception.code, 1)

    def test_validate_role_prompts_succeeds_with_tpm(self):
        """Test that TPM prompt validation succeeds."""
        with tempfile.TemporaryDirectory() as roles_dir:
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            role_files = validate_role_prompts(Path(roles_dir))
            self.assertIsNotNone(role_files["tpm"])
            self.assertEqual(role_files["tpm"], tpm_path)

    def test_validate_role_prompts_handles_missing_optional_roles(self):
        """Test that missing optional roles return None."""
        with tempfile.TemporaryDirectory() as roles_dir:
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            role_files = validate_role_prompts(Path(roles_dir))
            self.assertIsNone(role_files["cpo"])
            self.assertIsNone(role_files["cfo"])
            self.assertIsNone(role_files["cto"])
            self.assertIsNone(role_files["bdm"])

    @patch('product_committee.run_debate_room_with_retry')
    def test_run_all_rooms_executes_in_order(self, mock_run_room):
        """Test that rooms execute in correct order."""
        mock_run_room.return_value = create_debate_room("TPM_vs_CPO", "CPO")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prd_file:
            prd_file.write("Test PRD content")

        with tempfile.TemporaryDirectory() as roles_dir:
            tpm_path = Path(roles_dir) / "tpm.txt"
            tpm_path.write_text("TPM prompt content")

            try:
                role_files = validate_role_prompts(Path(roles_dir))
                metadata = create_metadata(
                    run_id="TEST_RUN",
                    prd_path=prd_file.name,
                    question="Test question",
                    model=None,
                    roles_dir=roles_dir,
                    output_dir="./output",
                    max_retries=2
                )

                rooms = run_all_rooms(
                    prd_path=Path(prd_file.name),
                    question="Test question",
                    role_files=role_files,
                    model=None,
                    max_retries=2,
                    verbose=False,
                    metadata=metadata
                )

                # Check that rooms were called in correct order
                call_args_list = [call[1]['room_id'] for call in mock_run_room.call_args_list]
                expected_order = [f"TPM_vs_{role.upper()}" for role in ROOM_ORDER if role_files[role]]
                self.assertEqual(call_args_list, expected_order)
            finally:
                os.unlink(prd_file.name)


class TestMetadataGeneration(unittest.TestCase):
    """T034: Test metadata generation."""

    def test_metadata_structure(self):
        """Test that metadata has all required fields."""
        metadata = create_metadata(
            run_id="TEST_RUN",
            prd_path="/path/to/prd.txt",
            question="Test question?",
            model="gpt-4",
            roles_dir="prompts/roles/",
            output_dir="./output",
            max_retries=3
        )

        self.assertEqual(metadata["run_id"], "TEST_RUN")
        self.assertEqual(metadata["prd_path"], "/path/to/prd.txt")
        self.assertEqual(metadata["question"], "Test question?")
        self.assertEqual(metadata["model"], "gpt-4")
        self.assertEqual(metadata["max_retries"], 3)
        self.assertIsInstance(metadata["start_time"], str)
        self.assertIsNone(metadata["end_time"])
        self.assertIsInstance(metadata["room_statuses"], dict)
        self.assertIsInstance(metadata["warning_flags"], dict)
        self.assertIsInstance(metadata["errors"], list)

    def test_run_id_generation_from_question(self):
        """Test automatic run ID generation."""
        question = "What is the potential of this AI project?"
        run_id = generate_run_id(question)

        self.assertTrue(run_id.startswith("RUN_"))
        self.assertIn("_", run_id)
        # Slug includes words from question
        self.assertIn("potential", run_id.lower())

    def test_manual_run_id_is_preserved(self):
        """Test that manual run ID is used as-is."""
        manual_id = "CUSTOM_RUN_123"
        run_id = generate_run_id("Any question?", manual_id)
        self.assertEqual(run_id, manual_id)


class TestReflectionIntegration(unittest.TestCase):
    """T035: Test reflection integration."""

    def test_reflection_prompt_includes_question(self):
        """Test that reflection prompt includes committee question."""
        prompt = generate_reflection_prompt(
            prd_text="PRD content",
            question="What is the potential?",
            successful_rooms=[]
        )

        self.assertIn("What is the potential?", prompt)

    def test_reflection_prompt_includes_room_results(self):
        """Test that reflection prompt includes room results."""
        room1 = create_debate_room("TPM_vs_CPO", "CPO")
        room1.status = "success"
        room1.judge_verdict = {"winner": "TPM", "explanation": "Test verdict"}
        room1.takeaways = ["Takeaway 1", "Takeaway 2"]

        prompt = generate_reflection_prompt(
            prd_text="PRD content",
            question="Test question",
            successful_rooms=[room1]
        )

        self.assertIn("TPM_vs_CPO", prompt)
        self.assertIn("TPM", prompt)  # Winner

    def test_reflection_handles_zero_successful_rooms(self):
        """Test that reflection handles empty room list."""
        prompt = generate_reflection_prompt(
            prd_text="PRD content",
            question="Test question",
            successful_rooms=[]
        )

        self.assertIn("0 successful", prompt)


class TestReportGeneration(unittest.TestCase):
    """Test report generation and formatting."""

    def test_report_includes_executive_summary(self):
        """Test that report includes executive summary."""
        rooms = []
        reflection = None
        metadata = {
            "run_id": "TEST_RUN",
            "end_time": datetime.utcnow().isoformat(),
            "prd_path": "/path/to/prd.txt",
            "roles_dir": "prompts/roles/",
            "model": "default",
            "max_retries": 2,
            "start_time": datetime.utcnow().isoformat()
        }

        report = generate_final_report(
            run_id="TEST_RUN",
            prd_path="/path/to/prd.txt",
            question="Test question",
            rooms=rooms,
            reflection=reflection,
            metadata=metadata
        )

        self.assertIn("# Product Committee Report", report)
        self.assertIn("Executive Summary", report)
        self.assertIn("**Successful rooms:** 0", report)

    def test_report_includes_room_results(self):
        """Test that report includes room summaries."""
        room1 = create_debate_room("TPM_vs_CPO", "CPO")
        room1.status = "success"
        room1.judge_verdict = {"winner": "TPM", "explanation": "TPM prevailed"}
        room1.takeaways = ["Key insight 1", "Key insight 2"]

        reflection = None
        metadata = {
            "run_id": "TEST_RUN",
            "end_time": datetime.utcnow().isoformat(),
            "prd_path": "/path/to/prd.txt",
            "roles_dir": "prompts/roles/",
            "model": "default",
            "max_retries": 2,
            "start_time": datetime.utcnow().isoformat()
        }

        report = generate_final_report(
            run_id="TEST_RUN",
            prd_path="/path/to/prd.txt",
            question="Test question",
            rooms=[room1],
            reflection=reflection,
            metadata=metadata
        )

        self.assertIn("TPM_vs_CPO", report)
        self.assertIn("TPM prevailed", report)
        self.assertIn("Key insight 1", report)

    def test_report_includes_reflection(self):
        """Test that report includes reflection data."""
        rooms = []
        reflection = {
            "learned_insights": ["Insight 1", "Insight 2"],
            "potential_assessment": {"overall": "high", "confidence": 0.8},
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }
        metadata = {
            "run_id": "TEST_RUN",
            "end_time": datetime.utcnow().isoformat(),
            "prd_path": "/path/to/prd.txt",
            "roles_dir": "prompts/roles/",
            "model": "default",
            "max_retries": 2,
            "start_time": datetime.utcnow().isoformat()
        }

        report = generate_final_report(
            run_id="TEST_RUN",
            prd_path="/path/to/prd.txt",
            question="Test question",
            rooms=rooms,
            reflection=reflection,
            metadata=metadata
        )

        self.assertIn("TPM Reflection", report)
        self.assertIn("Insight 1", report)
        self.assertIn("high", report)
        self.assertIn("Recommendation 1", report)


if __name__ == '__main__':
    unittest.main()
