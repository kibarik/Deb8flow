import asyncio
import argparse
import sys
from workflow.debate_workflow import DebateWorkflow
import os
import logging
from rich.console import Console
from rich.logging import RichHandler

def setup_logging():
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
    required_var = "OPENAI_API_KEY"
    if not os.getenv(required_var):
        raise EnvironmentError(f"Missing environment variable: {required_var}")

async def main():
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Run an AI debate between PRO and CON agents"
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Language and style setting for all agents (e.g., 'Русский официальный стиль', 'English, concise')"
    )
    args = parser.parse_args()

    # Prepare language setting
    language_setting = None
    if args.language:
        if len(args.language) > 500:
            logger.error("❌ --language value too long (max 500 characters)")
            sys.exit(1)
        language_setting = args.language if args.language.strip() else None
        if language_setting:
            logger.info(f"[cyan]🌐 Language setting: {language_setting}[/]")

    try:
        logger.info("[bold green]Starting debate workflow...[/]")
        workflow = DebateWorkflow()

        # Pass language_setting to initial state
        initial_state = {"language_setting": language_setting}
        workflow_result = await workflow.run(initial_state=initial_state)

        final_message = workflow_result["messages"][-1]["content"]
        logger.info("\n[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        if "WINNER: PRO" in final_message:
            logger.info("[bold green]  DEBATE VERDICT[/]")
            logger.info("[cyan]  %s[/]", final_message.replace("WINNER: PRO", "🏆 [bold]WINNER:[/] [cyan]PRO"))
        elif "WINNER: CON" in final_message:
            logger.info("[bold green]  DEBATE VERDICT[/]")
            logger.info("[magenta]  %s[/]", final_message.replace("WINNER: CON", "🏆 [bold]WINNER:[/] [magenta]CON"))
        else:
            logger.info("[yellow]  %s[/]", final_message)
        logger.info("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")
        logger.info("[green]Workflow completed successfully | Status: [bold]SUCCESS[/][/]")

    except Exception as e:
        logger.error("Workflow failed: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
