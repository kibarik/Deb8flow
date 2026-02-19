# Prompt Management Guide

## Quick Start

Edit any prompt in `src/prompts/` and run debates - changes take effect immediately.

## Prompt Structure

### Debate Stages

Each debate stage has separate PRO and CON prompts:
- `opening_pro.md` / `opening_con.md` - Opening statements
- `rebuttal_pro.md` / `rebuttal_con.md` - Rebuttals
- `counter_pro.md` / `counter_con.md` - Counter-arguments
- `final_pro.md` / `final_con.md` - Final arguments

### Judge

`judge/verdict.md` - Judge evaluation and verdict

### Analysis

- `analysis/system_prompt.md` - Analyst system prompt
- `analysis/takeaway_analysis.md` - Takeaway generation

### Roles

`roles/*.md` - Agent role descriptions (TPM, CPO, CFO, CTO, BDM)

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{question}` | Debate question | "Should we build this?" |
| `{topic}` | PRD excerpt | First 500 chars |
| `{prd_content}` | Full PRD | Complete content |
| `{language}` | Language | "en", "ru" |
| `{recent_context}` | Recent messages | Last exchanges |
| `{pro_prompt}` | PRO role | TPM description |
| `{con_prompt}` | CON role | Opponent description |

## Adding New Stages

1. Create prompt file: `src/prompts/debate/stages/clarification_pro.md`
2. Add to config: `config/debate_config.yaml`
3. Update orchestrator to use new stage
4. Test with `--mode standard`

## Best Practices

- Be specific about word counts
- Require evidence-based arguments
- Emphasize professional tone
- Include examples in prompts
- Test changes with sample debates

## Migration

If you have prompts in the old `config/prompts/` location:
```bash
python scripts/migrate_prompts.py
```

The system will automatically fall back to old locations if needed.
