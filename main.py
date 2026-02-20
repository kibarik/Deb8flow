#!/usr/bin/env python3
"""
Deb8flow - Multi-Agent AI Debate Framework

Main entry point for running debates, product committees, and conclusion generation.

Usage:
    python main.py debate --text "Topic" --pro-prompt pro.txt --con-prompt con.txt
    python main.py committee --prd prd.txt --question "Should we build this?"
    python main.py conclusion --run-dir ./committee_output/RUN_XXX

Separate scripts:
    scripts/conclusion_results.py - Generate conclusion from final_report.md
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import CLI adapters and executors
from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor
from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage
from src.committee.application.run_committee import RunProductCommittee
from src.committee.adapters.reports.final_report import FinalReportGenerator
from src.committee.adapters.reports.conclusion import ConclusionGenerator
from src.shared.config import load_config, DebateConfigFile

logger = logging.getLogger(__name__)

# Constants
DEFAULT_ROLES_DIR = "config/prompts/roles/"
DEFAULT_OUTPUT_DIR = "./committee_output"
DEFAULT_CONFIG_PATH = "config/debate_config.yaml"
MIN_CONCURRENCY = 0
MAX_CONCURRENCY = 4


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags."""
    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def run_debate(args) -> int:
    """Run document-based debate."""
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    from document_debate_cli import main as debate_main

    # Convert args to namespace for the original script
    import types
    args_ns = types.SimpleNamespace(
        text=args.text,
        docx=args.docx,
        pro_prompt=args.pro_prompt,
        con_prompt=args.con_prompt,
        model=args.model,
        language=args.language,
        json_output=args.json_output,
        temperature=args.temperature,
        api_key=args.api_key,
        base_url=args.base_url
    )

    # Monkey patch sys.argv for the subprocess script
    old_argv = sys.argv
    sys.argv = ["document_debate_cli.py"]
    if args.text:
        sys.argv.extend(["--text", args.text])
    if args.docx:
        sys.argv.extend(["--docx", args.docx])
    if args.pro_prompt:
        sys.argv.extend(["--pro-prompt", args.pro_prompt])
    if args.con_prompt:
        sys.argv.extend(["--con-prompt", args.con_prompt])
    if args.model:
        sys.argv.extend(["--model", args.model])
    if args.language:
        sys.argv.extend(["--language", args.language])
    if args.json_output:
        sys.argv.extend(["--json-output", args.json_output])
    if args.temperature is not None:
        sys.argv.extend(["--temperature", str(args.temperature)])
    if args.api_key:
        sys.argv.extend(["--api-key", args.api_key])
    if args.base_url:
        sys.argv.extend(["--base-url", args.base_url])

    try:
        return asyncio.run(debate_main())
    finally:
        sys.argv = old_argv


async def run_committee_async(args) -> int:
    """Run product committee (async implementation)."""
    # Load configuration
    config_path = args.config if args.config else DEFAULT_CONFIG_PATH
    try:
        config = DebateConfigFile.from_yaml_or_default(config_path)
        config.setup_logging()
        logger.info(f"Loaded configuration from: {config_path if Path(config_path).exists() else 'defaults'}")
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using CLI arguments only")
        config = None

    # Apply config defaults (CLI args take precedence)
    config_dict = config.get_cli_args_dict() if config else {}

    # Get agents config from config file or use defaults
    if config and config.agents.main_agent:
        agents_config = config.agents
        logger.info(f"Using agents from config: main={agents_config.main_agent.name}, "
                   f"opponents={[opp.name for opp in agents_config.opponents]}")
    else:
        # Fallback to roles_dir if provided
        from src.shared.config import AgentsConfig, AgentConfig
        roles_path = Path(args.roles_dir)

        if not roles_path.exists():
            logger.error(f"Roles directory not found: {args.roles_dir}")
            logger.error("Please configure agents in debate_config.yaml or provide a valid --roles-dir")
            return 1

        # Build agents config from roles directory
        tpm_path = roles_path / "tpm.txt"
        if not tpm_path.exists():
            logger.error(f"TPM prompt not found in roles directory: {tpm_path}")
            return 1

        main_agent = AgentConfig(name="TPM", prompt_path=str(tpm_path), role="main")
        opponents = []

        # Try to find standard role files
        for role_name in ["cpo", "cfo", "cto", "bdm"]:
            role_path = roles_path / f"{role_name}.txt"
            if role_path.exists():
                opponents.append(AgentConfig(
                    name=role_name.upper(),
                    prompt_path=str(role_path),
                    role="opponent"
                ))

        agents_config = AgentsConfig(main_agent=main_agent, opponents=opponents)
        logger.info(f"Using agents from roles directory: main={main_agent.name}, "
                   f"opponents={[opp.name for opp in opponents]}")

    # Create infrastructure adapters with LLM config from file
    llm_config = config.llm if config else None
    executor = CliDebateExecutor(llm_config=llm_config)
    storage = LocalFileStorage()

    class ReportGeneratorAdapter:
        """Adapter combining both report generators."""
        def __init__(self):
            self.final_gen = FinalReportGenerator()
            self.conclusion_gen = ConclusionGenerator()

        def generate_final_report(self, run_id: str, prd_path: str, question: str, rooms, metadata: dict) -> str:
            return self.final_gen.generate_final_report(run_id, prd_path, question, rooms, metadata)

        def generate_conclusion(self, question: str, rooms, metadata: dict) -> str:
            return self.conclusion_gen.generate_conclusion(question, rooms, metadata)

        def generate_intermediate_report(self, run_id: str, completed_rooms, total_rooms: int) -> str:
            return self.final_gen.generate_intermediate_report(run_id, completed_rooms, total_rooms)

    generator = ReportGeneratorAdapter()

    # Create use case
    use_case = RunProductCommittee(executor, generator, storage)

    # Execute committee
    try:
        result = await use_case.execute(
            prd_path=args.prd,
            question=args.question,
            agents_config=agents_config,
            model=args.model or config_dict.get("model"),
            language=args.language or config_dict.get("language"),
            max_retries=args.max_retries if args.max_retries is not None else config_dict.get("max_retries", 2),
            max_concurrency=args.max_concurrency if args.max_concurrency is not None else config_dict.get("max_concurrency", 2),
            output_dir=Path(args.output_dir) if args.output_dir else config_dict.get("output_dir", Path(DEFAULT_OUTPUT_DIR)),
            manual_run_id=args.run_id,
        )

        logger.info(f"Product Committee completed successfully!")
        logger.info(f"Run ID: {result.run_id.value}")
        logger.info(f"Output directory: {args.output_dir if args.output_dir else DEFAULT_OUTPUT_DIR}/{result.run_id.value}")

        if result.failed_rooms:
            logger.warning(f"{len(result.failed_rooms)} room(s) failed. Check metadata.json for details.")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_committee(args) -> int:
    """Run product committee."""
    try:
        exit_code = asyncio.run(run_committee_async(args))
        return exit_code
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130


def run_conclusion(args) -> int:
    """Generate conclusion from committee results."""
    run_dir = Path(args.run_dir)

    # Find final_report.md in the run directory
    final_report_path = run_dir / "final_report.md"
    if not final_report_path.exists():
        logger.error(f"final_report.md not found in: {run_dir}")
        return 1

    # Import here
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    from conclusion_results import main as conclusion_main

    # Monkey patch sys.argv - script expects path to final_report.md
    old_argv = sys.argv
    sys.argv = ["conclusion_results.py", str(final_report_path)]
    if args.prompt:
        sys.argv.extend(["--prompt", args.prompt])

    try:
        return conclusion_main()
    finally:
        sys.argv = old_argv


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deb8flow - Multi-Agent AI Debate Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a document-based debate
  %(prog)s debate --text "GitHub is useful for developers" --pro-prompt pro.txt --con-prompt con.txt

  # Run product committee (agents configured in debate_config.yaml)
  %(prog)s committee --prd prd.txt --question "What is the potential of this project?"

  # Run product committee with custom config
  %(prog)s committee --prd prd.txt --question "Should we build this?" --config my_config.yaml

  # Generate conclusion from existing committee results
  %(prog)s conclusion --run-dir ./committee_output/RUN_20260218_234755

  # Generate conclusion with custom instruction
  %(prog)s conclusion --run-dir ./committee_output/RUN_20260218_234755 --prompt /path/to/instruction.txt

Agent Configuration:
  Configure agents in debate_config.yaml under the 'agents' section:
    agents:
      main:
        name: "TPM"
        prompt: "config/prompts/roles/tpm.txt"
      opponents:
        - name: "CPO"
          prompt: "config/prompts/roles/cpo.txt"
        - name: "CFO"
          prompt: "config/prompts/roles/cfo.txt"
        """
    )

    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Debate subcommand
    debate_parser = subparsers.add_parser(
        "debate",
        help="Run document-based debate between PRO and CON participants",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    debate_parser.add_argument("--text", required=True, help="Debate topic/content text")
    debate_parser.add_argument("--docx", help="Path to .docx file (alternative to --text)")
    debate_parser.add_argument("--pro-prompt", required=True, help="Path to PRO debater prompt file")
    debate_parser.add_argument("--con-prompt", required=True, help="Path to CON debater prompt file")
    debate_parser.add_argument("--model", help="LLM model name")
    debate_parser.add_argument("--language", help="Language for output")
    debate_parser.add_argument("--json-output", help="Path to save JSON output")
    debate_parser.add_argument("--temperature", type=float, help="Sampling temperature")
    debate_parser.add_argument("--api-key", help="OpenAI API key")
    debate_parser.add_argument("--base-url", help="Custom API base URL")

    # Committee subcommand
    committee_parser = subparsers.add_parser(
        "committee",
        help="Run product committee with multiple debate rooms",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    committee_parser.add_argument("--prd", required=True, help="Path to PRD document")
    committee_parser.add_argument("--question", required=True, help="Committee question")
    committee_parser.add_argument("--config", help=f"Path to YAML config file (default: {DEFAULT_CONFIG_PATH})")
    committee_parser.add_argument("--model", help="LLM model name (overrides config)")
    committee_parser.add_argument("--base-url", help="API base URL (overrides config)")
    committee_parser.add_argument("--api-key", help="API key (overrides config)")
    committee_parser.add_argument("--temperature", type=float, help="Sampling temperature (overrides config)")
    committee_parser.add_argument("--language", help="Language for output (overrides config)")
    committee_parser.add_argument("--max-retries", type=int, help="Max retry attempts (overrides config)")
    committee_parser.add_argument("--max-concurrency", type=int, help="Max parallel rooms 0=all (overrides config)")
    committee_parser.add_argument("--output-dir", help="Output directory (overrides config)")
    committee_parser.add_argument("--roles-dir", default=DEFAULT_ROLES_DIR,
                                 help="Roles directory (fallback if agents not configured in config file)")
    committee_parser.add_argument("--run-id", help="Manual run identifier")

    # Conclusion subcommand
    conclusion_parser = subparsers.add_parser(
        "conclusion",
        help="Generate conclusion from existing committee results",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conclusion_parser.add_argument("--run-dir", required=True, help="Path to committee run directory")
    conclusion_parser.add_argument("--prompt", help="Path to custom prompt file for conclusion generation")

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "debate":
        return run_debate(args)
    elif args.command == "committee":
        return run_committee(args)
    elif args.command == "conclusion":
        return run_conclusion(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
