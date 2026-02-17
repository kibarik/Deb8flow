---
work_package_id: "WP10"
subtasks: ["T039", "T040", "T041", "T042"]
title: "Polish and Documentation"
phase: "Phase 3 - Enhancement"
lane: "planned"
dependencies: ["WP08"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP10 – Polish and Documentation

## Objectives & Success Criteria

Update dependencies, documentation, and create migration guide.

**Success Criteria**:
- pyyaml in requirements.txt
- README updated with config usage
- CLAUDE.md updated with architecture
- Migration guide created

## Context & Constraints

**Dependencies**: WP08 (Default Configuration) - for accurate documentation

## Subtasks

### T039 – Add pyyaml to Requirements
- Check if pyyaml is in requirements.txt
- Add if missing: `pyyaml>=6.0`

### T040 – Update README.md
- Add "Configuration" section
- Document --debate-config usage
- Include quickstart example
- Link to examples/ directory

### T041 – Update CLAUDE.md
- Update architecture section
- Add debate.yml reference
- Document configuration system
- Update multi-LLM section for config approach

### T042 – Create Migration Guide
- File: `docs/MIGRATION.md` or root
- Explain change from hardcoded to config
- How to preserve current behavior
- How to customize roles
- Common migration scenarios

## Implementation Notes

README additions:
```markdown
## Configuration

Debates are configured via `debate.yml`. To use a custom config:

```bash
python main.py --debate-config path/to/config.yml
```

See `examples/` for configuration templates.
```

## Review Guidance

[ ] pyyaml dependency added
[ ] README documents --debate-config
[ ] CLAUDE.md describes config architecture
[ ] Migration guide is clear

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
