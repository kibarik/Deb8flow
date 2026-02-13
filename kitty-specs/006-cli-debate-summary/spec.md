# CLI Debate Summary Output

## Overview

Add a summary output feature to the document debate CLI tool that displays key debate outcomes after winner selection. This enables users to quickly understand decisions made during AI debates without reviewing the full dialogue.

## Background

The current document debate CLI tool (`document_debate_cli.py`) conducts AI debates on document content but does not provide a concise summary of outcomes. Users must read through the full debate transcript to understand what was decided, which is time-consuming for long debates.

## Goals

1. Display a concise summary of debate outcomes in the console
2. Map each original question to its final decided answer
3. Show the summary immediately after the winner is selected
4. Maintain backward compatibility with existing CLI usage

## Actors

- **CLI User**: Runs the debate tool and needs to understand outcomes quickly

## User Scenarios & Testing

### Scenario 1: Single Question Debate

**Given** a user runs the CLI with a single question about a document
**When** the AI debate completes and a winner is selected
**Then** the console displays:
- The original question
- The final answer agreed upon by the debate participants

**Example output**:
```
=== DEBATE SUMMARY ===

Q: какой потенциал у этого проекта?
A: [Final answer content]

=======================
```

### Scenario 2: Multiple Questions

**Given** a user runs the CLI with multiple questions
**When** the debate completes
**Then** each question-answer pair is displayed in sequence

### Scenario 3: No Debate/Winner Selection Fails

**Given** a debate does not complete normally or winner selection fails
**When** the program reaches the summary stage
**Then** no summary is displayed or an appropriate message is shown

## Functional Requirements

1. **FR1**: After winner selection, the tool MUST output a summary section to the console
2. **FR2**: The summary MUST contain each original question paired with its final answer
3. **FR3**: The summary MUST be formatted for readability with clear question/answer separation
4. **FR4**: The summary MUST appear after all debate dialogue is complete
5. **FR5**: The tool MUST handle edge cases (no winner selected, empty questions) gracefully

## Success Criteria

1. **SC1**: Users can identify debate outcomes in under 10 seconds of reading the summary
2. **SC2**: Summary output does not break existing CLI functionality
3. **SC3**: Summary format is consistent across all debate runs

## Out of Scope

- Saving summaries to files
- Storing summary history
- Exporting summaries to different formats
- Interactive summary navigation
- Filtering or searching within summaries

## Assumptions

1. The debate process already tracks questions and final answers internally
2. Winner selection occurs before the summary stage
3. The tool is run in a terminal/console environment
4. Questions are provided in Russian (as shown in the example)

## Dependencies

- Existing `document_debate_cli.py` codebase
- Current debate winner selection logic

## Notes

- The user specifically requested console output, not file output
- Format should be "question → answer" pairing as specified
- Summary should be brief enough to avoid re-reading the full debate
