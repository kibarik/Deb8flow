#!/usr/bin/env python3
"""
Committee Conclusion Generator Script

A standalone CLI script that regenerates the `conclusion.md` file for existing
Product Committee runs by analyzing the `final_report.md` content.

Usage:
    python3 conclusion_results.py '/path/to/final_report.md'
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the ConclusionGenerator from our refactored code
from src.committee.adapters.reports.conclusion import ConclusionGenerator
from src.shared.debate.domain.entities import DebateRoom, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity flag."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s [%(name)s] - %(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_arguments() -> argparse.Namespace:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Regenerate conclusion.md from an existing final_report.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 conclusion_results.py committee_output/RUN_20260217_230136_test/final_report.md
  python3 conclusion_results.py '/path/to/final_report.md' --verbose
  python3 conclusion_results.py '/path/to/final_report.md' --prompt /path/to/custom_prompt.txt
        """
    )

    parser.add_argument(
        "final_report_path",
        help="Path to the final_report.md file to analyze"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "-p", "--prompt",
        help="Path to custom prompt file for conclusion generation"
    )

    return parser.parse_args()


def validate_input_path(path: Path) -> None:
    """
    Validate that the input path exists and is a readable file.

    Args:
        path: Path to validate

    Raises:
        SystemExit: If validation fails
    """
    if not path.exists():
        logger.error(f"Error: File not found: {path}")
        sys.exit(1)

    if not path.is_file():
        logger.error(f"Error: Path is not a file: {path}")
        sys.exit(1)

    if path.suffix.lower() != ".md":
        logger.warning(f"Warning: Input file is not a markdown file: {path}")


def parse_final_report(content: str) -> Dict[str, Any]:
    """
    Parse the final_report.md content to extract committee data.

    Args:
        content: The markdown content of final_report.md

    Returns:
        Dictionary with extracted data:
        {
            "question": str,
            "rooms": List[DebateRoom],
            "metadata": Dict[str, Any]
        }
    """
    lines = content.split('\n')

    question = None
    rooms = []
    current_room = None
    in_room_section = False

    # Metadata tracking
    metadata = {
        "end_time": datetime.now(timezone.utc).isoformat()
    }

    for i, line in enumerate(lines):
        # Extract committee question
        if line.startswith("## Committee Question"):
            # Question is on the next non-empty line
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith("---"):
                    question = lines[j].strip()
                    break
                elif lines[j].startswith("---"):
                    break

        # Start of room section
        if line.startswith("### ") and "_vs_" in line:
            # Save previous room if exists
            if current_room:
                rooms.append(current_room)

            room_id = line.replace("###", "").strip()
            opponent = room_id.split("_vs_")[-1] if "_vs_" in room_id else "UNKNOWN"

            current_room = {
                "room_id": room_id,
                "opponent": opponent,
                "status": None,
                "winner": None,
                "summary": None,
                "error": None,
                "takeaways": []
            }
            in_room_section = True

        # Inside a room section
        if in_room_section and current_room:
            # Status line
            if "**Status:**" in line:
                status = line.split("**Status:**")[1].strip().lower()
                current_room["status"] = status
                if status == "success":
                    current_room["status"] = "success"
                elif status == "failed":
                    current_room["status"] = "failed"
                else:
                    current_room["status"] = status

            # Winner line (for successful rooms)
            if "**Winner:**" in line:
                winner_str = line.split("**Winner:**")[1].strip()
                if winner_str == "PRO":
                    current_room["winner"] = Speaker.PRO
                elif winner_str == "CON":
                    current_room["winner"] = Speaker.CON

            # Error line (for failed rooms)
            if "**Error:**" in line:
                current_room["error"] = line.split("**Error:**")[1].strip()

            # Judge explanation
            if "**Judge Explanation:**" in line:
                # Collect explanation lines until next section
                explanation_lines = []
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if next_line.startswith("**") or next_line.startswith("---") or next_line.startswith("###"):
                        break
                    explanation_lines.append(next_line)
                current_room["summary"] = "\n".join(explanation_lines).strip()

            # Takeaways list items (check if we're in a Key Takeaways section)
            if line.strip().startswith("- "):
                # Look back for "Key Takeaways" heading
                in_takeaways = False
                for j in range(max(0, i - 10), i):
                    if "Key Takeaways" in lines[j]:
                        in_takeaways = True
                        break
                    if lines[j].startswith("###") or lines[j].startswith("**"):
                        break
                if in_takeaways:
                    takeaway = line.strip().replace("- ", "", 1)
                    current_room["takeaways"].append(takeaway)

        # End of room section
        if line.startswith("---") and in_room_section:
            in_room_section = False

    # Save last room
    if current_room:
        rooms.append(current_room)

    # Extract PRD path from Metadata section at the end
    for i, line in enumerate(lines):
        if line.strip().startswith("- **PRD:**") or line.strip().startswith("**PRD:**"):
            # Extract PRD path - format: "- **PRD:** /path/to/file" or "**PRD:** /path/to/file"
            if "**PRD:**" in line:
                prd_path = line.split("**PRD:**")[1].strip()
                metadata["prd_path"] = prd_path
            break
    # Also try to load from metadata.json if it exists
    # (this will be checked by the caller)

    return {
        "question": question or "Unknown question",
        "rooms": rooms,
        "metadata": metadata
    }


def convert_to_debate_rooms(parsed_rooms: List[Dict]) -> List[DebateRoom]:
    """
    Convert parsed room data to DebateRoom entities.

    Args:
        parsed_rooms: List of parsed room dictionaries

    Returns:
        List of DebateRoom entities
    """
    debate_rooms = []

    for room_data in parsed_rooms:
        # Map status string to RoomStatus enum
        status_str = room_data.get("status", "unknown")
        if status_str == "success":
            status = RoomStatus.SUCCESS
        elif status_str == "failed":
            status = RoomStatus.FAILED
        elif "skipped" in status_str:
            status = RoomStatus.SKIPPED
        else:
            status = RoomStatus.FAILED

        # Create verdict for successful rooms
        verdict = None
        if status == RoomStatus.SUCCESS and room_data.get("winner"):
            verdict = Verdict(
                winner=room_data["winner"],
                explanation=room_data.get("summary", "No explanation provided")
            )

        # Create room ID
        try:
            room_id = RoomId(room_data["room_id"])
        except Exception:
            room_id = RoomId(f"TPM_vs_{room_data.get('opponent', 'UNKNOWN')}")

        # Create DebateRoom
        debate_room = DebateRoom(
            room_id=room_id,
            pro_participant="TPM",
            con_participant=room_data.get("opponent", "UNKNOWN"),
            status=status,
            messages=[],  # Not parsing full dialogue for conclusion
            verdict=verdict,
            takeaways=room_data.get("takeaways", []),
            error=room_data.get("error")
        )

        debate_rooms.append(debate_room)

    return debate_rooms


def main():
    """Main entry point for the conclusion generator script."""
    args = parse_arguments()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Validate input path
    report_path = Path(args.final_report_path)
    validate_input_path(report_path)

    logger.info(f"Reading final report from: {report_path}")

    # Load custom prompt if provided
    custom_prompt = None
    if args.prompt:
        prompt_path = Path(args.prompt)
        if not prompt_path.exists():
            logger.error(f"Error: Prompt file not found: {prompt_path}")
            sys.exit(1)
        try:
            custom_prompt = prompt_path.read_text(encoding="utf-8")
            logger.info(f"Loaded custom prompt from: {prompt_path}")
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            sys.exit(1)

    # Read the final report content
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        sys.exit(1)

    # Try to load metadata.json for additional context (e.g., prd_path)
    metadata_json_path = report_path.parent / "metadata.json"
    if metadata_json_path.exists():
        try:
            with open(metadata_json_path, 'r', encoding='utf-8') as f:
                metadata_from_json = json.load(f)
                # Store for later use - we'll merge it with parsed metadata
                logger.debug(f"Loaded metadata from {metadata_json_path}")
        except Exception as e:
            logger.warning(f"Could not load metadata.json: {e}")
            metadata_from_json = {}
    else:
        metadata_from_json = {}

    if not content.strip():
        logger.error("Error: final_report.md is empty")
        sys.exit(1)

    # Collect takeaways from all dialogue JSON files
    logger.info("Collecting takeaways from dialogue JSON files...")
    all_takeaways = []
    run_dir = report_path.parent

    # Find all dialogue JSON files
    dialogue_files = sorted(run_dir.glob("*_dialogue.json"))
    logger.info(f"Found {len(dialogue_files)} dialogue files")

    for dialogue_file in dialogue_files:
        try:
            with open(dialogue_file, 'r', encoding='utf-8') as f:
                dialogue_data = json.load(f)
                if 'takeaways' in dialogue_data and dialogue_data['takeaways']:
                    room_id = dialogue_data.get('room_id', dialogue_file.stem)
                    logger.info(f"  {room_id}: {len(dialogue_data['takeaways'])} takeaways")
                    for takeaway in dialogue_data['takeaways']:
                        all_takeaways.append({
                            'room': room_id,
                            'text': takeaway
                        })
        except Exception as e:
            logger.warning(f"Could not read {dialogue_file}: {e}")

    logger.info(f"Total takeaways collected: {len(all_takeaways)}")

    # Parse the report to extract basic data (question, etc)
    logger.info("Parsing final report...")
    parsed_data = parse_final_report(content)

    # Merge metadata from JSON (JSON takes precedence for prd_path)
    if metadata_from_json:
        parsed_data["metadata"].update(metadata_from_json)

    if not parsed_data["rooms"]:
        logger.warning("Warning: No rooms found in report")

    # Convert to DebateRoom entities
    debate_rooms = convert_to_debate_rooms(parsed_data["rooms"])

    logger.info(f"Found {len(debate_rooms)} debate rooms:")
    for room in debate_rooms:
        status_icon = "✓" if room.is_successful else "✗"
        winner = f" (Winner: {room.verdict.winner.value})" if room.verdict else ""
        logger.info(f"  {status_icon} {room.room_id.value}: {room.status.value}{winner}")

    # Generate conclusion using our ConclusionGenerator
    logger.info("Generating conclusion...")
    generator = ConclusionGenerator()

    try:
        conclusion = generator.generate_conclusion(
            question=parsed_data["question"],
            rooms=debate_rooms,
            metadata=parsed_data["metadata"],
            custom_prompt=custom_prompt,
            all_takeaways=all_takeaways
        )
    except Exception as e:
        logger.error(f"Error generating conclusion: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Write conclusion to file
    output_path = report_path.parent / "conclusion.md"
    try:
        output_path.write_text(conclusion, encoding="utf-8")
        logger.info(f"Conclusion saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error writing conclusion file: {e}")
        sys.exit(1)

    logger.info("Done!")


if __name__ == "__main__":
    main()
