"""
Document Debate Workflow - LangGraph workflow for document-based debates.

This module extends the standard debate workflow to support document-based debates.
It uses DocumentTopicNode instead of GenerateTopicNode and passes document context
to debaters and judge for richer, evidence-based debates.
"""

from langgraph.graph import StateGraph, END
from debate_state import DebateState
from nodes.document_topic_node import DocumentTopicNode
from nodes.pro_debater_node import ProDebaterNode
from nodes.con_debater_node import ConDebaterNode
from nodes.debate_moderator_node import DebateModeratorNode
from nodes.fact_checker_node import FactCheckNode
from nodes.fact_check_router_node import FactCheckRouterNode
from nodes.judge_node import JudgeNode
from src.extractors.debate_state_extractor import DebateStateExtractor
from src.utils.conclusion_writer import ConclusionWriter
from nodes.conclusion_report_node import ConclusionReportNode
from nodes.conclusion_report_node import ConclusionReportNode
from src.extractors.debate_state_extractor import DebateStateExtractor
from src.utils.conclusion_writer import ConclusionWriter
from configurations.llm_config import requesty_llm_config_map


class DocumentDebateWorkflow:
    """
    Workflow for document-based AI debates.

    This workflow extends the standard debate workflow to support:
    - Document topic generation from .docx files
    - Document-aware debater prompts
    - Document viability assessment in judging

    Usage:
        workflow = DocumentDebateWorkflow()
        result = await workflow.run(initial_state={"document_input": doc_text})
    """

    def _initialize_workflow(self) -> StateGraph:
        """Initialize the LangGraph StateGraph with all nodes and edges."""
        workflow = StateGraph(DebateState)

        # Nodes - use DocumentTopicNode instead of GenerateTopicNode
        workflow.add_node("document_topic_node", DocumentTopicNode(requesty_llm_config_map["deepseek-chat"]))
        workflow.add_node("pro_debater_node", ProDebaterNode(requesty_llm_config_map["deepseek-chat"]))
        workflow.add_node("con_debater_node", ConDebaterNode(requesty_llm_config_map["deepseek-chat"]))
        workflow.add_node("fact_check_node", FactCheckNode())
        workflow.add_node("fact_check_router_node", FactCheckRouterNode())
        workflow.add_node("debate_moderator_node", DebateModeratorNode())
        workflow.add_node("judge_node", JudgeNode(requesty_llm_config_map["deepseek-chat"]))

        # Entry point - start with document topic generation
        workflow.set_entry_point("document_topic_node")

        # Flow - only PRO starts after topic generation
        workflow.add_edge("document_topic_node", "pro_debater_node")
        workflow.add_edge("pro_debater_node", "fact_check_node")
        workflow.add_edge("con_debater_node", "fact_check_node")
        workflow.add_edge("fact_check_node", "fact_check_router_node")
        # Note: fact_check_router_node uses Command(goto=...) for dynamic routing
        # No static edges needed from router - it routes to: pro/con/judge dynamically
        workflow.add_edge("judge_node", END)

        return workflow

    def _should_continue_debate(self, state: DebateState) -> str:
        """
        Determine whether the debate should continue or end.

        Args:
            state: Current debate state

        Returns:
            "continue" if debate should continue, "end" if debate should end
        """
        messages = state.get("messages", [])
        stage = state.get("stage", "opening")

        # End debate after final arguments
        if stage == "final_argument":
            return "end"

        # End debate if max rounds reached (e.g., 4 rounds per side)
        if len(messages) >= 8:
            return "end"

        return "continue"

    async def run(self, initial_state: dict = None):
        """
        Run the document debate workflow.

        Args:
            initial_state: Optional initial state dict. Must contain 'document_input'
                          if not using default empty state.

        Returns:
            Final debate state with messages and verdict

        Example:
            workflow = DocumentDebateWorkflow()
            result = await workflow.run(initial_state={
                "document_input": "path/to/document.docx"
            })
        """
        workflow = self._initialize_workflow()
        graph = workflow.compile()

        # Set default initial state if none provided
        if initial_state is None:
            initial_state = {
                "document_input": ""
            }

        final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
        return final_state
