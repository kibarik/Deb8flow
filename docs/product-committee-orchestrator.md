# Product Committee Orchestrator

## Overview

The Product Committee Orchestrator runs four separate debate rooms sequentially, each pitting TPM (Technical Product Manager) against a different executive role (CPO, CFO, CTO, BDM). After all rooms complete, TPM performs self-reflection to synthesize insights and produce actionable recommendations.

## What It Does

This feature enables multi-perspective PRD review by:

- Running four debate rooms: TPM vs CPO, TPM vs CFO, TPM vs CTO, and TPM vs BDM
- Capturing structured JSON output from each room
- Performing TPM self-reflection after all rooms complete
- Generating comprehensive reports with differentiated perspectives
- Supporting graceful partial failure handling

## How It Works

### Architecture

```
PRD + Question → 4 Sequential Debate Rooms → TPM Self-Reflection → Final Report
```

### Data Flow

1. **Input**: User provides PRD file (.docx or text) and strategic question
2. **Compression**: PRD is compressed to 500-1500 words for context
3. **Debate Rooms**: Four rooms execute sequentially with different opponent roles
4. **Room Output**: Each room produces JSON with positions, verdict, and takeaways
5. **Self-Reflection**: TPM synthesizes learnings from all rooms
6. **Final Report**: Comprehensive markdown report with all perspectives

### Room Structure

Each debate room follows this format:

```
Room (TPM vs [Role]) → Document Debate CLI → JSON Output → Next Room
```

Room JSON contains:
- Room ID (e.g., "TPM_vs_CPO")
- TPM position summary
- Opponent position summary
- Judge verdict (winner + explanation)
- 3-5 key takeaways

## Usage

### Basic Command

```bash
python product_committee.py --prd path/to/prd.docx --question "what's the potential?"
```

### CLI Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--prd` / `--docx` | Yes | - | Path to PRD file |
| `--question` | Yes | - | Committee question |
| `--model` | No | - | LLM model (passed through if supported) |
| `--max-retries` | No | 2 | Retry count per room |
| `--output-dir` | No | ./committee_output | Base output location |
| `--roles-dir` | No | prompts/roles/ | Role prompt location |
| `--run-id` | No | Auto-generated | Manual run identifier |
| `--allow-short-prd` | No | False | Enforce minimum PRD length |

### Output Structure

```
committee_output/
└── RUN_YYYY-MM-DD_HHMMSS_slug/
    ├── tpm_cpo.json
    ├── tpm_cfo.json
    ├── tpm_cto.json
    ├── tpm_bdm.json
    ├── tpm_reflection.json
    ├── final_report.md
    └── metadata.json
```

## Configuration

### Role Prompts

Role prompts are loaded from `prompts/roles/` directory by default:

- `tpm.txt` - Technical Product Manager (REQUIRED)
- `cpo.txt` - Chief Product Officer
- `cfo.txt` - Chief Financial Officer
- `cto.txt` - Chief Technology Officer
- `bdm.txt` - Business Development Manager

Custom role directories can be specified via `--roles-dir`.

### Room Status

Each room has a status:
- `success` - Room completed successfully
- `failed` - Room failed after retries
- `skipped_missing_prompt` - Room skipped due to missing prompt file

## Error Handling

### Graceful Partial Failure

The system continues running remaining rooms even if one fails:

1. Failed rooms are marked in metadata
2. Remaining rooms continue execution
3. Self-reflection runs with available data
4. Final report notes missing perspectives

### Validation

| Condition | Behavior |
|-----------|----------|
| PRD file missing/unreadable | Immediate error, non-zero exit code |
| Question empty | Error, require non-empty question |
| TPM prompt missing | Fatal error, abort immediately |
| Other role prompt missing | Warning logged, room skipped |
| PRD < 100 characters | Warning logged, run allowed (unless `--allow-short-prd` set) |

## Success Criteria

- **SC-001**: Full committee run completes without unhandled exceptions
- **SC-002**: Partial failures are surfaced in metadata and final report
- **SC-003**: Final report contains differentiated perspectives per role
- **SC-004**: Final report provides 3+ concrete, actionable recommendations
- **SC-005**: Iterative reruns create independent timestamped folders
- **SC-006**: Complete run finishes in under 10 minutes (soft target)

## TPM Self-Reflection

After all rooms complete, TPM self-reflection:

### Input

- Compressed PRD brief (500-1500 words)
- Original question
- All successful room JSON results

### Output

- What TPM learned from each role
- Updated project potential assessment
- Concrete recommendations for PRD author
- Which arguments were accepted/rejected

### Always Runs

Self-reflection executes even if:
- Zero rooms succeeded
- Only one room succeeded
- Multiple rooms failed

## Final Report Content

The `final_report.md` includes:

1. Brief summary of each room (TPM position, opponent position, judge verdict)
2. TPM self-reflection content
3. Explicit notes about failed/skipped rooms
4. Concrete, actionable recommendations (not generic advice)

## Edge Cases

### Input Validation

- PRD does not exist or is unreadable → Error before any rooms run
- PRD < 100 characters → Warning logged, run allowed
- Question empty → Error before any rooms run
- Question very short → Warning logged recommending reformulation

### Execution

- All four rooms fail → Self-reflection runs with zero room data
- Only one room succeeds → Self-reflection notes limited data
- Network timeout → Retry up to `--max-retries` times
- LLM API rate limiting → Retry with exponential backoff

### Output

- Output directory does not exist → Create directory tree as needed
- Output directory not writable → Error before any rooms run
- Same `--run-id` used twice → Overwrite previous run

### Large Documents

- PRD 30-50 pages or larger → Parse and run, may exceed target runtime
- PRD contains mixed languages → Handle and produce coherent output
- PRD contains only images → Warning about low text content, proceed if user insists
