# Quickstart: Product Committee Orchestrator

**Feature**: 007-product-committee-orchestrator
**Date**: 2026-02-14

## Overview

The Product Committee Orchestrator (`product_committee.py`) simulates a virtual product committee by running four sequential debate rooms where TPM debates against CPO, CFO, CTO, and BDM perspectives about your PRD. After all rooms complete, TPM synthesizes insights and produces actionable recommendations.

## Prerequisites

- Python 3.12+ installed
- Existing Deb8flow installation with `document_debate_cli.py`
- Role prompt files in `prompts/roles/`:
  - `tpm.txt` (required)
  - `cpo.txt`, `cfo.txt`, `cto.txt`, `bdm.txt` (optional but recommended)
- Valid PRD document (.docx or text file)
- LLM API credentials configured (for underlying debate system)

## Basic Usage

### Minimal Example

```bash
python product_committee.py \
  --prd path/to/your_prd.docx \
  --question "What's the potential of this project?"
```

This will:
1. Run 4 debate rooms sequentially (TPM vs each role)
2. Execute TPM self-reflection
3. Create output in `./committee_output/RUN_<timestamp>_*/`
4. Generate `final_report.md` with multi-perspective analysis

### Full Example with All Options

```bash
python product_committee.py \
  --prd path/to/your_prd.docx \
  --question "What's the potential of this project?" \
  --model gpt-4.1 \
  --max-retries 3 \
  --output-dir ./my_committee_runs \
  --roles-dir prompts/roles_custom \
  --run-id my-project-review-001 \
  --verbose
```

## CLI Arguments

### Required Arguments

| Flag | Description | Example |
|------|-------------|---------|
| `--prd` / `--docx` | Path to PRD document | `--prd docs/feature_prd.docx` |
| `--question` | Committee question for all rooms | `--question "What's the potential?"` |

### Optional Arguments

| Flag | Description | Default |
|------|-------------|---------|
| `--model` | LLM model name | (from debate system config) |
| `--max-retries` | Max retry attempts per room | 2 |
| `--output-dir` | Base output directory | `./committee_output` |
| `--roles-dir` | Role prompts location | `prompts/roles/` |
| `--run-id` | Manual run identifier | (auto-generated timestamp) |
| `--allow-short-prd` | Enforce minimum PRD length (100 chars) | (disabled) |
| `--verbose` | Extended logging | (disabled) |
| `--quiet` | Minimal logging | (disabled) |

## Output Structure

After running, you'll find artifacts in:

```
<output-dir>/RUN_<timestamp>_<slug>/
├── tpm_cpo.json          # TPM vs CPO room result
├── tpm_cfo.json          # TPM vs CFO room result
├── tpm_cto.json          # TPM vs CTO room result
├── tpm_bdm.json          # TPM vs BDM room result
├── tpm_reflection.json   # TPM self-reflection result
├── metadata.json         # Run metadata and room statuses
└── final_report.md       # Human-readable summary
```

### Understanding the Outputs

**`final_report.md`** - Start here! Contains:
- Brief summary of each room (TPM position, opponent position, judge verdict)
- TPM's self-reflection with:
  - What TPM learned from each role
  - Updated potential assessment
  - Concrete recommendations for your PRD
  - Which arguments TPM accepted/rejected

**`metadata.json`** - Technical details:
- Input paths, timestamps, model used
- Status of each room (success/failed/skipped)
- Warning flags (e.g., `prd_too_short`)
- Any errors encountered

**Room JSONs** - Detailed room results for automation/custom processing

## Common Workflows

### Iterative PRD Refinement

1. Run initial committee review
2. Read `final_report.md`
3. Update your PRD based on recommendations
4. Run again (creates new timestamped output folder)
5. Compare reports to see improvement

### Custom Personas

1. Create custom role prompts:
   ```
   prompts/roles_custom/
   ├── tpm.txt
   ├── cpo_industry.txt
   ├── cfo_fintech.txt
   ├── cto_enterprise.txt
   └── bdm_sme.txt
   ```

2. Run with custom prompts:
   ```bash
   python product_committee.py \
     --prd prd.docx \
     --question "..." \
     --roles-dir prompts/roles_custom
   ```

### Quick Validation

Use `--quiet` flag for minimal output (useful for CI/automation):

```bash
python product_committee.py \
  --prd prd.docx \
  --question "..." \
  --quiet
# Output: "Run finished. See: ./committee_output/RUN_..."
```

## Troubleshooting

### Common Errors

**Error: "PRD file not found"**
- Check `--prd` path is correct
- Use absolute path if relative path doesn't work

**Error: "TPM prompt file missing"**
- Ensure `prompts/roles/tpm.txt` exists
- Or specify custom location via `--roles-dir`

**Warning: "PRD too short"**
- PRD is < 100 characters; results may be poor quality
- Check `metadata.json` for `prd_too_short: true` flag

**One or more rooms failed**
- Check `metadata.json` for room statuses and error messages
- Run with `--verbose` for detailed retry logs
- Report is still generated with available perspectives

### Getting Help

```bash
python product_committee.py --help
```

## Next Steps

- Review `final_report.md` for actionable recommendations
- Iterate on your PRD and rerun as needed
- Explore room JSONs for deeper analysis
- Check `data-model.md` for detailed entity definitions
