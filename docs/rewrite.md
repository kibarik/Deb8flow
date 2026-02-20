# Rewrite Script - Document Revision with Debate Verification

The `rewrite` script automatically applies revisions from a committee conclusion file to your source document and validates completeness through AI-powered debate.

## Overview

After running a product committee, you get a `conclusion.md` with actionable revisions. The rewrite script automates applying these revisions to your document and verifies them through a PRO vs CON debate.

## How It Works

### Two-Phase Workflow

1. **Apply Revisions**: Parse conclusion.md and apply revisions to source document
2. **Verify Through Debate**: Run PRO vs CON debate to confirm all revisions are incorporated

The debate continues until:
- All revisions are verified, OR
- Maximum round limit is reached (default: 5)

### Verification Debate

- **PRO Agent**: Argues that revisions are properly incorporated
- **CON Agent**: Finds missing or incorrect implementations
- **Judge**: Evaluates and determines which revisions are verified

## Installation

The rewrite script is part of Deb8flow:

```bash
# If using from source
python scripts/rewrite --help

# Or if installed as package
rewrite --help
```

## Usage

### Basic Rewrite

Apply all revisions from a conclusion to your document:

```bash
rewrite --file docs/prd.md --conclusion committee_output/RUN_123/conclusion.md
```

What happens:
1. Source file backed up to `docs/prd.md.backup`
2. Revisions extracted and applied
3. Verification debate runs
4. Exit code indicates result (0=success, 1=partial)

### Custom Verification Rounds

Increase or decrease verification rounds:

```bash
# More thorough verification (10 rounds)
rewrite --file docs/prd.md --conclusion ... --max-rounds 10

# Quick verification (2 rounds)
rewrite --file docs/prd.md --conclusion ... --max-rounds 2
```

### Output to Different File

Keep original intact:

```bash
rewrite --file docs/prd.md --conclusion ... --output docs/prd_revised.md
```

### Skip Backup

If you're confident (use caution):

```bash
rewrite --file docs/prd.md --conclusion ... --no-backup
```

## Configuration

Configure rewrite behavior in `config/debate_config.yaml`:

```yaml
rewrite:
  max_rounds: 5              # Maximum verification rounds
  backup_suffix: ".backup"    # Backup file suffix
  partial_report: "rewrite_partial_report.md"
  prompts:
    pro: "src/prompts/rewrite/pro_verification.md"
    con: "src/prompts/rewrite/con_verification.md"
    judge: "src/prompts/rewrite/judge_verdict.md"
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | All revisions verified |
| 1 | Partial | Some revisions unverified (check console) |
| 2 | Failed | Critical error (check logs) |
| 3 | Validation Error | Input files invalid |

## Partial Completion

When max rounds reached without full verification:

```
Partial completion: 4 of 7 revisions applied
Remaining revisions:
- Section 3.2: Add error handling for timeout cases
- Section 4.1: Clarify API authentication flow
- Section 5.3: Add example for edge case

Recommendations:
- Manual review of Section 3.2, 4.1, 5.3
- Consider running rewrite again with --max-rounds 10
- Review rewrite_partial_report.md for details
```

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Markdown | `.md` | Section-based editing |
| Text | `.txt` | Keyword-based matching |
| Word | `.docx` | Requires python-docx |

## Examples

### Example 1: After Product Committee

```bash
# Run committee
committee --file docs/prd.md --question "Should we build X?"

# Apply revisions
rewrite --file docs/prd.md --conclusion committee_output/RUN_XXX/conclusion.md

# Result: PRD updated with verified revisions
```

### Example 2: Iterative Improvement

```bash
# Quick check first
rewrite --file docs/prd.md --conclusion ... --max-rounds 2

# If partial, run again with more rounds
rewrite --file docs/prd.md --conclusion ... --max-rounds 10
```

### Example 3: Safe Editing

```bash
# Always write to new file
rewrite --file docs/prd.md --conclusion ... --output prd_v2.md

# Compare before replacing
diff docs/prd.md prd_v2.md

# Replace if satisfied
mv prd_v2.md docs/prd.md
```

## Troubleshooting

### "No revisions found in conclusion"

**Cause**: Conclusion.md doesn't match expected format.

**Solution**: Ensure conclusion.md contains:
```markdown
## Рекомендации

1. First recommendation [room]
2. Second recommendation [room]
```

### "Cannot find section in document"

**Cause**: Revision references section that doesn't exist.

**Solution**: Review conclusion.md and update section references, or revision will be marked unverified.

### "Backup file already exists"

**Cause**: Previous backup wasn't cleaned up.

**Solution**:
```bash
# Review existing backup
cat docs/prd.md.backup

# Remove or rename it
rm docs/prd.md.backup
```

## Architecture

The rewrite feature follows clean architecture:

```
src/rewrite/
├── domain/          # Entities and value objects
├── adapters/        # CLI, parser, editor, storage
├── application/     # Use case orchestrator
└── infrastructure/  # File operations
```

## See Also

- [Quick Start Guide](../kitty-specs/019-document-rewrite-script/quickstart.md)
- [Specification](../kitty-specs/019-document-rewrite-script/spec.md)
- [Debate Configuration](../config/debate_config.yaml)
