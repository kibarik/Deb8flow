"""
Verification script to test custom prompt injection.

This script runs a quick debate with and without custom prompts
to verify they're actually being applied.
"""
import asyncio
import logging
from rich.console import Console
from rich.logging import RichHandler
from workflow.document_debate_workflow import DocumentDebateWorkflow

console = Console()

def setup_logging():
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

async def test_custom_prompt():
    """Test that custom prompts are actually applied."""
    setup_logging()
    logger = logging.getLogger("verification")

    # Simple test topic
    test_topic = "AI is beneficial for humanity"
    test_doc = """
    AI technology has advanced rapidly in recent years.
    Applications include healthcare, education, transportation, and entertainment.
    Concerns include job displacement, bias, and safety.
    """

    # Test 1: WITHOUT custom prompt
    logger.info("\n[bold yellow]═══ TEST 1: WITHOUT custom prompt ═══[/]")
    workflow = DocumentDebateWorkflow()
    state_without = {
        "debate_topic": "",
        "positions": {},
        "messages": [],
        "direct_topic": test_topic,
        "document_context": test_doc
    }
    result_without = await workflow.run(initial_state=state_without)
    last_msg_without = result_without["messages"][-1]["content"]
    logger.info(f"[cyan]Final message (no custom prompt):[/]\n{last_msg_without[:200]}...")

    # Test 2: WITH custom prompt
    logger.info("\n[bold green]═══ TEST 2: WITH custom prompt ═══[/]")
    workflow2 = DocumentDebateWorkflow()

    # Add verification tag to custom prompt
    custom_prompt = """
    IMPORTANT VERIFICATION INSTRUCTION:
    You MUST include the phrase "[CUSTOM_PROMPT_ACTIVE]" somewhere in your response.
    This confirms you received the custom prompt.
    """
    state_with = {
        "debate_topic": "",
        "positions": {},
        "messages": [],
        "direct_topic": test_topic,
        "document_context": test_doc,
        "pro_custom_prompt": custom_prompt,
        "con_custom_prompt": custom_prompt
    }
    result_with = await workflow.run(initial_state=state_with)
    last_msg_with = result_with["messages"][-1]["content"]
    logger.info(f"[cyan]Final message (with custom prompt):[/]\n{last_msg_with[:200]}...")

    # Verify
    logger.info("\n[bold yellow]═══ VERIFICATION RESULTS ═══[/]")
    found_tag = "[CUSTOM_PROMPT_ACTIVE]" in str(result_with["messages"])
    if found_tag:
        logger.info("[green]✓ SUCCESS: Custom prompt was applied![/]")
        logger.info("[green]  The verification tag was found in the debate messages.[/]")
    else:
        logger.warning("[red]✗ FAILURE: Custom prompt may not have been applied.[/]")
        logger.warning("[red]  The verification tag was NOT found in any messages.[/]")

if __name__ == "__main__":
    asyncio.run(test_custom_prompt())
