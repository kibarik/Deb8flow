---
work_package_id: WP06
title: StandardDebateOrchestrator Restoration
lane: "for_review"
dependencies: []
base_branch: main
base_commit: a4889d6c286d6fcba56d3823e23a6e8ed4e7239f
created_at: '2026-02-19T07:15:17.471721+00:00'
subtasks: [T031, T032, T033, T034, T035, T036]
shell_pid: "79455"
agent: "claude"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP06: StandardDebateOrchestrator Restoration

## Objective

Restore and upgrade the `StandardDebateOrchestrator` (multi-turn interactive debates) with separate LLM calls per stage. This enables deeper, more iterative debates compared to SimpleDebateOrchestrator.

## Context

The current `SimpleDebateOrchestrator` generates the entire debate in a single LLM call. While efficient, this limits depth and nuance.

We need to restore `StandardDebateOrchestrator` (or enhance `LLMDebateOrchestrator`) to:
- Execute each stage as a separate LLM call
- Allow each stage to build on full conversation history
- Support longer, more iterative exchanges
- Enable more nuanced judge evaluation

**Key differences from SimpleDebateOrchestrator:**
| Aspect | Simple Mode | Standard Mode |
|--------|-------------|---------------|
| API calls | 1 per debate | 9 per debate (8 stages + judge) |
| Conversation depth | Limited | Full context accumulated |
| Argument quality | Good | Better (more iterative) |
| Cost | Lower | Higher |
| Speed | Faster | Slower |

## Implementation Guidance

### T031: Create StandardDebateOrchestrator Class

**Purpose:** Create the multi-turn orchestrator with proper architecture.

**Steps:**

1. Create `src/shared/debate/infrastructure/llm/standard_orchestrator.py`:
   ```python
   """
   Standard Debate Orchestrator - Multi-turn interactive debates.

   This orchestrator executes each debate stage as a separate LLM call,
   allowing for deeper, more iterative exchanges than SimpleDebateOrchestrator.
   """

   import asyncio
   import logging
   from typing import List, Dict, Any, Optional, Tuple
   from datetime import datetime, timezone

   from langchain_openai import ChatOpenAI
   from langchain_core.messages import HumanMessage, SystemMessage

   from ..application.prompt_loader import PromptLoader, PromptContext
   from ..domain.entities import DebateMessage


   logger = logging.getLogger(__name__)


   class StandardDebateOrchestrator:
       """
       Multi-turn debate orchestrator with separate LLM calls per stage.

       This orchestrator provides higher quality debates by:
       - Executing each stage independently
       - Accumulating full conversation context
       - Allowing each response to build on all previous exchanges
       - Providing richer context to the judge

       Trade-offs:
       - More API calls (9 vs 1 per debate)
       - Slower execution time
       - Higher cost
       - Better debate quality and depth
       """

       def __init__(
           self,
           prompt_loader: PromptLoader,
           model: Optional[str] = None,
           temperature: float = 0.7,
           max_tokens: int = 1200,  # Lower per response, more responses
           api_key: Optional[str] = None,
           base_url: Optional[str] = None,
           language: str = "en"
       ):
           """Initialize the standard debate orchestrator."""
           self.prompt_loader = prompt_loader
           self.model = model or "gpt-4o"
           self.temperature = temperature
           self.max_tokens = max_tokens
           self.language = language

           # Initialize LLM
           llm_kwargs = {
               "model": self.model,
               "temperature": temperature,
               "max_tokens": max_tokens,
           }

           if api_key:
               llm_kwargs["api_key"] = api_key
           if base_url:
               llm_kwargs["base_url"] = base_url

           self.llm = ChatOpenAI(**llm_kwargs)

           # Debate state
           self.messages: List[DebateMessage] = []
           self.current_question: str = ""
           self.current_topic: str = ""
           self.current_prd: str = ""

       async def execute_debate(
           self,
           topic: str,
           pro_prompt: str,
           con_prompt: str,
           question: str,
           prd_content: str
       ) -> Tuple[List[Dict[str, Any]], str]:
           """
           Execute a full debate with separate LLM calls per stage.

           Args:
               topic: The debate topic/context
               pro_prompt: System prompt for PRO debater
               con_prompt: System prompt for CON debater
               question: The specific question to debate
               prd_content: Full PRD content for context

           Returns:
               Tuple of (dialogue as list of dicts, winner)
           """
           # Initialize state
           self.messages = []
           self.current_question = question
           self.current_topic = topic
           self.current_prd = prd_content

           try:
               # Execute each stage
               await self._execute_stage("opening_pro", pro_prompt, "PRO")
               await self._execute_stage("opening_con", con_prompt, "CON")
               await self._execute_stage("rebuttal_con", con_prompt, "CON")
               await self._execute_stage("rebuttal_pro", pro_prompt, "PRO")
               await self._execute_stage("counter_pro", pro_prompt, "PRO")
               await self._execute_stage("counter_con", con_prompt, "CON")
               await self._execute_stage("final_pro", pro_prompt, "PRO")
               await self._execute_stage("final_con", con_prompt, "CON")

               # Judge verdict
               winner = await self._execute_judge()

               return [msg.to_dict() for msg in self.messages], winner

           except Exception as e:
               logger.error(f"Standard debate execution failed: {e}")
               raise

       async def _execute_stage(
           self,
           stage_prompt_id: str,
           role_prompt: str,
           speaker: str
       ) -> None:
           """
           Execute a single debate stage.

           Args:
               stage_prompt_id: Prompt ID for this stage (e.g., "debate.stages.opening_pro")
               role_prompt: System prompt for the speaker's role
               speaker: "PRO" or "CON"
           """
           # Build context with full conversation history
           context = self._build_context_for_stage(speaker)

           # Load stage prompt
           stage_prompt = self.prompt_loader.load_with_context(
               f"debate.stages.{stage_prompt_id}",
               context
           )

           # Generate response
           response = await self._generate_response(
               system_prompt=role_prompt,
               human_prompt=stage_prompt,
               speaker=speaker
           )

           # Store message
           stage_name = stage_prompt_id.split("_")[0]  # "opening", "rebuttal", etc.
           self.messages.append(DebateMessage(
               speaker=speaker,
               content=response,
               stage=stage_name,
               timestamp=datetime.now(timezone.utc).isoformat(),
               validated=True
           ))

           logger.debug(f"{speaker} ({stage_name}): {response[:100]}...")

       async def _execute_judge(self) -> str:
           """Execute the judge's verdict stage."""
           # Build full context for judge
           context = self._build_context_for_stage("JUDGE")

           # Load judge prompt
           judge_prompt = self.prompt_loader.load_with_context(
               "debate.judge",
               context
           )

           # Generate verdict
           verdict = await self._generate_response(
               system_prompt=judge_prompt,
               human_prompt="Based on the debate above, provide your verdict.",
               speaker="JUDGE"
           )

           self.messages.append(DebateMessage(
               speaker="JUDGE",
               content=verdict,
               stage="verdict",
               timestamp=datetime.now(timezone.utc).isoformat(),
               validated=True
           ))

           # Extract winner
           if "WINNER: PRO" in verdict.upper():
               return "PRO"
           elif "WINNER: CON" in verdict.upper():
               return "CON"
           else:
               return "PRO"  # Default

       def _build_context_for_stage(self, speaker: str) -> PromptContext:
           """
           Build context for a stage with full conversation history.

           In standard mode, we provide the ENTIRE conversation history,
           not just recent messages. This enables deeper, more contextual
           responses that reference earlier arguments.
           """
           # Build full conversation history
           conversation_parts = []
           for msg in self.messages:
               conversation_parts.append(
                   f"{msg.speaker} ({msg.stage}): {msg.content}"
               )

           full_history = "\n\n".join(conversation_parts)

           # Create context with all available information
           return PromptContext(
               question=self.current_question,
               topic=self.current_topic[:500],
               prd_content=self.current_prd[:2000],
               recent_context=full_history,  # FULL history, not just recent
               language=self.language,
               pro_prompt="",  # Not needed for stage prompts
               con_prompt=""
           )

       async def _generate_response(
           self,
           system_prompt: str,
           human_prompt: str,
           speaker: str
       ) -> str:
           """Generate a response using the LLM."""
           try:
               messages = [
                   SystemMessage(content=system_prompt),
                   HumanMessage(content=human_prompt)
               ]

               response = await asyncio.to_thread(
                   self.llm.invoke,
                   messages
               )

               return response.content.strip()

           except Exception as e:
               logger.error(f"Error generating response for {speaker}: {e}")
               raise
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/standard_orchestrator.py` (new, ~200 lines)

**Validation:**
- [ ] Class compiles without errors
- [ ] All 9 stages are executed (8 + judge)
- [ ] Full conversation history is maintained
- [ ] PromptLoader is used for all prompts
- [ ] Stage naming is consistent

---

### T032-T036: Remaining Tasks

**T032: Implement Stage-by-Stage Execution** - Already done in T031
**T033: Add Conversation State Management** - Already done in T031
**T034: Implement Enhanced Context Building** - Already done in T031
**T035: Add Retry Logic** - Add retry logic for failed stages

**T035: Add Retry Logic:**
```python
from ..infrastructure.retry import retry_with_backoff

async def _execute_stage_with_retry(self, stage_id, role_prompt, speaker, max_retries=2):
    """Execute a stage with retry logic."""
    async def _once():
        await self._execute_stage(stage_id, role_prompt, speaker)

    try:
        await retry_with_backoff(_once, max_retries)
    except Exception as e:
        logger.error(f"Stage {stage_id} failed after retries: {e}")
        # Continue debate if possible
```

**T036: Create Integration Tests:**
```python
@pytest.mark.integration
async def test_standard_vs_simple_debate_quality():
    """Compare output quality between standard and simple modes."""
    # Run both modes on same input
    # Compare: word count, argument diversity, depth
    # Expect: standard mode > simple mode
```

---

## Definition of Done

- [ ] StandardDebateOrchestrator class exists
- [ ] Executes 9 separate LLM calls per debate
- [ ] Maintains full conversation history
- [ ] Uses PromptLoader for all prompts
- [ ] Retry logic is implemented
- [ ] Integration tests compare modes
- [ ] Documentation explains trade-offs

---

## Reviewer Guidance

**Check these specific items:**
1. All 9 stages are executed
2. Full history is passed to each stage
3. Context building uses full history, not recent
4. Retry logic doesn't break debate flow
5. Tests compare mode quality
6. Performance/cost implications are documented

**Files to Review:**
- `src/shared/debate/infrastructure/llm/standard_orchestrator.py`
- `tests/integration/test_standard_orchestrator.py`

## Activity Log

- 2026-02-19T07:16:27Z – claude – shell_pid=79455 – lane=for_review – Moved to for_review
