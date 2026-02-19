#!/usr/bin/env python3
"""
Document Debate CLI - Real LLM Integration

A CLI for executing AI-powered debates between PRO and CON participants.
This is called by the CliDebateExecutor in the product committee workflow.

Usage:
    python3 document_debate_cli.py --text <content> --pro-prompt <file> --con-prompt <file>
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.shared.debate.infrastructure.llm.debate_orchestrator import SimpleDebateOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments with environment variable support."""
    parser = argparse.ArgumentParser(
        description="Document Debate CLI - AI-Powered Debates",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--text", required=True, help="Debate topic/content text")
    parser.add_argument("--docx", help="Path to .docx file (alternative to --text)")
    parser.add_argument("--pro-prompt", required=True, help="Path to PRO debater prompt file")
    parser.add_argument("--con-prompt", required=True, help="Path to CON debater prompt file")

    # LLM parameters - CLI args override environment variables
    parser.add_argument("--model", help="LLM model name (default: from env or gpt-4o-mini)")
    parser.add_argument("--language", help="Language for output")
    parser.add_argument("--json-output", help="Path to save JSON output")
    parser.add_argument("--temperature", type=float,
                       help="Sampling temperature (default: from env or 0.8)")
    parser.add_argument("--api-key", help="OpenAI API key (default: from env)")
    parser.add_argument("--base-url", help="Custom API base URL (default: from env)")

    return parser.parse_args()


def get_llm_config(args) -> tuple:
    """
    Get LLM configuration from CLI args or environment variables.

    Priority: CLI args > DEBATE_* env vars > OPENAI_* env vars > defaults

    Returns:
        Tuple of (model, temperature, api_key, base_url)
    """
    # Model
    model = args.model or os.environ.get("DEBATE_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"

    # Temperature
    if args.temperature is not None:
        temperature = args.temperature
    else:
        temp_env = os.environ.get("DEBATE_TEMPERATURE")
        temperature = float(temp_env) if temp_env else 0.8

    # API Key
    api_key = (args.api_key or
               os.environ.get("DEBATE_API_KEY") or
               os.environ.get("OPENAI_API_KEY") or
               os.environ.get("LLM_API_KEY") or "")

    # Base URL
    base_url = (args.base_url or
                os.environ.get("DEBATE_BASE_URL") or
                os.environ.get("OPENAI_API_BASE") or
                os.environ.get("API_BASE_URL") or "")

    return model, temperature, api_key, base_url


async def run_debate(
    text: str,
    pro_prompt_path: str,
    con_prompt_path: str,
    model: Optional[str],
    language: Optional[str],
    json_output_path: Optional[str],
    temperature: float,
    api_key: Optional[str],
    base_url: Optional[str]
) -> dict:
    """
    Run an AI-powered debate simulation.

    Args:
        text: The debate topic/content text
        pro_prompt_path: Path to PRO debater prompt file
        con_prompt_path: Path to CON debater prompt file
        model: LLM model name
        language: Optional language setting
        json_output_path: Path to save JSON output
        temperature: Sampling temperature
        api_key: API key for LLM
        base_url: Custom API base URL

    Returns:
        Dictionary with dialogue and winner
    """
    # Read prompts
    try:
        pro_prompt_content = Path(pro_prompt_path).read_text(encoding="utf-8")
        con_prompt_content = Path(con_prompt_path).read_text(encoding="utf-8")
        logger.info(f"Loaded prompts: PRO ({len(pro_prompt_content)} chars), CON ({len(con_prompt_content)} chars)")
    except Exception as e:
        logger.error(f"Failed to read prompt files: {e}")
        raise

    # Get API key from argument or environment
    if not api_key:
        raise ValueError("API key not provided. Set OPENAI_API_KEY, DEBATE_API_KEY environment variable or use --api-key")

    # Extract question from text (assume first line or use default)
    lines = text.strip().split('\n')
    question = lines[0] if lines else "Should this project proceed?"

    # Log configuration
    logger.info(f"Debate configuration:")
    logger.info(f"  Model: {model}")
    if base_url:
        logger.info(f"  Base URL: {base_url}")
    logger.info(f"  Temperature: {temperature}")
    logger.info(f"  Language: {language or 'en (default)'}")

    # Initialize orchestrator
    orchestrator = SimpleDebateOrchestrator(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url if base_url else None,
        language=language or "en"
    )

    # Execute debate
    try:
        dialogue, winner = await orchestrator.execute_debate(
            topic=text,
            pro_prompt=pro_prompt_content,
            con_prompt=con_prompt_content,
            question=question,
            prd_content=text
        )

        logger.info(f"Debate completed. Winner: {winner}. Messages: {len(dialogue)}")

        result = {
            "dialogue": dialogue,
            "winner": winner,
            "summary": f"Debate completed with {len(dialogue)} messages. Winner: {winner}."
        }

        # Save JSON output if requested
        if json_output_path:
            try:
                Path(json_output_path).write_text(
                    json.dumps(dialogue, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                logger.info(f"Saved dialogue to: {json_output_path}")
            except Exception as e:
                logger.warning(f"Failed to save JSON output: {e}")

        return result

    except Exception as e:
        logger.error(f"Debate execution failed: {e}")
        raise


async def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Get LLM config from args or environment
        model, temperature, api_key, base_url = get_llm_config(args)

        result = await run_debate(
            text=args.text,
            pro_prompt_path=args.pro_prompt,
            con_prompt_path=args.con_prompt,
            model=model,
            language=args.language,
            json_output_path=args.json_output,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url
        )

        # Output results as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except KeyboardInterrupt:
        logger.info("Debate interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
