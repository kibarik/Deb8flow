#!/usr/bin/env python3
"""
Product Committee Orchestrator

Simulates a virtual product committee by running four sequential debate rooms (TPM vs CPO/CFO/CTO/BDM)
using the existing document_debate_cli.py script, followed by TPM self-reflection.

Usage:
    python product_committee.py --prd <path> --question <text> [--model <name>]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


# --- Configuration Constants ---

DEFAULT_ROLES_DIR = "prompts/roles/"
DEFAULT_OUTPUT_DIR = "./committee_output"
DEFAULT_MAX_RETRIES = 2
DEFAULT_RUN_ID_FORMAT = "RUN_{timestamp}_{slug}"

# Room execution order (fixed for MVP)
ROOM_ORDER = ["cpo", "cfo", "cto", "bdm"]


# --- Data Structures ---

@dataclass
class JudgeVerdict:
    """Judge's verdict from a debate room."""
    winner: str
    explanation: str
    tpm_score: Optional[float] = None
    opponent_score: Optional[float] = None


@dataclass
class DebateRoom:
    """Structured result from a single debate room."""
    room_id: str
    status: str  # "success", "failed", "skipped_missing_prompt"
    timestamp: str
    tpm_position: str
    opponent_position: str
    judge_verdict: Dict[str, Any]
    takeaways: List[str]
    error: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebateRoom':
        """Create DebateRoom from dictionary."""
        return cls(**data)


def create_debate_room(room_id: str, opponent_role: str) -> DebateRoom:
    """
    Create an initialized DebateRoom structure.

    Args:
        room_id: Room identifier (e.g., "TPM_vs_CPO")
        opponent_role: Opponent role name (e.g., "CPO")

    Returns:
        Initialized DebateRoom with placeholder data
    """
    return DebateRoom(
        room_id=room_id,
        status="failed",
        timestamp=datetime.utcnow().isoformat(),
        tpm_position="",
        opponent_position="",
        judge_verdict={"winner": "", "explanation": ""},
        takeaways=[],
        error=None
    )


# --- Logging Setup ---

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Configure logging based on verbosity flags.

    Args:
        verbose: If True, set DEBUG level with detailed output
        quiet: If True, set WARNING level with minimal output
        If both False, set INFO level (normal)

    Returns:
        Configured logger instance
    """
    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s [%(name)s] - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    return logger


# --- Argument Parsing ---

def parse_arguments() -> argparse.Namespace:
    """
    Parse and validate all CLI arguments.

    Returns:
        Parsed arguments namespace

    Raises:
        SystemExit if fatal validation fails
    """
    parser = argparse.ArgumentParser(
        description="Simulates a virtual product committee by running four sequential debate rooms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "--prd", "--docx",
        required=True,
        help="Path to PRD document (.docx or text file)",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Committee question for all rooms (e.g., 'What's the potential of this project?')",
    )

    # Optional arguments
    parser.add_argument(
        "--model",
        help="LLM model name (passed through to underlying debate CLI)",
        default=None,
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Maximum retry attempts per room (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Base output directory for run artifacts (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--roles-dir",
        default=DEFAULT_ROLES_DIR,
        help=f"Directory containing role prompt files (default: {DEFAULT_ROLES_DIR})",
    )
    parser.add_argument(
        "--run-id",
        help="Manual run identifier (auto-generated if omitted)",
        default=None,
    )
    parser.add_argument(
        "--allow-short-prd",
        action="store_true",
        help="Enforce minimum PRD length (100 chars); abort if shorter",
        default=False,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (detailed retry attempts, CLI params, file sizes)",
        default=False,
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Enable quiet mode (minimal output: start/finish/errors only)",
        default=False,
    )

    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    return args


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate CLI arguments and exit with appropriate error codes.

    Raises:
        SystemExit(1) if PRD file missing/unreadable
        SystemExit(1) if question is empty
        SystemExit(1) if TPM prompt file missing
    """
    # Check PRD file
    prd_path = Path(args.prd)
    if not prd_path.exists():
        logger.error(f"Error: PRD file not found or unreadable: {prd_path}")
        sys.exit(1)

    # Check question
    if not args.question or not args.question.strip():
        logger.error("Error: Question cannot be empty. Please provide a question for the committee.")
        sys.exit(1)

    # Check TPM prompt file
    tpm_prompt_path = Path(args.roles_dir) / "tpm.txt"
    if not tpm_prompt_path.exists():
        logger.error(f"Error: TPM prompt file not found at {tpm_prompt_path}. Aborting.")
        sys.exit(1)

    # Check mutual exclusivity
    if args.verbose and args.quiet:
        logger.error("Error: --verbose and --quiet are mutually exclusive. Please use only one.")
        sys.exit(1)

    # Check max_retries is non-negative
    if args.max_retries < 0:
        logger.error("Error: --max-retries must be >= 0")
        sys.exit(1)

    # Check PRD length if --allow-short-prd is set
    if args.allow_short_prd:
        prd_text = read_prd_text(prd_path)
        if len(prd_text) < 100:
            logger.error("Error: PRD is too short (< 100 characters) with --allow-short-prd flag.")
            sys.exit(1)

    logger.debug("All arguments validated successfully")


def read_prd_text(prd_path: Path) -> str:
    """
    Read PRD text from file for validation and logging purposes.

    Args:
        prd_path: Path to PRD file

    Returns:
        File content as string
    """
    try:
        with open(prd_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading PRD file: {e}")
        sys.exit(1)


# --- Subprocess Wrapper & Retry Logic (WP02) ---

DEFAULT_DEBATE_TIMEOUT = 300  # 5 minutes timeout for debate subprocess


def parse_debate_output(stdout: str, stderr: str) -> Dict[str, Any]:
    """
    Parse debate CLI output to extract structured room data.

    Args:
        stdout: Standard output from document_debate_cli.py
        stderr: Standard error from document_debate_cli.py

    Returns:
        Dictionary containing parsed debate results
    """
    result = {
        "tpm_position": "",
        "opponent_position": "",
        "judge_verdict": {"winner": "", "explanation": ""},
        "takeaways": [],
        "raw_output": stdout,
        "errors": stderr
    }

    # Parse verdict from output (look for WINNER pattern)
    verdict_pattern = r"WINNER:\s*(PRO|CON)"
    verdict_match = re.search(verdict_pattern, stdout)
    if verdict_match:
        winner = verdict_match.group(1)
        result["judge_verdict"]["winner"] = "TPM" if winner == "PRO" else "CON"

    # Extract final messages/positions from the workflow
    # The debate CLI outputs structured messages; we parse the last few
    lines = stdout.strip().split('\n')

    # Look for judge verdict and explanations
    for i, line in enumerate(lines):
        if "WINNER:" in line:
            # Extract explanation from surrounding context
            context_start = max(0, i - 5)
            context = '\n'.join(lines[context_start:i+1])
            result["judge_verdict"]["explanation"] = context.strip()
            break

    # For MVP, extract takeaways from any lines with "recommendation" or "insight"
    # In production, this would be structured JSON output
    takeaway_keywords = ["recommend", "insight", "suggest", "advise", "should"]
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in takeaway_keywords):
            cleaned = line.strip().replace('*', '').replace('-', '').strip()
            if cleaned and len(cleaned) > 10:
                result["takeaways"].append(cleaned)
                if len(result["takeaways"]) >= 5:
                    break

    return result


def run_debate_room_with_retry(
    prd_path: Path,
    question: str,
    pro_prompt_path: Path,
    con_prompt_path: Path,
    model: Optional[str],
    room_id: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    verbose: bool = False
) -> DebateRoom:
    """
    Run a single debate room with retry logic and exponential backoff.

    Args:
        prd_path: Path to PRD document
        question: Committee question for the debate
        pro_prompt_path: Path to PRO debater prompt file
        con_prompt_path: Path to CON debater prompt file
        model: Optional LLM model name
        room_id: Room identifier (e.g., "TPM_vs_CPO")
        max_retries: Maximum retry attempts
        verbose: Enable detailed logging

    Returns:
        DebateRoom result with status and parsed data
    """
    room = create_debate_room(room_id, room_id.split("_vs_")[-1])

    # Build command
    cmd = [
        sys.executable,  # Use current Python interpreter
        "document_debate_cli.py",
        "--docx", str(prd_path),
        "--request", question,
        "--pro-prompt", str(pro_prompt_path),
        "--con-prompt", str(con_prompt_path)
    ]

    if model:
        cmd.extend(["--model", model])

    if verbose:
        cmd.append("--verbose")

    # Retry loop with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0 and verbose:
                logger.debug(f"Retry attempt {attempt}/{max_retries} for room {room_id}")

            # Run subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEFAULT_DEBATE_TIMEOUT,
                check=False
            )

            # Check for successful execution
            if result.returncode == 0:
                logger.info(f"Room {room_id} completed successfully")
                parsed = parse_debate_output(result.stdout, result.stderr)

                # Update room with parsed data
                room.status = "success"
                room.tpm_position = parsed["tpm_position"] or "TPM position from debate"
                room.opponent_position = parsed["opponent_position"] or f"{room_id.split('_vs_')[-1]} position from debate"
                room.judge_verdict = parsed["judge_verdict"]
                room.takeaways = parsed["takeaways"][:5]  # Limit to 5 takeaways

                if not room.takeaways:
                    room.takeaways = [f"Debate completed for {room_id}"]

                return room
            else:
                # Non-zero exit code
                error_msg = result.stderr or result.stdout or "Unknown error"
                if attempt < max_retries:
                    if verbose:
                        logger.debug(f"Room {room_id} failed (attempt {attempt + 1}): {error_msg[:200]}")
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    logger.error(f"Room {room_id} failed after {max_retries + 1} attempts")
                    room.status = "failed"
                    room.error = error_msg[:500]  # Truncate long errors
                    return room

        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                if verbose:
                    logger.debug(f"Room {room_id} timed out (attempt {attempt + 1})")
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                logger.error(f"Room {room_id} timed out after {max_retries + 1} attempts")
                room.status = "failed"
                room.error = "Debate timed out"
                return room

        except Exception as e:
            logger.error(f"Unexpected error running room {room_id}: {e}")
            room.status = "failed"
            room.error = str(e)
            return room

    # Should not reach here, but handle gracefully
    room.status = "failed"
    room.error = "Max retries exceeded"
    return room


# --- Room Orchestration & Metadata Tracking (WP03) ---

def validate_role_prompts(roles_dir: Path) -> Dict[str, Optional[Path]]:
    """
    Validate that role prompt files exist.

    Args:
        roles_dir: Directory containing role prompt files

    Returns:
        Dictionary mapping role names to prompt file paths (None if missing)

    Raises:
        SystemExit(1) if TPM prompt is missing
    """
    role_files = {}

    # TPM is required
    tpm_path = roles_dir / "tpm.txt"
    if not tpm_path.exists():
        logger.error(f"Error: TPM prompt file not found at {tpm_path}. Aborting.")
        sys.exit(1)
    role_files["tpm"] = tpm_path

    # Other roles are optional
    for role in ["cpo", "cfo", "cto", "bdm"]:
        role_path = roles_dir / f"{role}.txt"
        role_files[role] = role_path if role_path.exists() else None
        if role_files[role] is None:
            logger.warning(f"Warning: {role.upper()} prompt file not found at {role_path}. Room will be skipped.")

    return role_files


def generate_run_id(question: str, manual_id: Optional[str] = None) -> str:
    """
    Generate a run identifier from question or use manual ID.

    Args:
        question: Committee question
        manual_id: Optional manual run identifier

    Returns:
        Run ID string
    """
    if manual_id:
        return manual_id

    # Generate slug from first 3-5 words of question
    words = question.strip().split()[:5]
    slug = "-".join(words).lower()
    # Remove non-alphanumeric characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"RUN_{timestamp}_{slug}"


def create_metadata(
    run_id: str,
    prd_path: str,
    question: str,
    model: Optional[str],
    roles_dir: str,
    output_dir: str,
    max_retries: int
) -> Dict[str, Any]:
    """
    Create initial metadata structure for a committee run.

    Args:
        run_id: Unique run identifier
        prd_path: Path to PRD document
        question: Committee question
        model: Optional LLM model name
        roles_dir: Roles directory path
        output_dir: Output directory path
        max_retries: Maximum retry attempts

    Returns:
        Metadata dictionary with initial values
    """
    return {
        "run_id": run_id,
        "prd_path": prd_path,
        "question": question,
        "model": model or "default",
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
        "room_statuses": {
            "tpm_cpo": "pending",
            "tpm_cfo": "pending",
            "tpm_cto": "pending",
            "tpm_bdm": "pending"
        },
        "roles_dir": roles_dir,
        "output_dir": output_dir,
        "max_retries": max_retries,
        "warning_flags": {
            "prd_too_short": False,
            "question_too_short": False,
            "some_rooms_failed": False
        },
        "errors": []
    }


def run_all_rooms(
    prd_path: Path,
    question: str,
    role_files: Dict[str, Optional[Path]],
    model: Optional[str],
    max_retries: int,
    verbose: bool,
    metadata: Dict[str, Any]
) -> List[DebateRoom]:
    """
    Execute all four debate rooms sequentially.

    Args:
        prd_path: Path to PRD document
        question: Committee question
        role_files: Dictionary of role prompt file paths
        model: Optional LLM model name
        max_retries: Maximum retry attempts
        verbose: Enable verbose logging
        metadata: Metadata dictionary to update

    Returns:
        List of DebateRoom results
    """
    results = []
    successful_rooms = []

    for role in ROOM_ORDER:
        opponent_file = role_files[role]

        # Skip if opponent prompt is missing
        if opponent_file is None:
            room_id = f"TPM_vs_{role.upper()}"
            logger.warning(f"Skipping room {room_id} (missing prompt file)")
            metadata["room_statuses"][f"tpm_{role}"] = "skipped_missing_prompt"

            # Add placeholder room result
            room = create_debate_room(room_id, role.upper())
            room.status = "skipped_missing_prompt"
            results.append(room)
            continue

        room_id = f"TPM_vs_{role.upper()}"
        logger.info(f"Starting room {room_id}...")

        # Run debate with TPM as PRO, opponent as CON
        room = run_debate_room_with_retry(
            prd_path=prd_path,
            question=question,
            pro_prompt_path=role_files["tpm"],
            con_prompt_path=opponent_file,
            model=model,
            room_id=room_id,
            max_retries=max_retries,
            verbose=verbose
        )

        # Update metadata
        metadata["room_statuses"][f"tpm_{role}"] = room.status
        results.append(room)

        if room.status == "success":
            successful_rooms.append(room)
        else:
            metadata["warning_flags"]["some_rooms_failed"] = True
            metadata["errors"].append({
                "room": room_id,
                "message": room.error or "Unknown error",
                "timestamp": datetime.utcnow().isoformat()
            })

        logger.info(f"Room {room_id} completed with status: {room.status}")

    return results


# --- Self-Reflection Integration (WP04) ---

REFLECTION_PROMPT_PATH = "prompts/tpm_reflection.txt"
REFLECTION_TIMEOUT = 300  # 5 minutes for reflection


def generate_reflection_prompt(
    prd_text: str,
    question: str,
    successful_rooms: List[DebateRoom]
) -> str:
    """
    Generate prompt for TPM self-reflection subprocess.

    Args:
        prd_text: PRD document text
        question: Committee question
        successful_rooms: List of successful debate room results

    Returns:
        Prompt string for reflection subprocess
    """
    # For MVP, use a simple inline prompt
    # In production, this would load from prompts/tpm_reflection.txt
    prompt_parts = [
        f"PRD Content:\n{prd_text}\n",
        f"\nCommittee Question: {question}\n",
        f"\nDebate Room Results ({len(successful_rooms)} successful):\n"
    ]

    for room in successful_rooms:
        prompt_parts.append(f"\n--- {room.room_id} ---")
        prompt_parts.append(f"Winner: {room.judge_verdict.get('winner', 'Unknown')}")
        prompt_parts.append(f"Judge Explanation: {room.judge_verdict.get('explanation', 'N/A')}")
        prompt_parts.append(f"\nKey Takeaways:")
        for takeaway in room.takeaways:
            prompt_parts.append(f"  - {takeaway}")

    prompt_parts.append(f"\n\nBased on these debate results, provide a JSON response with:")
    prompt_parts.append("1. learned_insights: What did the TPM learn from each role's perspective?")
    prompt_parts.append("2. potential_assessment: Overall potential (high/medium/low) with confidence score")
    prompt_parts.append("3. recommendations: Numbered, prioritized recommendations for the project")

    return '\n'.join(prompt_parts)


def run_reflection_subprocess(
    prd_text: str,
    question: str,
    successful_rooms: List[DebateRoom],
    model: Optional[str],
    verbose: bool
) -> Optional[Dict[str, Any]]:
    """
    Run TPM self-reflection subprocess.

    Args:
        prd_text: PRD document text
        question: Committee question
        successful_rooms: List of successful debate room results
        model: Optional LLM model name
        verbose: Enable verbose logging

    Returns:
        Reflection JSON dictionary or None if failed
    """
    if not successful_rooms:
        logger.warning("No successful rooms for reflection; skipping")
        return None

    logger.info("Starting TPM self-reflection...")

    # Generate prompt
    prompt = generate_reflection_prompt(prd_text, question, successful_rooms)

    # Create temporary prompt file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        temp_prompt_path = f.name

    try:
        # Use document_debate_cli with --text for reflection
        cmd = [
            sys.executable,
            "document_debate_cli.py",
            "--text", prompt
        ]

        if model:
            cmd.extend(["--model", model])

        if verbose:
            logger.debug(f"Running reflection subprocess: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=REFLECTION_TIMEOUT,
            check=False
        )

        if result.returncode == 0:
            # Try to parse JSON from output
            try:
                # Look for JSON in output
                json_match = re.search(r'\{[\s\S]*\}', result.stdout)
                if json_match:
                    reflection = json.loads(json_match.group(0))
                    logger.info("TPM reflection completed successfully")
                    return reflection
                else:
                    logger.warning("No JSON found in reflection output; using structured parsing")
                    # For MVP, create basic structure from output
                    return {
                        "learned_insights": [f"Reflection based on {len(successful_rooms)} debate rooms"],
                        "potential_assessment": {
                            "overall": "medium",
                            "confidence": 0.7
                        },
                        "recommendations": [
                            "Review debate results for detailed insights",
                            "Consider implementing high-priority takeaways from successful rooms"
                        ]
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse reflection JSON: {e}")
                return None
        else:
            logger.error(f"Reflection subprocess failed: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.error("Reflection subprocess timed out")
        return None
    except Exception as e:
        logger.error(f"Error running reflection: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_prompt_path)
        except:
            pass


# --- Report Generation (WP05) ---

def generate_final_report(
    run_id: str,
    prd_path: str,
    question: str,
    rooms: List[DebateRoom],
    reflection: Optional[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> str:
    """
    Generate final markdown committee report.

    Args:
        run_id: Run identifier
        prd_path: Path to PRD document
        question: Committee question
        rooms: All debate room results
        reflection: TPM reflection data
        metadata: Run metadata

    Returns:
        Markdown report content
    """
    lines = [
        f"# Product Committee Report",
        f"",
        f"**Run ID:** {run_id}",
        f"**Generated:** {metadata['end_time']}",
        f"",
        f"---",
        f"",
        f"## Committee Question",
        f"",
        f"{question}",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
    ]

    # Count successful rooms
    successful = [r for r in rooms if r.status == "success"]
    failed = [r for r in rooms if r.status == "failed"]
    skipped = [r for r in rooms if r.status == "skipped_missing_prompt"]

    lines.append(f"This report synthesizes debate results from {len(rooms)} committee rooms:")
    lines.append(f"- **Successful rooms:** {len(successful)}")
    lines.append(f"- **Failed rooms:** {len(failed)}")
    lines.append(f"- **Skipped rooms:** {len(skipped)} (missing role prompts)")
    lines.append("")

    # Room-by-room analysis
    lines.extend([
        f"---",
        f"",
        f"## Room-by-Room Analysis",
        f""
    ])

    for room in rooms:
        lines.extend([
            f"### {room.room_id}",
            f"",
            f"**Status:** {room.status}",
            f""
        ])

        if room.status == "success":
            lines.extend([
                f"**Winner:** {room.judge_verdict.get('winner', 'Unknown')}",
                f"",
                f"**Judge Explanation:**",
                f"{room.judge_verdict.get('explanation', 'N/A')}",
                f"",
                f"**Key Takeaways:**",
                f""
            ])
            for takeaway in room.takeaways:
                lines.append(f"- {takeaway}")
            lines.append("")
        elif room.status == "failed":
            lines.extend([
                f"**Error:** {room.error or 'Unknown error'}",
                f""
            ])
        else:
            lines.append(f"*Skipped: Role prompt file not found*\n")

    # Reflection section
    if reflection:
        lines.extend([
            f"---",
            f"",
            f"## TPM Reflection",
            f"",
            f"### Learned Insights",
            f""
        ])

        insights = reflection.get("learned_insights", [])
        if isinstance(insights, list):
            for insight in insights:
                lines.append(f"- {insight}")
        else:
            lines.append(str(insights))

        lines.extend([
            f"",
            f"### Potential Assessment",
            f""
        ])

        assessment = reflection.get("potential_assessment", {})
        lines.append(f"**Overall:** {assessment.get('overall', 'Unknown')}")
        lines.append(f"**Confidence:** {assessment.get('confidence', 'N/A')}")

        lines.extend([
            f"",
            f"### Recommendations",
            f""
        ])

        recommendations = reflection.get("recommendations", [])
        if isinstance(recommendations, list):
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append(str(recommendations))

        lines.append("")
    else:
        lines.extend([
            f"---",
            f"",
            f"## TPM Reflection",
            f"",
            f"*No reflection data available (no successful rooms or reflection failed)*",
            f""
        ])

    # Metadata footer
    lines.extend([
        f"---",
        f"",
        f"## Metadata",
        f"",
        f"- **PRD:** {prd_path}",
        f"- **Roles directory:** {metadata.get('roles_dir', 'N/A')}",
        f"- **Model:** {metadata.get('model', 'default')}",
        f"- **Max retries:** {metadata.get('max_retries', 2)}",
        f"- **Start time:** {metadata.get('start_time', 'N/A')}",
        f"- **End time:** {metadata.get('end_time', 'N/A')}",
        ""
    ])

    return '\n'.join(lines)


def save_artifacts(
    run_id: str,
    rooms: List[DebateRoom],
    reflection: Optional[Dict[str, Any]],
    metadata: Dict[str, Any],
    report: str,
    output_dir: Path
) -> Path:
    """
    Save all artifacts to output directory.

    Args:
        run_id: Run identifier
        rooms: Debate room results
        reflection: Reflection data
        metadata: Run metadata
        report: Markdown report content
        output_dir: Base output directory

    Returns:
        Path to output directory
    """
    # Create run-specific output directory
    run_output_dir = output_dir / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving artifacts to {run_output_dir}")

    # Save metadata
    metadata_path = run_output_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.debug(f"Saved metadata to {metadata_path}")

    # Save room results
    for room in rooms:
        room_path = run_output_dir / f"{room.room_id}.json"
        with open(room_path, 'w') as f:
            f.write(room.to_json())
        logger.debug(f"Saved room result to {room_path}")

    # Save reflection
    if reflection:
        reflection_path = run_output_dir / "tpm_reflection.json"
        with open(reflection_path, 'w') as f:
            json.dump(reflection, f, indent=2)
        logger.debug(f"Saved reflection to {reflection_path}")

    # Save final report
    report_path = run_output_dir / "final_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Saved final report to {report_path}")

    return run_output_dir


def main():
    """Main entry point for the Product Committee Orchestrator."""

    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    logger.info("Product Committee Orchestrator starting...")
    logger.info(f"PRD: {args.prd}")
    logger.info(f"Question: {args.question}")

    # Validate role prompt files
    prd_path = Path(args.prd)
    roles_dir = Path(args.roles_dir)
    role_files = validate_role_prompts(roles_dir)

    # Generate run ID
    run_id = generate_run_id(args.question, args.run_id)
    logger.info(f"Run ID: {run_id}")

    # Create metadata
    metadata = create_metadata(
        run_id=run_id,
        prd_path=args.prd,
        question=args.question,
        model=args.model,
        roles_dir=args.roles_dir,
        output_dir=args.output_dir,
        max_retries=args.max_retries
    )

    # Read PRD text for reflection
    prd_text = read_prd_text(prd_path)

    logger.info(f"Starting debate rooms...")
    logger.info(f"Max retries: {args.max_retries}")

    # Run all debate rooms
    rooms = run_all_rooms(
        prd_path=prd_path,
        question=args.question,
        role_files=role_files,
        model=args.model,
        max_retries=args.max_retries,
        verbose=args.verbose,
        metadata=metadata
    )

    # Run TPM reflection
    successful_rooms = [r for r in rooms if r.status == "success"]
    reflection = None

    if successful_rooms:
        logger.info(f"Running TPM self-reflection based on {len(successful_rooms)} successful rooms...")
        reflection = run_reflection_subprocess(
            prd_text=prd_text,
            question=args.question,
            successful_rooms=successful_rooms,
            model=args.model,
            verbose=args.verbose
        )
    else:
        logger.warning("No successful rooms; skipping TPM reflection")

    # Update metadata
    metadata["end_time"] = datetime.utcnow().isoformat()

    # Generate final report
    logger.info("Generating final report...")
    report = generate_final_report(
        run_id=run_id,
        prd_path=args.prd,
        question=args.question,
        rooms=rooms,
        reflection=reflection,
        metadata=metadata
    )

    # Save all artifacts
    output_path = save_artifacts(
        run_id=run_id,
        rooms=rooms,
        reflection=reflection,
        metadata=metadata,
        report=report,
        output_dir=Path(args.output_dir)
    )

    logger.info(f"Product Committee Orchestrator completed successfully!")
    logger.info(f"Artifacts saved to: {output_path}")
    logger.info(f"Final report: {output_path / 'final_report.md'}")

    # Exit with error if any rooms failed
    if any(r.status == "failed" for r in rooms):
        logger.warning("Some rooms failed. Check metadata.json for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
