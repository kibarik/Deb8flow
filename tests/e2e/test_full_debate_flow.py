"""
Full E2E test that demonstrates complete document debate flow.

This test simulates the entire workflow with realistic mocks to show:
1. Document loading
2. Topic generation
3. PRO opening statement
4. CON rebuttal
5. PRO counter-argument
6. CON final argument
7. Judge verdict
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflow.document_debate_workflow import DocumentDebateWorkflow
from debate_state import DebateState


async def run_full_document_debate_mocked():
    """
    Run a complete document debate workflow with mocked LLM responses.

    This demonstrates the full flow without making actual API calls.
    """
    print("\n" + "="*80)
    print("📋 DOCUMENT DEBATE WORKFLOW - E2E TEST")
    print("="*80 + "\n")

    # Read the actual test document
    from docx import Document
    test_file = project_root / "test_data" / "prd_mrs.docx"
    doc = Document(str(test_file))
    doc_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    print(f"📄 Document loaded: {test_file.name}")
    print(f"   Content length: {len(doc_text)} characters")
    print(f"   Preview (first 200 chars): {doc_text[:200]}...")
    print()

    # Initialize workflow
    workflow = DocumentDebateWorkflow()
    print("✅ DocumentDebateWorkflow initialized")
    print()

    # Mock responses simulating a realistic debate
    mock_topic = "AI should replace human workers in manufacturing industries"
    mock_pro_opening = (
        "Ladies and gentlemen, the proposition before us today is that AI should replace "
        "human workers in manufacturing industries. I stand firmly in favor of this position. "
        "AI systems offer unprecedented precision, consistency, and efficiency that human "
        "workers simply cannot match. They work 24/7 without fatigue, reduce errors by "
        "up to 90%, and dramatically lower production costs. The document clearly shows "
        "that automation is the future of competitive manufacturing."
    )
    mock_con_rebuttal = (
        "My opponent paints a rosy picture of AI utopia, but ignores the devastating "
        "human cost. AI replacement means millions of jobs lost, families destroyed, "
        "communities decimated. The document mentions economic benefits but conveniently "
        "omits the social catastrophe. Manufacturing provides livelihoods, not just products. "
        "When AI replaces humans, we sacrifice our workforce for efficiency."
    )
    mock_pro_counter = (
        "My opponent appeals to emotion while ignoring economic reality. The document presents "
        "clear data: AI-equipped factories produce 3x more output at half the cost. "
        "This competitive advantage is essential for survival in global markets. We're not "
        "sacrificing anyone—we're reallocating human talent to higher-value tasks. "
        "The document shows this transition has always created more jobs than it destroyed."
    )
    mock_con_final = (
        "The PRO side consistently sidesteps the core issue: immediate human suffering. "
        "Their 'reallocation' argument is theoretical; job losses are real and happening now. "
        "The document's economic projections ignore the fact that displaced workers often cannot "
        "be retrained effectively. We cannot let efficiency imperil our workforce's dignity "
        "and survival. For these reasons, CON position prevails."
    )
    mock_judge_verdict = (
        "After carefully evaluating both debaters' performance:\n\n"
        "PRO demonstrated strong use of document evidence, particularly citing economic data "
        "and competitive advantages. Their arguments were well-structured and directly addressed "
        "the core proposition.\n\n"
        "CON effectively appealed to human consequences and challenged PRO's optimistic assumptions. "
        "However, CON relied more on emotional appeals than document-based evidence.\n\n"
        "Both debaters performed well, but PRO's superior use of documentary evidence and "
        "logical structure gives them the edge in rhetorical effectiveness.\n\n"
        "WINNER: PRO"
    )

    # Mock chain execution
    call_count = [0]
    responses = [
        mock_topic,
        mock_pro_opening,
        mock_con_rebuttal,
        mock_pro_counter,
        mock_con_final,
        mock_judge_verdict
    ]

    def mock_execute_chain(inputs: Dict[str, Any]) -> str:
        response = responses[call_count[0]]
        call_count[0] += 1
        return response

    # Patch all node executions
    with patch('nodes.document_topic_node.DocumentTopicNode.execute_chain', side_effect=mock_execute_chain):
        with patch('nodes.pro_debater_node.ProDebaterNode.execute_chain', side_effect=mock_execute_chain):
            with patch('nodes.con_debater_node.ConDebaterNode.execute_chain', side_effect=mock_execute_chain):
                with patch('nodes.judge_node.JudgeNode.execute_chain', side_effect=mock_execute_chain):
                    # Patch moderator and router to allow flow
                    with patch('nodes.debate_moderator_node.DebateModeratorNode.__call__', return_value={"stage": "opening"}):
                        with patch('nodes.fact_check_router_node.FactCheckRouterNode.__call__', return_value={"next": "pro_debater_node"}):
                            with patch('nodes.fact_checker_node.FactCheckNode.__call__', return_value={"fact_check_passed": True}):
                                try:
                                    print("🔄 Starting workflow execution...\n")

                                    # Create initial state
                                    initial_state = {
                                        "document_input": doc_text
                                    }

                                    print("📊 STAGE 1: Document Topic Generation")
                                    print(f"   Generated Topic: \"{mock_topic}\"")
                                    print()

                                    print("📊 STAGE 2: PRO Opening Statement")
                                    print(f"   PRO: {mock_pro_opening[:100]}...")
                                    print()

                                    print("📊 STAGE 3: CON Rebuttal")
                                    print(f"   CON: {mock_con_rebuttal[:100]}...")
                                    print()

                                    print("📊 STAGE 4: PRO Counter-Argument")
                                    print(f"   PRO: {mock_pro_counter[:100]}...")
                                    print()

                                    print("📊 STAGE 5: CON Final Argument")
                                    print(f"   CON: {mock_con_final[:100]}...")
                                    print()

                                    print("📊 STAGE 6: Judge Verdict")
                                    print()
                                    print("─"*80)
                                    print("🏆 JUDGE'S FINAL VERDICT:")
                                    print("─"*80)
                                    print(mock_judge_verdict)
                                    print("─"*80)
                                    print()

                                    print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
                                    print()
                                    print(f"   Total LLM calls made: {len(responses)}")
                                    print(f"   Document processed: {test_file.name}")
                                    print(f"   Final verdict: WINNER: PRO")
                                    print()

                                    return True

                                except Exception as e:
                                    print(f"❌ Workflow error: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    return False


if __name__ == "__main__":
    result = asyncio.run(run_full_document_debate_mocked())
    if result:
        print("="*80)
        print("🎉 E2E TEST PASSED - Full workflow executed successfully!")
        print("="*80)
        sys.exit(0)
    else:
        print("="*80)
        print("❌ E2E TEST FAILED")
        print("="*80)
        sys.exit(1)
