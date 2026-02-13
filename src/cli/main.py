import argparse
import asyncio
import logging
from logger import getLogger
from workflow.debate.document_debate_workflow import DocumentDebateWorkflow


logger = getLogger(__name__)


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

    try:
        logger.info("[bold green]Starting document debate workflow...[/]")

        # Parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--docx", required=True, help="Path to .docx file for debate analysis")

        args = parser.parse_args()

        # Read .docx file and extract text
        try:
            from docx import Document
            doc = Document(args.docx)
            doc_text = "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            logger.error(f"❌ Error reading .docx file: {args.docx}")
            raise RuntimeError(f"Failed to read .docx file: {args.docx}")

        # Run document debate workflow
        workflow = DocumentDebateWorkflow()
        workflow_result = await workflow.run(initial_state={"document_input": doc_text})

        # Display final verdict
        final_message = workflow_result["messages"][-1]["content"]
        logger.info("\n[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        if "WINNER: PRO" in final_message:
            logger.info("[cyan]  %s[/]", final_message.replace("WINNER: PRO", "🏆 [bold]WINNER:[/] [cyan]PRO"))
        elif "WINNER: CON" in final_message:
            logger.info("[magenta]  %s[/]", final_message.replace("WINNER: CON", "🏆 [bold]WINNER:[/] [magenta]CON"))
        else:
            logger.info("[yellow]  %s[/]", final_message)

        logger.info("[bold green]Workflow completed successfully | Status: [bold]SUCCESS[/][/]")
        logger.info("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")

    except Exception as e:
        logger.error(f"Workflow failed: %s", str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
