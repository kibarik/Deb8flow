#!/usr/bin/env python3
"""
Add takeaways to existing debate dialogue JSON files.

This script processes dialogue JSON files and generates takeaways
using LLM analysis of the debate content.

Usage:
    python3 add_takeaways_to_dialogue.py <path_to_dialogue.json> [--question "question"]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.debate.application.analyzers import TakeawayAnalyzer, TakeawayConfig


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Add takeaways to existing debate dialogue JSON files"
    )
    parser.add_argument(
        "dialogue_path",
        help="Path to the dialogue JSON file"
    )
    parser.add_argument(
        "--question",
        help="The committee question (optional, will use default if not provided)"
    )
    parser.add_argument(
        "--model",
        help="LLM model to use for takeaway generation"
    )
    parser.add_argument(
        "--api-key",
        help="API key for LLM (defaults to OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--base-url",
        help="Custom API base URL"
    )
    parser.add_argument(
        "--min",
        type=int,
        default=3,
        help="Minimum number of takeaways to generate (default: 3)"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=15,
        help="Maximum number of takeaways to generate (default: 15)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate takeaways but don't modify the file"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock takeaways instead of LLM (for testing without API key)"
    )

    return parser.parse_args()


async def process_dialogue_file(
    dialogue_path: Path,
    question: str,
    config: TakeawayConfig,
    use_mock: bool = False
) -> list:
    """
    Process a dialogue file and generate takeaways.

    Args:
        dialogue_path: Path to the dialogue JSON file
        question: The committee question
        config: Takeaway configuration
        use_mock: Use mock takeaways for testing

    Returns:
        List of generated takeaways
    """
    logger.info(f"Processing: {dialogue_path}")

    # Load the dialogue JSON
    try:
        content = dialogue_path.read_text(encoding='utf-8')
        dialogue_json = json.loads(content)
    except Exception as e:
        logger.error(f"Failed to read {dialogue_path}: {e}")
        return []

    # Extract dialogue data
    messages = dialogue_json.get("messages", [])
    verdict = dialogue_json.get("verdict", {})

    if not messages:
        logger.warning(f"No messages found in {dialogue_path}")
        return []

    # Use mock mode if requested
    if use_mock:
        return generate_mock_takeaways(dialogue_json, config)

    # Create analyzer
    analyzer = TakeawayAnalyzer(config)

    # Generate takeaways
    try:
        takeaways = await analyzer.generate_takeaways(
            dialogue=messages,
            question=question,
            verdict_explanation=verdict.get("explanation"),
            winner=verdict.get("winner")
        )
        return takeaways
    except Exception as e:
        logger.error(f"Failed to generate takeaways: {e}")
        return []


def generate_mock_takeaways(dialogue_json: dict, config: TakeawayConfig) -> list:
    """Generate mock takeaways for testing without API key."""
    import re

    verdict = dialogue_json.get("verdict", {})
    winner = verdict.get("winner", "PRO")
    explanation = verdict.get("explanation", "")
    messages = dialogue_json.get("messages", [])

    # Generate mock takeaways based on actual dialogue content
    takeaways = []

    # Analyze PRO messages for strengths
    pro_messages = [m for m in messages if m.get("speaker") == "PRO"]
    con_messages = [m for m in messages if m.get("speaker") == "CON"]

    # Extract key themes from dialogue
    all_text = " ".join([m.get("content", "") for m in messages])

    # Common themes to look for
    themes = {
        "техническая": "Техническая архитектура",
        "рынок": "Рыночное позиционирование",
        "бизнес": "Бизнес-модель",
        "финансов": "Финансовая модель",
        "конкурент": "Конкурентная стратегия",
        "масштаб": "Масштабируемость",
        "риск": "Риски проекта",
        "клиент": "Работа с клиентами",
        "интеграц": "Интеграция с системами",
        "монетизац": "Монетизация",
    }

    mentioned_themes = []
    for keyword, theme in themes.items():
        if keyword.lower() in all_text.lower():
            mentioned_themes.append(theme)

    def clean_text(text: str) -> str:
        """Clean markdown and formatting artifacts from text."""
        # Remove markdown bold markers
        text = re.sub(r'\*\*', '', text)
        # Remove markdown headers
        text = re.sub(r'^#+\s*', '', text)
        # Remove colon prefixes (including various formats)
        text = re.sub(r'^:\s*\*\*\s*', '', text)
        text = re.sub(r'^:\s*', '', text)
        # Clean up extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    # Generate takeaways based on winner and themes
    if winner == "CON":
        takeaways.append(f"Победа CON: выявлены критические проблемы в {mentioned_themes[0] if mentioned_themes else 'проекте'}")

        # Add specific concerns from CON arguments
        if con_messages:
            for msg in con_messages[:2]:
                content = clean_text(msg.get("content", ""))
                if len(content) > 100:
                    # Extract first meaningful sentence
                    sentences = re.split(r'[.!?\n]', content)
                    for sent in sentences:
                        sent = sent.strip()
                        if 40 < len(sent) < 200:
                            takeaways.append(f"CON: {sent}")
                            break
    else:
        takeaways.append(f"Победа PRO: {mentioned_themes[0] if mentioned_themes else 'Проект'} признан достаточно проработанным")

        # Add positive points from PRO arguments
        if pro_messages:
            for msg in pro_messages[:2]:
                content = clean_text(msg.get("content", ""))
                if len(content) > 100:
                    sentences = re.split(r'[.!?\n]', content)
                    for sent in sentences:
                        sent = sent.strip()
                        if 40 < len(sent) < 200:
                            takeaways.append(f"PRO: {sent}")
                            break

    # Add themes that were mentioned
    for theme in mentioned_themes[:3]:
        if theme not in str(takeaways):
            takeaways.append(f"Обсуждена тема: {theme}")

    # Add verdict insight
    if explanation and len(explanation) > 30:
        # Clean explanation
        clean_exp = clean_text(explanation)
        if len(clean_exp) > 200:
            # Try to truncate at sentence boundary
            for sep in ['.', '!', ',']:
                idx = clean_exp.rfind(sep, 150, 200)
                if idx > 150:
                    clean_exp = clean_exp[:idx + 1]
                    break
            else:
                clean_exp = clean_exp[:197] + "..."
        takeaways.append(f"Вердикт судьи: {clean_exp}")

    # Ensure min/max limits
    while len(takeaways) < config.min_takeaways:
        if mentioned_themes:
            theme_idx = len(takeaways) % len(mentioned_themes)
            takeaways.append(f"Требуется анализ: {mentioned_themes[theme_idx]}")
        else:
            takeaways.append("Требуется дополнительный анализ аспектов проекта")

    return takeaways[:config.max_takeaways]


async def main():
    """Main entry point."""
    args = parse_arguments()

    dialogue_path = Path(args.dialogue_path)

    if not dialogue_path.exists():
        logger.error(f"File not found: {dialogue_path}")
        return 1

    # Default question
    question = args.question or "Анализ документа продукта комитета"

    # Configure analyzer
    config = TakeawayConfig(
        min_takeaways=args.min,
        max_takeaways=args.max,
        model=args.model,
    )

    # Process the file
    takeaways = await process_dialogue_file(
        dialogue_path,
        question,
        config,
        use_mock=args.mock
    )

    if not takeaways:
        logger.warning("No takeaways generated")
        return 1

    logger.info(f"Generated {len(takeaways)} takeaways:")
    for i, takeaway in enumerate(takeaways, 1):
        print(f"{i}. {takeaway}")

    # Update the file if not dry run
    if not args.dry_run:
        try:
            # Load the original file
            content = dialogue_path.read_text(encoding='utf-8')
            dialogue_json = json.loads(content)

            # Update takeaways
            dialogue_json["takeaways"] = takeaways

            # Save back
            dialogue_path.write_text(
                json.dumps(dialogue_json, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info(f"Updated {dialogue_path} with {len(takeaways)} takeaways")
        except Exception as e:
            logger.error(f"Failed to update file: {e}")
            return 1
    else:
        logger.info("Dry run - file not modified")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
