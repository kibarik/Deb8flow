---
work_package_id: "WP04"
subtasks:
  - "T013"
  - "T014"
title: "Topic Generator"
phase: "Phase 1 - Design & Contracts"
lane: "planned"
dependencies: ["WP01"]
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2025-02-13T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP04 – Topic Generator

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add contact the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: ```python, ```bash

---

## Objectives & Success Criteria

- Implement topic generation node that extracts project proposal from PRD text
- Generate debatable topic questions in format: "Should [project description] receive funding and be launched?"
- Handle variable PRD lengths from short ideas to full specifications

**Success Criteria**:
- [ ] `nodes/tpm_cpo_topic_generator_node.py` created with TpmCpoTopicGeneratorNode class
- [ ] `generate_topic()` accepts PRD text, returns topic string
- [ ] Extracts core project concept from PRD input
- [ ] Formats topic as debatable question
- [ ] Handles long PRDs without exceeding token limits

## Context & Constraints

**Implementation Command**:
```bash
spec-kitty implement WP04 --base WP01
```

**Reference Documents**:
- [Data Model](../data-model.md) - State entity definitions
- [Topic Generator Contract](../contracts/tpm_cpo_topic_generator_node.py.md) - Interface specification
- [Quickstart](../quickstart.md) - Usage examples
- [BaseComponent](../../../../nodes/base_component.py) - Base class to inherit from
- [Existing topic_generator_node.py](../../../../nodes/topic_generator_node.py) - Reference for similar implementation

**Architectural Decisions**:
- Follow same pattern as `GenerateTopicNode` from existing codebase
- Use LLM to extract and format topic (not rule-based)
- No separate prompts file needed (simple prompt inline)

**Constraints**:
- Must inherit from `BaseComponent`
- Must use LLM from `requesty_llm_config_map["deepseek-chat"]`
- Topic format must match: "Should [description] receive funding and be launched?"

## Subtasks & Detailed Guidance

### Subtask T013 – Create Topic Generator Node Class

**Purpose**: Create the topic generation node class.

**Steps**:
1. Create `nodes/tpm_cpo_topic_generator_node.py`
2. Import `BaseComponent` from `.base_component`
3. Define `TpmCpoTopicGeneratorNode(BaseComponent)` class:
   ```python
   class TpmCpoTopicGeneratorNode(BaseComponent):
       def __init__(self, llm_config: dict):
           super().__init__(llm_config)
   ```
4. Add method signature: `def generate_topic(self, prd_text: str) -> str:` (empty for now)

**Files**: `nodes/tpm_cpo_topic_generator_node.py` (create, ~15 lines)

**Parallel?**: Can proceed alongside WP02, WP03

**Notes**:
- Follow exact pattern of `GenerateTopicNode` from existing codebase
- Method accepts raw PRD text (not state object)

### Subtask T014 – Implement generate_topic() Method

**Purpose**: Extract project concept from PRD and format as debatable topic.

**Steps**:
1. In `TpmCpoTopicGeneratorNode`, implement `generate_topic()` method
2. Create inline prompt instructing LLM to:
   - Extract core project concept: problem, solution, target market, value proposition
   - Format as debatable topic question
   - Target format: "Should [project description] receive funding and be launched?"
3. Call LLM with PRD text: `response = self.llm_client.generate(prompt)`
4. Extract topic from response (clean up any markdown/wrapper)
5. Return topic string

**Files**: `nodes/tpm_cpo_topic_generator_node.py` (modify, add ~30 lines)

**Parallel?**: Depends on T013

**Notes**:
- Handle edge cases: empty PRD text, very long PRDs
- For long PRDs (>50 pages), consider truncating with note: "[PRD truncated for topic extraction]"
- Topic should be concise (1-2 sentences) but capture core concept

## Test Strategy

**Manual Testing** (tests not auto-generated):
1. Test with short PRD (2 paragraphs):
   - Verify topic captures core concept
   - Verify format matches "Should X receive funding and be launched?"
2. Test with long PRD (20+ paragraphs):
   - Verify topic doesn't exceed token limits
   - Verify topic still meaningful (not generic)
3. Test with empty PRD:
   - Verify graceful handling (error or default topic)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Long PRDs exceed token limits | High | Truncate PRD text in prompt, add note |
| Topic too generic/meaningless | Medium | Prompt LLM to extract specific concept (not generic summary) |
| Topic format mismatch | Low | Explicitly specify target format in prompt |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] `TpmCpoTopicGeneratorNode` inherits from `BaseComponent`
- [ ] `generate_topic()` accepts prd_text: str, returns str
- [ ] Method uses LLM client from base class
- [ ] Topic format matches "Should [description] receive funding and be launched?"
- [ ] Handles edge cases (empty input, long PRDs)

**Review Context**:
- Compare with `GenerateTopicNode` implementation for consistency
- Verify topic format matches expected pattern
- Check PRD text is passed to LLM (not state object)

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP04 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
