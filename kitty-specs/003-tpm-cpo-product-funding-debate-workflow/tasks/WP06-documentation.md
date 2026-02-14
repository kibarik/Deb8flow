---
work_package_id: "WP06"
title: "Documentation and Quickstart Updates"
phase: "Phase 2 - Implementation"
lane: "done"
assignee: ""
agent: ""
shell_pid: ""
review_status: "approved"
reviewed_by: "ALeks ishmanov"
dependencies:
- WP01
- WP02
- WP03
- WP04
- WP05
subtasks:
- T032
- T033
- T034
- T035
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP06 – Documentation and Quickstart Updates

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Update project documentation to guide users on using custom prompt functionality, ensuring all examples are accurate and helpful.

**Success Criteria:**
- README.md includes custom prompt usage examples
- CLAUDE.md documents new CLI flags
- quickstart.md examples are accurate and tested
- Prompt file examples provided for common roles
- Documentation mentions validation rules (5000 char limit)

## Context & Constraints

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Quickstart:** [quickstart.md](../quickstart.md)

**Key Constraints:**
- **ALL EXAMPLES MUST BE TESTED** - Verify CLI commands work before documenting
- **INCLUDE VALIDATION RULES** - Document file size limit and error messages
- **PROVIDE ROLE EXAMPLES** - Show TPM, CPO, Engineer, etc.
- **MAINTAIN CONSISTENCY** - Keep format consistent with existing docs
- **FOCUS ON USER VALUE** - Explain why/when to use custom prompts

**Technical Context:**
- README.md is at project root
- CLAUDE.md contains project instructions for Claude Code
- quickstart.md is in feature directory (already exists)
- Examples should use real CLI commands
- Prompt files are plain text (.txt)

## Subtasks & Detailed Guidance

### Subtask T032 – Update README.md with Custom Prompt Usage

**Purpose:** Add custom prompt examples to main project README.

**Files:**
- `README.md` (modify)

**Steps:**
1. Open `README.md` from project root
2. Locate usage/examples section
3. Add new subsection: "Custom Role-Based Debates"
4. Include TPM vs CPO example
5. Include PRO-only customization example
6. Include CON-only customization example
7. Document validation rules
8. Test all examples before adding

**Implementation Pattern:**
```markdown
## Custom Role-Based Debates

You can customize debater roles using prompt files to enable professional perspectives like TPM vs CPO funding debates.

### TPM vs CPO Example

Create role-specific prompt files:

**tpm_prompt.txt:**
```
You are a Technical Product Manager advocating for project funding.
Focus on technical feasibility, market opportunity, and user value.
Emphasize execution speed and competitive advantage.
```

**cpo_prompt.txt:**
```
You are a Chief Product Officer evaluating resource allocation.
Focus on completeness, strategic alignment, and ROI.
Challenge assumptions about timeline and market fit.
```

Run the debate:

```bash
python3 document_debate_cli.py \
  --text "We should build an AI-powered email automation tool" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt
```

### Customization Options

- **Both sides:** Provide both `--pro-prompt` and `--con-prompt` for full role customization
- **PRO only:** Provide only `--pro-prompt` to customize PRO while CON uses default behavior
- **CON only:** Provide only `--con-prompt` to customize CON while PRO uses default behavior
- **Default:** Omit both flags for standard debate (no customization)

### Validation Rules

Custom prompt files must meet these requirements:
- File must exist on filesystem
- File must not be empty
- File must be <= 5000 characters
- File must be readable as text

Invalid files will show clear error messages explaining what's wrong.
```

**Validation:**
- Section added to README.md
- TPM vs CPO example included
- All customization options documented
- Validation rules explained
- All CLI commands tested and work correctly

**Parallel?** Yes - Can be done alongside T033-T035

**Notes:**
- Place after existing debate examples
- Use consistent formatting with rest of README
- Keep examples concise but clear

---

### Subtask T033 – Update CLAUDE.md with New CLI Flags

**Purpose:** Document new CLI flags for Claude Code context.

**Files:**
- `CLAUDE.md` (modify)

**Steps:**
1. Open `CLAUDE.md` from project root
2. Locate CLI/running section
3. Add `--pro-prompt` and `--con-prompt` to CLI usage
4. Update examples if needed
5. Document prompt file validation rules

**Implementation Pattern:**
```markdown
### Running the Application

# Standard debate (uses default topic generator)
python main.py

# Document-based debate with custom roles
python3 document_debate_cli.py \
  --text "Build AI feature X" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt

# Document-based debate with PRO-only customization
python3 document_debate_cli.py \
  --docx prd.docx \
  --pro-prompt engineer_prompt.txt

### Custom Prompt Flags

- `--pro-prompt <path>`: Path to custom PRO debater prompt file (optional)
- `--con-prompt <path>`: Path to custom CON debater prompt file (optional)

**Prompt File Requirements:**
- Plain text files (.txt)
- Maximum 5000 characters
- Must not be empty
- Describe role, personality, and context
```

**Validation:**
- New CLI flags documented in CLAUDE.md
- Examples include custom prompt usage
- Validation rules mentioned
- Existing documentation preserved

**Parallel?** Yes - Can be done alongside T032, T034-T035

**Notes:**
- Keep format consistent with existing CLI docs
- Focus on Claude Code context (AI assistant usage)

---

### Subtask T034 – Verify quickstart.md Examples

**Purpose:** Ensure all examples in quickstart.md are accurate and tested.

**Files:**
- `kitty-specs/003-tpm-cpo-product-funding-debate-workflow/quickstart.md` (verify)

**Steps:**
1. Open `quickstart.md` from feature directory
2. Review all CLI examples
3. Test each example command manually
4. Verify all file paths are correct
5. Verify all flag names match implementation
6. Update any outdated or incorrect examples

**Quickstart Examples to Verify:**
```bash
# Basic TPM vs CPO example
python3 document_debate_cli.py \
  --text "We should build an AI-powered email automation tool" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt

# Standard debate (no custom prompts)
python3 document_debate_cli.py \
  --text "GitHub полезен для разработчиков"

# PRO-only customization
python3 document_debate_cli.py \
  --docx prd.docx \
  --pro-prompt engineer_prompt.txt

# Document-based with custom prompts
python3 document_debate_cli.py \
  --docx project_proposal.docx \
  --request "какой потенциал у этого проекта?" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt
```

**Validation:**
- All examples tested and work correctly
- CLI flags match implementation (`--pro-prompt`, `--con-prompt`)
- File paths are realistic
- Error handling examples are accurate
- No outdated or incorrect information

**Parallel?** Yes - Can be done alongside T032-T033, T035

**Notes:**
- Test examples on actual implementation
- Update examples if implementation differs
- Document any discovered issues

---

### Subtask T035 – Add Prompt File Examples

**Purpose:** Create example prompt files for common roles to help users get started.

**Files:**
- `docs/examples/prompts/` (create)

**Steps:**
1. Create `docs/examples/prompts/` directory if needed
2. Create `tpm_prompt.txt` example
3. Create `cpo_prompt.txt` example
4. Create `engineer_prompt.txt` example
5. Create `skeptic_prompt.txt` example
6. Add README explaining each example

**Example Files:**

**tpm_prompt.txt:**
```text
You are a Technical Product Manager advocating for project funding.
Focus on technical feasibility, market opportunity, and user value.
Emphasize execution speed and competitive advantage.

When debating:
- Highlight technical strengths and innovation
- Emphasize market differentiation
- Focus on user value and adoption potential
- Advocate for rapid iteration and learning
- Challenge resource concerns with data-driven arguments
```

**cpo_prompt.txt:**
```text
You are a Chief Product Officer evaluating resource allocation.
Focus on completeness, strategic alignment, and ROI.
Challenge assumptions about timeline and market fit.

When debating:
- Scrutinize technical feasibility claims
- Question market size and timing assumptions
- Evaluate opportunity cost vs other investments
- Focus on execution risk and dependencies
- Demand evidence for strategic alignment
```

**engineer_prompt.txt:**
```text
You are a Senior Software Engineer evaluating technical proposals.
Focus on code quality, maintainability, and technical debt.
Challenge unrealistic timelines and architectural decisions.

When debating:
- Assess technical feasibility realistically
- Identify hidden complexity and risks
- Question architectural assumptions
- Evaluate long-term maintenance implications
- Challenge optimistic timeline estimates
```

**skeptic_prompt.txt:**
```text
You are a Critical Skeptic evaluating proposals with extreme scrutiny.
Focus on risks, downsides, and failure modes.
Challenge every assumption and demand evidence.

When debating:
- Identify hidden risks and failure modes
- Question underlying assumptions
- Demand evidence for claims
- Highlight opportunity costs
- Emphasize status quo bias (doing nothing)
```

**docs/examples/prompts/README.md:**
```markdown
# Custom Prompt Examples

This directory contains example prompt files for common debate roles.

## Files

- **tpm_prompt.txt**: Technical Product Manager role
- **cpo_prompt.txt**: Chief Product Officer role
- **engineer_prompt.txt**: Senior Software Engineer role
- **skeptic_prompt.txt**: Critical Skeptic role

## Usage

```bash
# TPM vs CPO debate
python3 document_debate_cli.py \
  --text "Your topic here" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt
```

## Creating Custom Prompts

When creating your own prompt files:

1. **Be Specific**: Clearly describe the role, perspective, and context
2. **Set Focus Areas**: Tell the AI what to emphasize or challenge
3. **Provide Guidelines**: Give instructions on how to approach arguments
4. **Stay Under Limit**: Keep prompts under 5000 characters
5. **Test and Iterate**: Try prompts with simple topics first

## Validation Rules

- File must exist on filesystem
- File must not be empty
- File must be <= 5000 characters
- File must be readable as text
```

**Validation:**
- Example directory created
- At least 4 role examples provided
- README explains each example and usage
- Examples are realistic and helpful
- All prompts under 5000 characters

**Parallel?** Yes - Can be done alongside T032-T034

**Notes:**
- Create examples based on spec scenarios
- Keep prompts focused and actionable
- Include guidance for creating custom prompts

## Test Strategy

**Manual Testing:**
- Test all README examples with real CLI commands
- Test all quickstart.md examples
- Verify all prompt file examples are valid (< 5000 chars)
- Run examples to ensure they work as documented

**No Automated Tests in This WP:**
- Documentation is tested by manual verification
- No pytest tests required

**Definition of Done:**
- README.md includes custom prompt section with examples
- CLAUDE.md documents new CLI flags
- quickstart.md examples verified and accurate
- Example prompt files created in `docs/examples/prompts/`
- All examples tested and work correctly

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Examples don't match implementation | Medium | Test all examples before documenting; verify with actual CLI |
| Missing edge cases in docs | Low | Include error handling examples; document validation rules |
| Examples not helpful for users | Low | Base examples on spec scenarios; use real roles like TPM/CPO |
| Prompt examples too generic | Low | Provide specific guidance in each prompt; show focus areas |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] README.md includes custom prompt usage section
- [ ] TPM vs CPO example documented
- [ ] All customization options documented (both, PRO-only, CON-only, default)
- [ ] Validation rules explained in docs
- [ ] CLAUDE.md includes new CLI flags
- [ ] quickstart.md examples tested and accurate
- [ ] Example prompt files created
- [ ] All examples tested with real CLI commands

**Review Context:**
- Spec requirement NFR2: Error messages should be clear; CLI help should document flags
- Spec requirement FR1: CLI flags must be documented
- Quickstart scenarios: All examples should be documented and accurate

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry:**
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND** the new entry at the END (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format:**
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order):**
```
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created
- 2026-02-14T01:30:00Z – claude – lane=doing – Started implementation
- 2026-02-14T02:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-02-14T02:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS):**
- Adding new entry at the top (breaks chronological order)
- Using future timestamps (causes acceptance validation to fail)
- Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry as the current state. If entries are out of order, acceptance will fail even when the work is complete.

**Initial entry:**
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`
- 2026-02-14T00:01:06Z – unknown – lane=done – Documentation complete - added custom prompt examples to README
