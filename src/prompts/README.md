# Prompts Directory

This directory contains all prompt templates used in debate generation.

## Structure

- `debate/stages/` - Individual debate stage prompts
  - `opening_pro.md` / `opening_con.md` - Opening statements
  - `rebuttal_pro.md` / `rebuttal_con.md` - Rebuttals
  - `counter_pro.md` / `counter_con.md` - Counter-arguments
  - `final_pro.md` / `final_con.md` - Final arguments
- `debate/judge/` - Judge evaluation prompts
- `debate/context/` - Debate context templates
- `debate/modes/` - Mode-specific debate instructions
  - `simple.md` - Single-call debate mode
  - `standard.md` - Multi-turn debate mode
- `analysis/` - Takeaway analysis prompts
- `roles/` - Agent role descriptions

## Template Variables

Prompts support variable substitution using `{variable}` syntax:

| Variable | Description | Example Usage |
|----------|-------------|---------------|
| `{question}` | Debate question | "Should we build this feature?" |
| `{topic}` | PRD topic excerpt (truncated) | First 500-800 chars of PRD |
| `{prd_content}` | Full PRD content | Complete PRD text |
| `{language}` | Output language instruction | "English" or "Russian" |
| `{recent_context}` | Recent debate messages | Last 2-3 exchanges |
| `{pro_prompt}` | PRO role description | TPM agent prompt |
| `{con_prompt}` | CON role description | Opponent agent prompt |
| `{dialogue_summary}` | Debate summary for analysis | Combined dialogue text |
| `{verdict_explanation}` | Judge's verdict explanation | Winner reasoning |
| `{winner}` | Debate winner | "PRO" or "CON" |
| `{min_takeaways}` | Minimum takeaways to generate | 3 |
| `{max_takeaways}` | Maximum takeaways to generate | 15 |

## Editing Prompts

To modify debate behavior:

1. Navigate to the relevant prompt file
2. Edit the Markdown content
3. Save the file
4. Run debates - changes take effect immediately

## Adding New Stages

To add a new debate stage:

1. Create prompt file: `src/prompts/debate/stages/<stage_name>_<speaker>.md`
2. Add to configuration: `config/debate_config.yaml`
3. Update orchestrator to use the new stage
4. Test with sample debates

## Best Practices

- Be specific about word counts and response lengths
- Require evidence-based arguments referencing PRD content
- Emphasize professional, constructive tone
- Include examples in prompts where helpful
- Test changes with sample debates before committing
- Keep prompts focused and concise

## Migration Notes

If you have prompts in the old `config/prompts/` location:

```bash
python scripts/migrate_prompts.py
```

The system will automatically fall back to old locations if needed, with deprecation warnings.
