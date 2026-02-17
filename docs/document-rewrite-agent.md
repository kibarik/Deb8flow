# Document Rewrite Agent

## Overview

The Document Rewrite Agent automatically updates documents based on debate conclusions. When the `--make-review` flag is provided, the system preserves the original document, processes it through an AI rewriter agent using recommendations from conclusion.md, and generates a new document with all improvements applied.

## What It Does

This feature:

- Copies the original document to the run-id directory for reference
- Invokes an AI rewriter agent after conclusion.md is generated
- Reads both the original document and conclusion.md
- Applies all recommendations from the debate conclusion
- Creates a new document with timestamped filename
- Supports multiple file formats (.docx, .md, .txt, .rtf)

## How It Works

### Architecture

```
--make-review Flag → Original Document Copy → Debate → conclusion.md → Rewriter Agent → Rewritten Document
```

### Data Flow

1. User provides `--make-review` flag with document path
2. Original document is copied to `{run-id}` directory
3. Debate proceeds normally and generates conclusion.md
4. After conclusion.md is created, rewriter agent is invoked
5. Rewriter reads original document and conclusion.md
6. Rewriter applies all recommendations aggressively
7. New document is saved with timestamped filename

### Output Files

When `--make-review` is enabled, the output directory contains:

```
{run-id}/
├── {original_name}.{extension}           # Original document copy
├── {original_name}_YYYYMMDD_HHMMSS.{extension}  # Rewritten document
├── conclusion.md                          # Debate conclusions
└── metadata.json                          # Run metadata
```

## Usage

### Basic Command

```bash
python product_committee.py --prd /path/to/prd.docx --question "What's the potential?" --make-review
```

### What Happens

1. Debate runs normally with all participants
2. Original `/path/to/prd.docx` is copied to output directory
3. conclusion.md is generated with recommendations
4. Rewriter agent automatically processes the document
5. New file `prd_20260217_123456.docx` is created with improvements

### Without the Flag

```bash
python product_committee.py --prd /path/to/prd.docx --question "..."
```

Normal debate execution without document rewriting.

## Rewriter Behavior

### Processing Rules

The rewriter agent:

1. **Reads both inputs**: Original document + conclusion.md
2. **Applies recommendations aggressively**: All recommendations are applied without asking clarifying questions
3. **Resolves contradictions**: Chooses the most consistent option when recommendations conflict
4. **Preserves unchanged sections**: Sections without recommendations remain unchanged
5. **Maintains structure**: Document structure is preserved unless conclusion.md recommends changes
6. **Adds inline comments sparingly**: Only when absolutely necessary (estimated <5% of rewrites)

### Recommendation Application

| Recommendation Type | Behavior |
|---------------------|----------|
| Remove section | Section is removed from output |
| Update terminology | Terminology is updated throughout |
| Add content | New content is added at appropriate location |
| Reorganize | Structure is reorganized as specified |
| Contradictory | Most consistent option chosen automatically |
| Ambiguous | Best effort interpretation, inline comment if necessary |

### What the Rewriter Avoids

- Removing important sections unless explicitly instructed
- Leaving "TODO" or placeholder text
- Asking user for clarification
- Making changes beyond what's in conclusion.md

## File Format Support

### Supported Formats

| Format | Extension | Support Level |
|--------|-----------|---------------|
| Word Document | .docx | MUST (Full) |
| Markdown | .md | MUST (Full) |
| Plain Text | .txt | MUST (Full) |
| Rich Text | .rtf | SHOULD (Best effort) |
| OpenDocument | .odt | SHOULD (Best effort) |

### Unsupported Formats

Clear error message when unsupported format is provided:

```
Error: Unsupported file format '.pdf'. Supported formats: .docx, .md, .txt, .rtf, .odt
```

## Configuration

### CLI Flag

- **Flag**: `--make-review`
- **Required**: No
- **Effect**: Enables document rewriting after debate

### Timestamp Format

Rewritten filenames use UTC timestamps:

```
{original_name}_{YYYYMMDD_HHMMSS}.{extension}
```

Example: `prd_20260217_123456.docx`

### Metadata Preservation

Where supported by file format:
- Author information
- Creation/modification dates
- Document properties

## Error Handling

### Graceful Failure

The system handles errors without crashing the main workflow:

| Error Scenario | Behavior |
|----------------|----------|
| Original file corrupted/unreadable | Log error, continue without crashing |
| conclusion.md missing/empty | Create copy of original with note about no changes |
| Rewriter agent fails partway through | Preserve debate results (conclusion.md, metadata.json) |
| Unsupported file format | Clear error message with supported formats list |
| Output directory not writable | Error before debate starts |

### Error Reporting

Rewriter errors are reported in CLI output with sufficient detail for debugging.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Original file deleted during debate | Error logged, graceful handling |
| Malformed conclusion.md recommendations | Best effort interpretation |
| Rewritten document would exceed size limits | Warning, attempt completion |
| Mixed language documents | Preserve original languages |
| Documents with binary data/images | Preserve on best-effort basis |
| Very large documents (>100 pages) | May require special handling/timeouts |
| Same input file used multiple times | Each run creates new timestamped output |
| Documents with tracked changes/comments | Preserve on best-effort basis |
| Output file with same timestamped name exists | Overwrite (user responsibility) |

## Success Criteria

- **SC-001**: Users can obtain rewritten document with single CLI flag
- **SC-002**: 95%+ of recommendations applied without user intervention
- **SC-003**: Rewritten document generated within 60 seconds after debate
- **SC-004**: Document sections without recommendations remain unchanged (100%)
- **SC-005**: Corrupted/unreadable files handled without crashing workflow
- **SC-006**: Clear error messages for unsupported formats (100%)
- **SC-007**: File metadata preserved where format allows (90%+)
- **SC-008**: Contradictory recommendations resolved without asking user (100%)
- **SC-009**: Original document copy is bit-for-bit identical to input
- **SC-010**: Rewritten filename follows specified format with valid timestamp (100%)

## Assumptions

1. Original document available at debate execution time
2. conclusion.md contains actionable recommendations (not just general feedback)
3. LLM has sufficient context window to process document + conclusion together
4. Document formatting preserved on "best effort" basis for .docx files
5. Rewriter agent uses same LLM configuration as other participants unless specified
6. Inline comments added only when absolutely necessary (<5% of rewrites)
7. Timestamp format uses UTC to avoid timezone ambiguity
8. Users compare original and rewritten documents manually (no diff tool provided)
9. Rewriter agent does not verify semantic correctness of applied changes
10. Large files (>10MB) may require special handling or timeouts

## Rewriter Agent Logic

### Input

- Original document copy (from `{run-id}` directory)
- conclusion.md file (from same directory)

### Processing

1. Parse conclusion.md for recommendations
2. Read original document content
3. Apply recommendations in order of priority
4. Resolve contradictions automatically
5. Preserve sections without recommendations
6. Maintain document structure unless changes specified

### Output

- New document with all recommendations applied
- Timestamped filename in same directory as original copy
- Same file extension as original
