---
work_package_id: WP01
title: Prompt Directory Structure and Initial Files
lane: "doing"
dependencies: []
base_branch: main
base_commit: fe5c2b96b94a8fe6063d6cb05668bf74e0e015f3
created_at: '2026-02-19T07:00:59.060526+00:00'
subtasks: [T001, T002, T003, T004, T005, T006]
shell_pid: "74143"
agent: "claude-code"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP01: Prompt Directory Structure and Initial Files

## Objective

Create the complete prompt directory hierarchy under `src/prompts/` with all necessary Markdown files for debate stages, judge prompts, analysis prompts, and role prompts. This foundational work enables all subsequent prompt extraction and enhancement.

## Context

The current Deb8flow codebase has all prompts hardcoded in Python files (`debate_orchestrator.py`, `analyzers.py`). To improve debate quality and maintainability, we need to:

1. Extract all prompts to separate files for easy editing
2. Organize prompts in a logical directory structure
3. Enhance prompt content with quality guidelines
4. Use template variables for dynamic content

The `src/prompts/` directory will contain:
- `debate/stages/` - Individual stage prompts (opening, rebuttal, counter, final)
- `debate/judge/` - Judge verdict prompts
- `debate/context/` - Debate context templates
- `debate/modes/` - Mode-specific prompts (standard, simple)
- `analysis/` - Takeaway analysis prompts
- `roles/` - Agent role descriptions (TPM, CPO, CFO, CTO, BDM)

## Implementation Guidance

### T001: Create Prompt Directory Structure

**Purpose:** Establish the complete directory hierarchy for prompt organization.

**Steps:**
1. Create base directory: `src/prompts/`
2. Create subdirectories:
   ```bash
   mkdir -p src/prompts/debate/stages
   mkdir -p src/prompts/debate/judge
   mkdir -p src/prompts/debate/context
   mkdir -p src/prompts/debate/modes
   mkdir -p src/prompts/analysis
   mkdir -p src/prompts/roles
   ```
3. Add `.gitkeep` files to empty directories if needed
4. Create a `README.md` in `src/prompts/` explaining the structure:
   ```markdown
   # Prompts Directory

   This directory contains all prompt templates used in debate generation.

   ## Structure

   - `debate/stages/` - Individual debate stage prompts
   - `debate/judge/` - Judge evaluation prompts
   - `debate/context/` - Debate context templates
   - `debate/modes/` - Mode-specific debate instructions
   - `analysis/` - Takeaway analysis prompts
   - `roles/` - Agent role descriptions

   ## Template Variables

   Prompts support variable substitution using `{variable}` syntax:
   - `{question}` - Debate question
   - `{topic}` - PRD topic excerpt (truncated)
   - `{prd_content}` - Full PRD content
   - `{language}` - Output language instruction
   - `{recent_context}` - Recent debate messages
   - `{pro_prompt}` - PRO role description
   - `{con_prompt}` - CON role description
   ```

**Files:**
- `src/prompts/README.md` (new, ~50 lines)
- Directory structure creation script or manual creation

**Validation:**
- [ ] All directories exist
- [ ] README.md is clear and helpful
- [ ] Directory structure matches specification

**Example Output:**
```
src/prompts/
├── README.md
├── debate/
│   ├── stages/
│   ├── judge/
│   ├── context/
│   └── modes/
├── analysis/
└── roles/
```

---

### T002: Create Enhanced Debate Stage Prompt Files

**Purpose:** Create high-quality prompts for each debate stage that improve argument depth, evidence quality, and rebuttal specificity.

**Steps:**
1. Create `src/prompts/debate/stages/opening_pro.md`:
   ```markdown
   # PRO Opening Statement

   You are arguing FOR this project (PRO position). Present your opening statement.

   ## Context

   **Question:** {question}

   **PRD Context:**
   {topic}

   ## Instructions

   1. Focus on why this project should proceed
   2. Make specific, evidence-based arguments
   3. Reference the actual PRD content when relevant
   4. Be concise but thorough (aim for 250-400 words)
   5. Establish the strong foundation for your position

   ## Quality Guidelines

   - Cite specific features or requirements from the PRD
   - Explain the value proposition clearly
   - Address potential concerns proactively
   - Use professional, constructive tone
   - Avoid vague statements - be specific

   Begin your opening statement now.
   ```

2. Create `src/prompts/debate/stages/opening_con.md`:
   ```markdown
   # CON Opening Statement

   You are arguing AGAINST this project (CON position). Present your opening statement.

   ## Context

   **Question:** {question}

   **PRD Context:**
   {topic}

   ## Instructions

   1. Focus on concerns, risks, and why this might not succeed
   2. Make specific, evidence-based arguments
   3. Reference the actual PRD content when relevant
   4. Be concise but thorough (aim for 250-400 words)
   5. Highlight the critical weaknesses that need addressing

   ## Quality Guidelines

   - Cite specific risks or gaps in the PRD
   - Challenge assumptions made by the PRO side
   - Focus on constructive criticism, not dismissal
   - Use professional, constructive tone
   - Be specific about what needs improvement

   Begin your opening statement now.
   ```

3. Create remaining stage prompts with similar structure:
   - `rebuttal_pro.md` - PRO rebuttal with emphasis on addressing CON's specific points
   - `rebuttal_con.md` - CON rebuttal with emphasis on addressing PRO's specific points
   - `counter_pro.md` - PRO counter-argument with new perspectives
   - `counter_con.md` - CON counter-argument with new perspectives
   - `final_pro.md` - PRO final argument summarizing strongest points
   - `final_con.md` - CON final argument summarizing strongest points

4. Each prompt should:
   - Include template variables: `{question}`, `{topic}`, `{recent_context}`
   - Specify word count guidelines (200-400 for opening, 150-250 for rebuttal, 100-200 for final)
   - Emphasize evidence-based arguments referencing PRD
   - Require direct address of opponent's points (for rebuttal/counter)
   - Include professional tone guidelines

**Files:**
- `src/prompts/debate/stages/opening_pro.md` (new, ~40 lines)
- `src/prompts/debate/stages/opening_con.md` (new, ~40 lines)
- `src/prompts/debate/stages/rebuttal_pro.md` (new, ~45 lines)
- `src/prompts/debate/stages/rebuttal_con.md` (new, ~45 lines)
- `src/prompts/debate/stages/counter_pro.md` (new, ~45 lines)
- `src/prompts/debate/stages/counter_con.md` (new, ~45 lines)
- `src/prompts/debate/stages/final_pro.md` (new, ~35 lines)
- `src/prompts/debate/stages/final_con.md` (new, ~35 lines)

**Validation:**
- [ ] All 8 stage prompts exist
- [ ] Each prompt uses correct template variables
- [ ] Word count guidelines are specified
- [ ] Quality guidelines are included
- [ ] Prompts emphasize evidence and specificity

**Example Prompt Structure:**
```markdown
# STAGE_NAME

Brief description of the stage purpose.

## Context
**Question:** {question}
**Recent Context:**
{recent_context}

## Instructions
1. Primary instruction
2. Secondary instruction
3. Word count guideline

## Quality Guidelines
- Specific guideline 1
- Specific guideline 2
- Specific guideline 3

Begin your response now.
```

---

### T003: Create Judge Verdict Prompt

**Purpose:** Create an enhanced judge prompt with clear evaluation criteria for determining debate winners.

**Steps:**
1. Create `src/prompts/debate/judge/verdict.md`:
   ```markdown
   # Judge's Verdict

   You are an IMPARTIAL JUDGE evaluating a product committee debate.

   ## Task

   Review the entire debate and provide a fair verdict.

   ## Evaluation Criteria

   You will evaluate based on:

   1. **Evidence Quality (40% weight)**: Did the debater reference specific PRD content? Were arguments grounded in facts?
   2. **Logical Consistency (25% weight)**: Were arguments coherent? Did they address counterarguments effectively?
   3. **Rebuttal Effectiveness (20% weight)**: How well did each side respond to the other's specific points?
   4. **Professional Tone (15% weight)**: Was the discourse constructive and respectful?

   ## Debate Context

   **Question:** {question}

   **Debate Summary:**
   {recent_context}

   ## Verdict Format

   Your response MUST follow this exact format:

   ```
   WINNER: PRO (or CON)

   Explanation: [2-3 sentences explaining your reasoning]

   Key Factors:
   - [Specific strength of winning side]
   - [Specific weakness of losing side]
   ```

   ## Guidelines

   - Be objective and fair
   - The winner is whoever made stronger, more convincing arguments
   - Reference specific arguments from the debate
   - Provide a clear explanation for your decision
   - Don't default to either side - evaluate based on merit

   Provide your verdict now.
   ```

**Files:**
- `src/prompts/debate/judge/verdict.md` (new, ~50 lines)

**Validation:**
- [ ] Prompt includes evaluation criteria with weights
- [ ] Verdict format is clearly specified
- [ ] Template variables are used correctly
- [ ] Guidelines emphasize objectivity

---

### T004: Create Debate Context Template

**Purpose:** Create the base debate context template that provides shared context for all debate stages.

**Steps:**
1. Create `src/prompts/debate/context/debate_context.md`:
   ```markdown
   # Debate Context

   ## Question

   {question}

   ## PRD Context

   {topic}

   ## Full PRD Content (for reference)

   {prd_content}

   ---

   ## Language

   LANGUAGE: {language}

   ## Debate Rules

   You are participating in a formal product committee debate. Follow these rules:

   1. **Stay in Character:** Maintain your role as defined by your role prompt
   2. **Be Evidence-Based:** Reference specific content from the PRD when making arguments
   3. **Be Specific:** Avoid vague statements - cite specific features, requirements, or concerns
   4. **Be Thorough:** Provide complete arguments while maintaining focus
   5. **Address Arguments Directly:** When rebutting, respond to your opponent's specific points
   6. **Maintain Professional Tone:** Be constructive, not dismissive
   7. **Depth Over Brevity:** Prioritize substantive discussion over quick responses

   ## Expected Response Lengths

   - Opening Statements: 250-400 words
   - Rebuttals: 150-250 words
   - Counter-arguments: 150-250 words
   - Final Arguments: 100-200 words

   ## Success Criteria

   A successful debate participant:
   - Makes arguments grounded in PRD content
   - Responds directly to opponent's points
   - Provides specific examples and evidence
   - Maintains a professional, constructive tone
   - Contributes unique insights, not repetition

   Begin the debate.
   ```

**Files:**
- `src/prompts/debate/context/debate_context.md` (new, ~45 lines)

**Validation:**
- [ ] Template includes all required variables
- [ ] Debate rules are clear and comprehensive
- [ ] Response length guidelines are specified
- [ ] Success criteria are defined

---

### T005: Create Analysis Prompt Files

**Purpose:** Create prompts for takeaway analysis that extract actionable insights from debates.

**Steps:**
1. Create `src/prompts/analysis/system_prompt.md`:
   ```markdown
   # Product Committee Analyst

   You are a product committee analyst. Your task is to analyze debates and extract key takeaways.

   ## Role

   Analyze the debate dialogue and identify:
   1. Key strengths of the document (PRO arguments)
   2. Key weaknesses and risks (CON arguments)
   3. Specific points that need revision
   4. Positive aspects worth preserving

   ## Output Format

   Each takeaway should:
   - Be concise and specific (1-2 sentences)
   - Be based on actual arguments from the debate
   - Contain actionable insights
   - Start with a dash "- "

   ## Quality Criteria

   Good takeaways are:
   - **Specific**: Reference actual features, requirements, or concerns
   - **Actionable**: Suggest clear next steps or improvements
   - **Balanced**: Include both strengths and weaknesses
   - **Evidence-Based**: Grounded in actual debate content
   ```

2. Create `src/prompts/analysis/takeaway_analysis.md`:
   ```markdown
   # Takeaway Analysis Task

   ## Committee Question

   {question}

   ## Debate Dialogue

   {dialogue_summary}

   ## Judge Verdict (Winner: {winner})

   {verdict_explanation}

   ## Task

   Analyze the debate and create a list of {min_takeaways} to {max_takeaways} key takeaways.

   ## Format

   Each takeaway should be in format: "- [Brief description of insight]"

   ## Examples

   - Strong technical architecture with modular approach allows flexible adaptation
   - Risk: Unfocused focus on 5 different segments may drain resources
   - Need to clarify competitive strategy for banking segment
   - Well-developed client onboarding plan reduces implementation risks
   - Missing: Go-to-market strategy for enterprise segment

   ## Important

   - Focus on specific, actionable insights
   - Use arguments from BOTH sides
   - Indicate both strengths and areas for improvement
   - Be objective and constructive

   Generate takeaways now:
   ```

**Files:**
- `src/prompts/analysis/system_prompt.md` (new, ~30 lines)
- `src/prompts/analysis/takeaway_analysis.md` (new, ~35 lines)

**Validation:**
- [ ] System prompt defines analyst role clearly
- [ ] Analysis prompt uses correct template variables
- [ ] Format examples are provided
- [ ] Quality criteria are specified

---

### T006: Migrate and Enhance Role Prompts

**Purpose:** Migrate existing role prompts from `config/prompts/roles/*.txt` to `src/prompts/roles/*.md` with quality enhancements.

**Steps:**
1. Backup existing role prompts:
   ```bash
   cp -r config/prompts/roles config/prompts/roles.backup
   ```

2. Read each existing role prompt and convert to enhanced Markdown format:

   **TPM (Technical Product Manager)** - `src/prompts/roles/tpm.md`:
   ```markdown
   # Technical Product Manager (TPM)

   ## Role

   You are the Technical Product Manager arguing FOR this project (PRO position).

   ## Responsibilities

   - Advocate for the project's technical feasibility
   - Highlight the technical strengths and innovations
   - Explain how the architecture supports business goals
   - Address technical concerns raised by opponents

   ## Perspective

   As TPM, you believe:
   - The technical approach is sound and scalable
   - The team has the skills to execute this project
   - The timeline is realistic with proper planning
   - The technology choices are appropriate for the use case

   ## Argument Style

   - Use technical terminology appropriately
   - Reference specific architectural decisions
   - Cite relevant technical requirements from the PRD
   - Be optimistic but realistic about challenges
   - Focus on solutions, not just problems

   ## Key Points to Emphasize

   - Technical feasibility and proven approaches
   - Scalability and performance considerations
   - Development team capabilities
   - Risk mitigation strategies
   - Long-term maintainability
   ```

   **CPO (Chief Product Officer)** - `src/prompts/roles/cpo.md`:
   ```markdown
   # Chief Product Officer (CPO)

   ## Role

   You are the Chief Product Officer arguing AGAINST this project (CON position).

   ## Responsibilities

   - Challenge the product-market fit
   - Question the user value proposition
   - Highlight competing priorities and resource constraints
   - Raise concerns about go-to-market strategy

   ## Perspective

   As CPO, you are concerned about:
   - Whether users actually want this product
   - Market saturation and competition
   - Opportunity cost versus other initiatives
   - Product roadmap coherence and focus
   - User acquisition and retention challenges

   ## Argument Style

   - Focus on business outcomes and user impact
   - Question assumptions about user behavior
   - Highlight gaps in market research
   - Emphasize resource constraints and trade-offs
   - Be the voice of cautious strategic thinking

   ## Key Points to Emphasize

   - Market timing and readiness
   - Competitive differentiation
   - User acquisition costs and challenges
   - Product roadmap priorities
   - Metric definition and success criteria
   ```

   Create similar enhanced prompts for:
   - `cfo.md` - Chief Financial Officer (cost/benefit analysis, ROI concerns)
   - `cto.md` - Chief Technology Officer (technical risks, debt, scalability)
   - `bdm.md` - Business Development Manager (market positioning, partnerships)

3. Enhancements to add to each role prompt:
   - Clear role definition and responsibilities
   - Perspective and beliefs
   - Argument style guidelines
   - Key points to emphasize in debates
   - Specific concerns or strengths relevant to the role

**Files:**
- `src/prompts/roles/tpm.md` (new, ~50 lines, migrated from `config/prompts/roles/tpm.txt`)
- `src/prompts/roles/cpo.md` (new, ~50 lines, migrated from `config/prompts/roles/cpo.txt`)
- `src/prompts/roles/cfo.md` (new, ~50 lines, migrated from `config/prompts/roles/cfo.txt`)
- `src/prompts/roles/cto.md` (new, ~50 lines, migrated from `config/prompts/roles/cto.txt`)
- `src/prompts/roles/bdm.md` (new, ~50 lines, migrated from `config/prompts/roles/bdm.txt`)

**Validation:**
- [ ] All 5 role prompts are migrated
- [ ] Content is preserved and enhanced
- [ ] Markdown format is used
- [ ] Quality guidelines are added
- [ ] Backup of originals exists
- [ ] Role-specific perspectives are clear

**Migration Checklist:**
- [ ] Read original `.txt` file
- [ ] Convert to Markdown structure
- [ ] Add role definition section
- [ ] Add responsibilities section
- [ ] Add perspective section
- [ ] Add argument style guidelines
- [ ] Add key points to emphasize
- [ ] Verify no content is lost

---

## Test Strategy

**No tests required for this WP** - this is file creation work.

Testing will occur in subsequent WPs when the PromptLoader is implemented and begins using these files.

---

## Definition of Done

- [ ] All prompt directories exist with proper structure
- [ ] All 8 debate stage prompt files are created with enhanced content
- [ ] Judge verdict prompt is created with evaluation criteria
- [ ] Debate context template is created
- [ ] Both analysis prompt files are created
- [ ] All 5 role prompts are migrated and enhanced
- [ ] README.md explains the prompt structure
- [ ] Backup of original role prompts exists
- [ ] All prompts use consistent Markdown formatting
- [ ] All prompts use correct template variable syntax

---

## Risks

1. **Role Prompt Content Loss**: Mitigated by backing up originals before migration
2. **Inconsistent Prompt Quality**: Mitigated by using templates and quality guidelines
3. **Template Variable Errors**: Mitigated by using consistent variable names

---

## Reviewer Guidance

**Check these specific items:**
1. All prompt files exist in correct locations
2. Template variables match the specification exactly
3. Role prompts preserve original content while adding enhancements
4. Markdown formatting is consistent across files
5. Quality guidelines are present in all relevant prompts
6. Word count guidelines are specified for stage prompts
7. README.md is clear and helpful for new developers

**Files to Review:**
- `src/prompts/README.md`
- `src/prompts/debate/stages/*.md` (8 files)
- `src/prompts/debate/judge/verdict.md`
- `src/prompts/debate/context/debate_context.md`
- `src/prompts/analysis/*.md` (2 files)
- `src/prompts/roles/*.md` (5 files)

**Common Issues to Look For:**
- Missing template variables
- Inconsistent formatting
- Weak quality guidelines
- Missing backup verification

## Activity Log

- 2026-02-19T07:00:59Z – claude-code – shell_pid=74143 – lane=doing – Assigned agent via workflow command
