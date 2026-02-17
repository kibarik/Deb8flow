---
work_package_id: "WP08"
subtasks: ["T031", "T032", "T033", "T034"]
title: "Default Configuration"
phase: "Phase 2 - Core Implementation"
lane: "planned"
dependencies: ["WP01"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP08 – Default Configuration 🎯 MVP

## Objectives & Success Criteria

Create default `debate.yml` that preserves current PRD review behavior exactly.

**Success Criteria**:
- debate.yml exists in project root
- PRO/CON prompts match current hardcoded prompts exactly
- Default config produces identical output to current system

## Context & Constraints

**Dependencies**: WP01 (Config Data Model)

**Critical**: This is the MVP - must preserve existing behavior

## Subtasks

### T031 – Extract PRO Role Prompts
- Copy from `prompts/pro_debater_prompts.py`
- Copy from `prompts/roles/` if exists
- Preserve exact wording

### T032 – Extract CON Role Prompts
- Copy from `prompts/con_debater_prompts.py`
- Copy from `prompts/roles/` if exists
- Preserve exact wording

### T033 – Create debate.yml
- Mode: standard
- Rounds: 3
- Model: deepseek-chat (Requesty)
- Fact-checking: enabled, max_failures: 3
- Use extracted prompts inline

### T034 – Test Default Config
- Run debate with debate.yml
- Compare output to original system
- Verify identical behavior

## Implementation Notes

```yaml
# debate.yml
debate_config_version: "1.0"

workflow:
  mode: standard
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: |-
      [EXACT PROMPT FROM T031]
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

  - name: con
    side: con
    prompt: |-
      [EXACT PROMPT FROM T032]
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY

fact_checking:
  enabled: true
  max_failures: 3
```

## Review Guidance

[ ] Prompts copied exactly
[ ] All current settings preserved
[ ] Test shows identical output
[ ] debate.yml in project root

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
