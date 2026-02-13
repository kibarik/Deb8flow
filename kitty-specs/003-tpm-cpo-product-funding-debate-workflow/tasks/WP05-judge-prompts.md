---
work_package_id: "WP05"
subtasks:
  - "T006"
title: "Judge Prompts"
phase: "Phase 1 - Design & Contracts"
lane: "planned"
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

# Work Package Prompt: WP05 – Judge Prompts

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: ```python, ```bash

---

## Objectives & Success Criteria

- Create funding decision judge prompt template
- Instruct judge to evaluate both TPM and CPO arguments
- Require binary decision (APPROVE/DENY) with reasoning

**Success Criteria**:
- [ ] `prompts/tpm_cpo_judge_prompts.py` created with VERDICT template
- [ ] Template includes placeholders for debate_topic, prd_input, debate_history
- [ ] Instructs judge to evaluate both sides fairly
- [ ] Requires binary decision with clear reasoning

## Context & Constraints

**Implementation Command**:
```bash
spec-kitty implement WP05
```

**Reference Documents**:
- [Judge Prompts Contract](../contracts/tpm_cpo_judge_prompts.py.md) - Prompt specification
- [Quickstart](../quickstart.md) - Verdict criteria examples
- [Existing judge_prompts.py](../../../../prompts/judge_prompts.py) - Reference for similar implementation

**Architectural Decisions**:
- Follow same pattern as `judge_prompts.py` from existing codebase
- Separate prompts file for TPM-CPO judge (different criteria than general debates)
- Focus on business value assessment (not rhetorical performance)

**Constraints**:
- Must require binary decision: APPROVE or DENY
- Must require reasoning explanation (2-4 paragraphs)
- Must evaluate both TPM's advocacy and CPO's skepticism

## Subtasks & Detailed Guidance

### Subtask T006 – Create Judge Prompts File

**Purpose**: Define prompt template for funding decision verdict.

**Steps**:
1. Create `prompts/tpm_cpo_judge_prompts.py`
2. Define `VERDICT_PROMPT_TEMPLATE`:
   - Role: Judge evaluating a product funding debate
   - Context: Project topic, PRD input, full debate transcript
   - Evaluation criteria:
     - TPM: Did they demonstrate market need, technical feasibility, business value?
     - CPO: Did they identify real risks, resource concerns, or completeness gaps?
     - Overall: If TPM made compelling case addressing CPO's concerns → Approve
     - Overall: If CPO identified critical gaps TPM couldn't address → Deny
   - Output format:
     - Funding Decision: [APPROVE | DENY]
     - Reasoning: [2-4 paragraphs explaining decision]
3. Include placeholders: `{debate_topic}`, `{prd_input}`, `{debate_history}`
4. Instruct judge to reference specific arguments from debate in reasoning

**Files**: `prompts/tpm_cpo_judge_prompts.py` (create, ~60 lines)

**Parallel?**: Can proceed alongside WP02, WP03, WP04

**Notes**:
- Judge prompt is business-focused (not rhetorical evaluation)
- Must require explicit decision (not implicit)
- Reasoning should reference specific debate points
- This is a new prompts file (not modifying existing `judge_prompts.py`)

## Test Strategy

**Manual Testing** (tests not auto-generated):
1. Create mock debate with TPM advocating strongly, CPO with weak concerns
   - Verify verdict would be APPROVE
2. Create mock debate with CPO identifying critical gaps
   - Verify verdict would be DENY
3. Create mock debate with balanced arguments
   - Verify decision is not biased toward either side

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Judge biased toward TPM (always Approves) | Medium | Explicitly instruct to evaluate both sides fairly |
| Judge biased toward CPO (always Denies) | Medium | Require clear criteria for both Approve/Deny |
| Verdict lacks reasoning | Low | Require 2-4 paragraphs in prompt |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] `tpm_cpo_judge_prompts.py` created with VERDICT template
- [ ] Template requires binary decision (APPROVE/DENY)
- [ ] Template requires reasoning explanation
- [ ] Template includes all required placeholders
- [ ] Template instructs evaluation of both TPM and CPO
- [ ] Template specifies decision criteria clearly

**Review Context**:
- Compare with `judge_prompts.py` for tone and structure
- Verify business focus (not rhetorical)
- Check placeholders match contract specification

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP05 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
