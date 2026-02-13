# Quickstart: CLI Progress Indicators

**Feature**: 005-cli-progress-indicators
**Last Updated**: 2025-02-14

---

## Overview

This guide shows how to use the CLI progress indicators feature for the document debate workflow.

---

## Installation

Ensure `tqdm` is added to your dependencies:

```bash
pip install tqdm
```

Or add to `requirements.txt`:

```
tqdm>=4.66.0
```

---

## Basic Usage

Run the CLI with default progress display:

```bash
python3 document_debate_cli.py --docx 'document.docx' --request "What is the potential?"
```

You'll see output like:

```
[00:51:07] INFO     Starting document debate workflow...
[00:51:07] INFO     📄 Loaded document: document.docx
[00:51:07] INFO     📋 Debate topic: What is the potential?

Step 1/6: Generating debate topic...: 100%|██████████| 1/1
Step 2/6: Generating pro arguments...: 100%|██████████| 1/1
Step 3/6: Generating con arguments...: 100%|██████████| 1/1
Step 4/6: Fact checking pro arguments...: 100%|██████████| 1/1
Step 5/6: Fact checking con arguments...: 100%|██████████| 1/1
Step 6/6: Judge evaluating arguments...: 100%|██████████| 1/1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🏆 WINNER: PRO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[00:52:15] INFO     Workflow completed successfully | Status: SUCCESS
```

---

## Verbosity Levels

### Default Mode (no flags)

Shows step-by-step progress with "Step N/M:" format.

```bash
python3 document_debate_cli.py --docx 'document.docx' --request "question"
```

### Verbose Mode (`--verbose`)

Shows detailed sub-step progress and timing information.

```bash
python3 document_debate_cli.py --docx 'document.docx' --request "question" --verbose
```

Verbose output includes:
- Sub-step descriptions within each step
- Timing information for operations
- Internal workflow details
- LLM API call indicators

### Quiet Mode (`--quiet` or `-q`)

Suppresses all progress indicators, only shows errors and final result.

```bash
python3 document_debate_cli.py --docx 'document.docx' --request "question" --quiet
# or
python3 document_debate_cli.py --docx 'document.docx' --request "question" -q
```

Quiet mode is useful for:
- Automation scripts
- CI/CD pipelines
- Logging output to files

---

## Troubleshooting

### Progress bars not displaying

**Problem**: No progress bars appear during execution.

**Solutions**:
1. Check if `--quiet` flag is set (remove it)
2. Ensure terminal supports ANSI codes (most modern terminals do)
3. Check if output is being redirected (progress bars require TTY)
   ```bash
   # Use --quiet for non-TTY output
   python3 document_debate_cli.py --docx 'file.docx' --request "q" --quiet > output.txt
   ```

### Progress bars look distorted

**Problem**: Progress bars display incorrectly or overlap.

**Solutions**:
1. Try increasing terminal width (tqdm needs at least 40 characters)
2. Use `--quiet` mode if terminal doesn't support cursor control
3. Check if multiple processes are writing to the same terminal

### Progress updates freeze

**Problem**: Progress bar stops updating during execution.

**Solutions**:
1. The workflow is likely waiting on LLM API (this is normal)
2. Check internet connection
3. Verify API key is valid: `echo $OPENAI_API_KEY`

### Unicode issues on Windows

**Problem**: Progress bars show garbled characters on Windows.

**Solution**:
```bash
# Set terminal to UTF-8 mode
chcp 65001
python3 document_debate_cli.py --docx 'file.docx' --request "q"
```

---

## Tips

**For automation**: Always use `--quiet` mode to avoid TTY requirements
```bash
python3 document_debate_cli.py --docx 'file.docx' --request "q" --quiet > results.txt 2>&1
```

**For debugging**: Use `--verbose` to see internal operations
```bash
python3 document_debate_cli.py --docx 'file.docx' --request "q" --verbose
```

**For interactive use**: Default mode provides the best balance of information

---

## Environment Variables

No special environment variables required for progress tracking.

The existing `OPENAI_API_KEY` variable is still required for the workflow itself.

---

## Next Steps

- See `contracts/` for detailed interface documentation
- See `data-model.md` for implementation details
- Report issues on GitHub if progress display behaves unexpectedly
