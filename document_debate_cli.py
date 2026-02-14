"""
Document Debate CLI - Command-line interface for document-based AI debates.

This module provides a CLI for running document-based debates using the
DocumentDebateWorkflow. It accepts .docx files as input and generates
debate topics and arguments based on the document content.
"""

import argparse
import asyncio
import logging
import os
import sys
from docx import Document
from rich.console import Console
from rich.logging import RichHandler
from workflow.document_debate_workflow import DocumentDebateWorkflow


logger = logging.getLogger(__name__)


def setup_logging():
    """Configure rich logging for the CLI."""
    console = Console(width=100)
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_level=True,
                markup=True,
                show_path=False
            )
        ]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def validate_env():
    """Validate that required environment variables are set."""
    required_var = "OPENAI_API_KEY"
    if not os.getenv(required_var):
        raise EnvironmentError(f"Missing environment variable: {required_var}")


def read_docx_file(file_path: str) -> str:
    """
    Extract text content from a .docx file.

    Args:
        file_path: Path to the .docx file

    Returns:
        Extracted text content

    Raises:
        RuntimeError: If file cannot be read
    """
    try:
        doc = Document(file_path)
        doc_text = "\n".join(p.text for p in doc.paragraphs)
        return doc_text
    except Exception as e:
        raise RuntimeError(f"Failed to read .docx file: {file_path}") from e


def validate_prompt_file(file_path: str) -> tuple[bool, str]:
    """
    Validate custom prompt file exists, is non-empty, and within size limits.

    Args:
        file_path: Path to prompt file

    Returns:
        Tuple of (is_valid, content_or_error_message)
    """
    # Check file exists
    if not os.path.exists(file_path):
        return False, f"Prompt file not found: {file_path}"

    # Check file not empty
    if os.path.getsize(file_path) == 0:
        return False, f"Prompt file is empty: {file_path}"

    # Check file size <= 5000 chars
    with open(file_path, 'r') as f:
        content = f.read()
        if len(content) > 5000:
            return False, f"Prompt file too large (max 5000 characters): {file_path}"

    return True, content


async def main():
    """Main entry point for the document debate CLI."""
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")

    try:
        logger.info("[bold green]Starting document debate workflow...[/]")

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run an AI debate based on a document"
        )
        parser.add_argument(
            "--docx",
            help="Path to .docx file for context (required with --request)"
        )
        parser.add_argument(
            "--text",
            help="Direct topic input (alternative to --docx)"
        )
        parser.add_argument(
            "--request",
            help="Debate topic/question (required when using --docx)"
        )
        parser.add_argument(
            "--pro-prompt",
            type=str,
            help="Path to custom PRO debater prompt file"
        )
        parser.add_argument(
            "--con-prompt",
            type=str,
            help="Path to custom CON debater prompt file"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed prompt content for verification"
        )

        args = parser.parse_args()

        # Validate argument combinations
        if args.request and not args.docx:
            logger.error("❌ --request requires --docx to provide document context")
            sys.exit(1)

        # Get document text from file or direct input
        # Base state with required fields for DebateState TypedDict
        base_state = {
            "debate_topic": "",
            "positions": {},
            "messages": []
        }

        # Validate and add custom prompts if provided
        if args.pro_prompt:
            is_valid, result = validate_prompt_file(args.pro_prompt)
            if not is_valid:
                logger.error(f"❌ {result}")
                sys.exit(1)
            base_state["pro_custom_prompt"] = result
            logger.info(f"[cyan]✓ Loaded PRO custom prompt from: {args.pro_prompt}[/]")
            if args.verbose:
                logger.info(f"[cyan]└─ Content ({len(result)} chars):[/]\n{result}\n")

        if args.con_prompt:
            is_valid, result = validate_prompt_file(args.con_prompt)
            if not is_valid:
                logger.error(f"❌ {result}")
                sys.exit(1)
            base_state["con_custom_prompt"] = result
            logger.info(f"[magenta]✓ Loaded CON custom prompt from: {args.con_prompt}[/]")
            if args.verbose:
                logger.info(f"[magenta]└─ Content ({len(result)} chars):[/]\n{result}\n")

        if args.docx:
            try:
                doc_text = read_docx_file(args.docx)
                logger.info(f"[cyan]📄 Loaded document: {args.docx}[/]")
                # Validate document content
                if not doc_text or not doc_text.strip():
                    logger.error("❌ Document is empty or contains no readable text")
                    sys.exit(1)

                if args.request:
                    # --docx with --request: document is context, request is topic
                    logger.info(f"[cyan]📋 Debate topic: {args.request}[/]")
                    base_state["direct_topic"] = args.request
                    base_state["document_context"] = doc_text
                    initial_state = base_state
                else:
                    # --docx only: old behavior - generate topic from document
                    logger.info("[yellow]⚠️ No --request provided, will generate topic from document[/]")
                    base_state["document_input"] = doc_text
                    initial_state = base_state
            except Exception as e:
                logger.error(f"❌ Error reading .docx file: {args.docx}")
                raise
        elif args.text:
            if args.request:
                logger.error("❌ --request can only be used with --docx, not --text")
                sys.exit(1)
            doc_text = args.text
            logger.info("[cyan]📄 Using direct topic input[/]")
            # Validate topic content
            if not doc_text or not doc_text.strip():
                logger.error("❌ Topic cannot be empty")
                sys.exit(1)
            # Use direct_topic to skip topic generation
            base_state["direct_topic"] = doc_text
            initial_state = base_state
        else:
            logger.error("❌ Either --docx or --text must be provided")
            parser.print_help()
            sys.exit(1)

        # Run document debate workflow
        workflow = DocumentDebateWorkflow()
        workflow_result = await workflow.run(initial_state=initial_state)

        # Display final verdict
        if "messages" in workflow_result and workflow_result["messages"]:
            final_message = workflow_result["messages"][-1]["content"]
            logger.info("\n[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
            if "WINNER: PRO" in final_message:
                logger.info("[cyan]  %s[/]", final_message.replace("WINNER: PRO", "🏆 [bold]WINNER:[/] [cyan]PRO"))
            elif "WINNER: CON" in final_message:
                logger.info("[magenta]  %s[/]", final_message.replace("WINNER: CON", "🏆 [bold]WINNER:[/] [magenta]CON"))
            else:
                logger.info("[yellow]  %s[/]", final_message)

            logger.info("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")

        logger.info("[bold green]Workflow completed successfully | Status: [bold]SUCCESS[/][/]")
        logger.info("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")

    except Exception as e:
        logger.error(f"Workflow failed: %s", str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
