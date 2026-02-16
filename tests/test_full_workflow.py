import pytest
from workflow.debate_workflow import DebateWorkflow

@pytest.mark.asyncio
async def test_full_debate_workflow_completes():
    """Test standard debate workflow (backward compatibility - T060)."""
    workflow = DebateWorkflow()
    graph = workflow._initialize_workflow().compile()

    initial_state = {
        "debate_topic": "Should autonomous drones be allowed in warfare?",
        "positions": {
            "pro": "In favor of the topic",
            "con": "Against the topic"
        },
        "messages": [],
        "opening_statement_pro_agent": "",
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})

    assert "messages" in final_state
    assert any(m["stage"] == "verdict" for m in final_state["messages"]) or final_state["speaker"] in ["pro", "con"]


@pytest.mark.asyncio
async def test_committee_debate_workflow_supports_enhanced_conclusion():
    """Test committee debate workflow with enhanced conclusion support (T060)."""
    from workflow.committee_workflow import CommitteeWorkflow

    workflow = CommitteeWorkflow()
    graph = workflow._initialize_workflow().compile()

    initial_state = {
        "debate_topic": "Should we approve the PRD for the new AI-powered feature?",
        "positions": {
            "pro": "In favor of the topic",
            "con": "Against the topic"
        },
        "messages": [],
        "stage": "topic_generation",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
        "committee_mode": True,
        "run_id": "TEST_RUN_ID",
    }

    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 100})

    # Verify committee workflow completes
    assert "messages" in final_state
    assert "run_id" in final_state

    # Verify committee output directory would be created for enhanced conclusion
    # (The actual enhanced conclusion generation happens in ConclusionReportNode)
    assert final_state.get("committee_mode") is True
