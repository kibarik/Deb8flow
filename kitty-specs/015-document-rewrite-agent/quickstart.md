# Quickstart Guide: Document Rewrite Agent

**Feature**: 015-document-rewrite-agent
**Version**: 1.0.0
**Last Updated**: 2026-02-17

## Overview

The Document Rewrite Agent automatically updates your source documents based on debate conclusions. Simply add the `--make-review` flag when running a debate, and the system will create an updated version of your document incorporating all recommendations from the debate.

## Prerequisites

- Python 3.12 or higher
- Deb8flow installed with all dependencies
- Source document in supported format (.docx, .md, .txt)
- Valid debate configuration

## Supported File Formats

| Format | Extension | Read | Write | Formatting Preservation |
|--------|-----------|------|-------|-------------------------|
| Word Document | .docx | ✅ | ✅ | Full (best effort) |
| Markdown | .md | ✅ | ✅ | Full |
| Plain Text | .txt | ✅ | ✅ | None |
| Rich Text | .rtf | ⚠️ | ⚠️ | Limited |

**Note**: .rtf support is experimental. Stick to .docx, .md, and .txt for best results.

## Basic Usage

### Product Committee Debates

```bash
python product_committee.py \
  --prd path/to/document.docx \
  --question "What's the potential of this project?" \
  --make-review
```

**What happens**:
1. Debate runs normally with all rooms
2. Original document is copied to `{run-id}/` directory
3. After debate completes, `conclusion.md` is generated
4. Rewriter agent automatically processes the document
5. Rewritten document saved as `{run-id}/{name}_{timestamp}.{ext}`

### Document Debates

```bash
python document_debate_cli.py \
  --docx path/to/document.docx \
  --request "Is this document clear?" \
  --make-review
```

## Output Structure

After running with `--make-review`, your output directory will contain:

```
{run-id}/
├── conclusion.md                    # Debate conclusions with recommendations
├── {original_name}.{ext}            # Original document copy
├── {original_name}_{timestamp}.{ext} # Rewritten document
├── file_metadata.json               # Preserved metadata
└── metadata.json                    # Run metadata
```

**Example**:
```
RUN_20260217_123456_project_potential/
├── conclusion.md
├── prd.docx                         # Original copy
├── prd_20260217_123456.docx         # Rewritten version
├── file_metadata.json
└── metadata.json
```

## Understanding the Rewrite

The rewriter agent:

1. **Reads** both your original document and the debate conclusion
2. **Extracts** all actionable recommendations from `conclusion.md`
3. **Converts** your document to markdown (if not already)
4. **Applies** all recommendations aggressively:
   - Removes sections marked for removal
   - Updates content as recommended
   - Adds new content where suggested
   - Resolves contradictions independently
5. **Preserves** sections without recommendations
6. **Converts** back to the original format
7. **Saves** with timestamp-based filename

## Rewriter Behavior

### What Gets Changed

The rewriter applies recommendations from these conclusion sections:
- **Recommended Improvements**: Changes to improve quality
- **TPM Position Analysis**: Structural and content updates
- **Recommendations by Role**: Specific suggestions from debate participants

### What Stays the Same

- Sections without any corresponding recommendations
- Basic document structure (unless conclusion recommends restructuring)
- File metadata (preserved in original copy, best-effort in rewrite)

### Edge Cases

**Ambiguous recommendations**: If the rewriter cannot apply a recommendation unambiguously, it adds an inline comment:
```html
<!-- REVIEW NOTE: Could not apply recommendation "X" - please review manually -->
```

**Contradictory recommendations**: The rewriter resolves conflicts independently by choosing the most consistent option.

**No recommendations**: If `conclusion.md` has no recommendations, the rewriter creates a copy with a note explaining no changes were made.

## Troubleshooting

### Rewrite Not Running

**Symptom**: No rewritten document created

**Possible causes**:
1. `--make-review` flag not provided
2. Debate failed before conclusion was generated
3. Original file not found

**Solution**: Check the CLI output for error messages. Verify the original file path is correct.

### Formatting Lost

**Symptom**: Rewritten document has less formatting than original

**Cause**: Format conversion limitations (especially .docx ↔ markdown)

**Mitigation**:
- The rewriter uses best-effort formatting preservation
- Complex formatting (tables, images) may not be perfectly preserved
- Compare with original copy in the same directory

### Rewrite Failed

**Symptom**: Error message about rewrite failure

**Behavior**:
- Original copy is preserved
- Debate results (conclusion.md) are still available
- Check error message for specific issue

**Common failures**:
- LLM timeout: Document too large or model slow
- Conversion error: Corrupted or unsupported file
- Write error: Disk full or permissions issue

### Large Documents

**Symptom**: Timeout or incomplete rewrite

**Cause**: Document exceeds LLM context window

**Solution** (future enhancement):
- The system will implement chunking for large documents
- For now, consider splitting large documents

## Advanced Usage

### Checking Rewrite Quality

Compare original and rewritten documents:

```bash
# Original copy
RUN_20260217_123456/prd.docx

# Rewritten version
RUN_20260217_123456/prd_20260217_123456.docx
```

Use your diff tool of choice to see changes:
- VS Code: Select both files → Right-click → "Compare Selected"
- Git: `git diff --no-index original.docx rewritten.docx`
- Online: Use tools like DiffNow or Draftable

### Understanding Metadata

Check `file_metadata.json` to see:
- Original file information
- Preserved metadata (author, dates)
- Rewrite statistics (duration, recommendations applied)

```json
{
  "original_file": "/path/to/original.docx",
  "preserved_metadata": {
    "author": "John Doe",
    "created": "2026-01-15T10:30:00Z",
    "modified": "2026-02-01T14:20:00Z"
  },
  "rewrite_metadata": {
    "recommendations_count": 7,
    "recommendations_applied": 7,
    "duration_seconds": 45.2
  }
}
```

## Best Practices

1. **Keep original copies**: The `{run-id}` directory preserves your original document
2. **Review before using**: Always review the rewritten document before using it
3. **Version control**: Consider committing both versions to git for comparison
4. **Iterate**: You can run multiple debates with `--make-review` to iteratively improve
5. **Format choice**: Use .md or .docx for best formatting preservation

## Limitations

- **Formatting**: Complex formatting may not be perfectly preserved
- **Large files**: Very large files (>10MB) may timeout
- **Binary content**: Embedded images and binary data not supported
- **Tracked changes**: Tracked changes in .docx are not preserved
- **Languages**: Works best with English and major European languages

## Getting Help

If you encounter issues:

1. Check the CLI output for error messages
2. Review `file_metadata.json` for details
3. Compare original and rewritten documents
4. Check the troubleshooting section above
5. Report issues with: CLI output, file formats, document size

## Next Steps

- Run your first debate with `--make-review`
- Review the rewritten document
- Iterate based on results
- Check `conclusion.md` for detailed recommendations

---

**Happy rewriting! 📝✨**
