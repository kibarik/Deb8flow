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
import warnings
from pathlib import Path
from typing import Optional

# Suppress Pydantic warnings for Python 3.14
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible with Python 3.14")

# Add the src directory to the path for imports
# Need parent directory (project root) since src is at the root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.debate.infrastructure.llm.debate_orchestrator import LLMDebateOrchestrator
from src.shared.debate.application.prompt_loader import PromptLoader
from src.shared.config import load_config, DebateConfigFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress httpx and httpcore INFO logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


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
    parser.add_argument("--fallback-models", help="Comma-separated list of fallback models (default: from config)")
    parser.add_argument("--language", help="Language for output")
    parser.add_argument("--json-output", help="Path to save JSON output")
    parser.add_argument("--temperature", type=float,
                       help="Sampling temperature (default: from env or 0.8)")
    parser.add_argument("--api-key", help="OpenAI API key (default: from env)")
    parser.add_argument("--base-url", help="Custom API base URL (default: from env)")
    parser.add_argument("--room-id", help="Room identifier for logging (default: 'Debate')")

    return parser.parse_args()


def get_llm_config(args) -> tuple:
    """
    Get LLM configuration from CLI args, config file, or environment variables.

    Priority: CLI args > config file > environment variables > defaults

    Returns:
        Tuple of (model, temperature, api_key, base_url, max_tokens)
    """
    # Try to load config file first
    try:
        config = DebateConfigFile.from_yaml_or_default()
        if config and config.llm:
            llm_config = config.llm
            # Use config values as defaults
            default_model = llm_config.model
            default_temperature = llm_config.temperature
            default_api_key = llm_config.api_key
            default_base_url = llm_config.get_effective_base_url() or ""
            default_max_tokens = getattr(llm_config, 'max_tokens', 5000)
        else:
            default_model = "gpt-4o-mini"
            default_temperature = 0.8
            default_api_key = ""
            default_base_url = ""
            default_max_tokens = 5000
    except Exception:
        # Fallback to defaults if config loading fails
        default_model = "gpt-4o-mini"
        default_temperature = 0.8
        default_api_key = ""
        default_base_url = ""
        default_max_tokens = 5000

    # Model: CLI args > config > env vars > default
    model = (args.model or
             default_model or
             os.environ.get("DEBATE_MODEL") or
             os.environ.get("OPENAI_MODEL") or
             "gpt-4o-mini")

    # Temperature: CLI args > config > env vars > default
    if args.temperature is not None:
        temperature = args.temperature
    else:
        temp_env = os.environ.get("DEBATE_TEMPERATURE")
        temperature = (float(temp_env) if temp_env else
                      default_temperature if default_temperature else
                      0.8)

    # API Key: CLI args > config > env vars > default
    api_key = (args.api_key or
               default_api_key or
               os.environ.get("DEBATE_API_KEY") or
               os.environ.get("OPENAI_API_KEY") or
               os.environ.get("LLM_API_KEY") or "")

    # Base URL: CLI args > config > env vars > default
    base_url = (args.base_url or
                default_base_url or
                os.environ.get("DEBATE_BASE_URL") or
                os.environ.get("OPENAI_API_BASE") or
                os.environ.get("API_BASE_URL") or "")

    # Max tokens: config > env vars > default (5000)
    max_tokens_str = os.environ.get("DEBATE_MAX_TOKENS")
    max_tokens = int(max_tokens_str) if max_tokens_str else default_max_tokens

    return model, temperature, api_key, base_url, max_tokens


async def run_debate(
    text: str,
    pro_prompt_path: str,
    con_prompt_path: str,
    model: Optional[str],
    language: Optional[str],
    json_output_path: Optional[str],
    temperature: float,
    api_key: Optional[str],
    base_url: Optional[str],
    max_tokens: int,
    room_id: Optional[str] = None
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

    # Load configuration and create PromptLoader
    try:
        config = load_config()
        if hasattr(config, 'prompts') and config.prompts:
            prompt_loader = PromptLoader(config.prompts)
            logger.info("Using PromptLoader for prompts")
        else:
            # Fallback if prompts section not available
            logger.warning("No prompts configuration found, using orchestrator defaults")
            prompt_loader = None
    except Exception as e:
        logger.warning(f"Failed to load prompt configuration: {e}, using defaults")
        prompt_loader = None

    # Initialize orchestrator
    orchestrator = LLMDebateOrchestrator(
        prompt_loader=prompt_loader,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url if base_url else None,
        language=language or "en",
        room_id=room_id or "Debate",
        json_output_path=Path(json_output_path) if json_output_path else None  # Progressive saving
    )

    # Print start message to stderr for immediate feedback
    import sys
    print(f"🚀 Starting debate: {room_id or 'Debate'}", file=sys.stderr, flush=True)

    # Execute debate
    try:
        dialogue, winner = await orchestrator.execute_debate(
            topic=text,
            pro_prompt=pro_prompt_content,
            con_prompt=con_prompt_content,
            question=question,
            prd_content=text
        )

        logger.debug(f"Debate completed. Winner: {winner}. Messages: {len(dialogue)}")

        result = {
            "dialogue": dialogue,
            "winner": winner,
            "summary": f"Debate completed with {len(dialogue)} messages. Winner: {winner}."
        }

        # Note: JSON is saved progressively by orchestrator during execution
        # No need to save again here unless it failed
        if json_output_path and not Path(json_output_path).exists():
            # Fallback: if progressive saving failed, save now
            try:
                output_data = {
                    "messages": dialogue,
                    "winner": winner
                }
                Path(json_output_path).write_text(
                    json.dumps(output_data, indent=2, ensure_ascii=False),
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
        model, temperature, api_key, base_url, max_tokens = get_llm_config(args)

        result = await run_debate(
            text=args.text,
            pro_prompt_path=args.pro_prompt,
            con_prompt_path=args.con_prompt,
            model=model,
            language=args.language,
            json_output_path=args.json_output,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            max_tokens=max_tokens,
            room_id=args.room_id
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
