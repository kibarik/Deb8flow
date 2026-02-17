# CLI Debate Summary Output

## Overview

The CLI Debate Summary Output feature adds a summary display to the document debate CLI tool. It shows key debate outcomes after winner selection, enabling users to quickly understand decisions made during AI debates without reviewing the full dialogue.

## What It Does

This feature:

- Displays a concise summary of debate outcomes in the console
- Maps each original question to its final decided answer
- Shows the summary immediately after the winner is selected
- Maintains backward compatibility with existing CLI usage

## How It Works

### Architecture

The summary output is generated as a post-processing step after the debate winner is selected:

```
Debate Completion → Winner Selection → Summary Generation → Console Output
```

### Data Flow

1. Debate completes all rounds
2. Winner is selected by judge
3. Summary is extracted from debate state
4. Question-answer pairs are formatted
5. Summary is displayed to console

## Usage

### Single Question Debate

When running a debate with a single question:

```bash
python3 document_debate_cli.py --text "GitHub полезен для разработчиков"
```

**Output**:
```
=== DEBATE SUMMARY ===

Q: какой потенциал у этого проекта?
A: [Final answer content]

=======================
```

### Multiple Questions

When running a debate with multiple questions, each question-answer pair is displayed in sequence:

```
=== DEBATE SUMMARY ===

Q: Question 1?
A: Answer 1

Q: Question 2?
A: Answer 2

=======================
```

## Configuration

### Console Output Format

The summary format uses clear question/answer separation:

- **Q:** prefix for questions
- **A:** prefix for answers
- **Separator lines** for visual clarity
- **Brief content** to avoid re-reading full debate

### Edge Cases

| Scenario | Expected Behavior |
|----------|------------------|
| No debate/winner selection fails | No summary is displayed or appropriate message is shown |
| Empty questions | Graceful handling with clear messaging |
| Multiple questions | Sequential display of all Q&A pairs |

## Success Criteria

- **SC1**: Users can identify debate outcomes in under 10 seconds of reading the summary
- **SC2**: Summary output does not break existing CLI functionality
- **SC3**: Summary format is consistent across all debate runs

## Out of Scope

The following items are explicitly out of scope:

- Saving summaries to files
- Storing summary history
- Exporting summaries to different formats
- Interactive summary navigation
- Filtering or searching within summaries

## Implementation Notes

- The summary uses console output only (not file output)
- Format follows "question → answer" pairing structure
- Summary is brief enough to avoid re-reading the full debate
- Questions are preserved in their original language (e.g., Russian)
