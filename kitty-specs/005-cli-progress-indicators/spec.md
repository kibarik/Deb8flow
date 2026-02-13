# Specification: CLI Progress Indicators for Document Debate

## Overview

Add real-time progress tracking to the document debate CLI workflow to eliminate uncertainty during long-running operations. Users currently experience silence for extended periods (1+ minutes) with no indication whether the system is working or has hung.

## Problem Statement

When users run `document_debate_cli.py`, there is no visual feedback during execution:
- Users cannot tell if the workflow is progressing or has stalled
- No visibility into which step is currently running
- Uncertainty leads to user anxiety and potential premature termination

## Goals

- Provide clear, real-time progress indication during workflow execution
- Reduce user uncertainty about system status
- Maintain flexibility for different verbosity preferences

## Actors

| Actor | Description | Interests |
|-------|-------------|-----------|
| CLI User | Person running document debate commands | Needs visibility into workflow progress, assurance system is working |

## User Scenarios

### Scenario 1: Normal Progress Display
**Actor**: CLI User

**Trigger**: User runs a document debate command without `--verbose` flag

**Preconditions**:
- Document debate CLI is installed
- User has a valid document and topic/question

**Main Flow**:
1. User executes: `python3 document_debate_cli.py --docx 'document.docx' --request "question"`
2. Workflow starts and displays initial "Starting workflow..." message
3. Each major step displays progress (e.g., "Step 2/5: Generating pro arguments...")
4. User sees continuous updates as workflow progresses
5. Workflow completes with success/failure message

**Postconditions**:
- User has confidence system was working throughout execution
- Output is readable and not overwhelming

### Scenario 2: Verbose Mode
**Actor**: CLI User

**Trigger**: User runs command with `--verbose` flag

**Preconditions**:
- Document debate CLI is installed
- User wants detailed diagnostic information

**Main Flow**:
1. User executes: `python3 document_debate_cli.py --docx 'document.docx' --request "question" --verbose`
2. Workflow starts and displays detailed step-by-step progress
3. Each sub-step within major steps is displayed
4. Timing information and internal operations are shown
5. Workflow completes with comprehensive execution summary

**Postconditions**:
- User has detailed insight into execution
- Useful for debugging or understanding workflow behavior

### Scenario 3: Quiet Mode
**Actor**: CLI User

**Trigger**: User runs command with `--quiet` flag

**Preconditions**:
- Document debate CLI is installed
- User wants minimal output

**Main Flow**:
1. User executes: `python3 document_debate_cli.py --docx 'document.docx' --request "question" --quiet`
2. Workflow runs with minimal progress indication
3. Only critical messages (errors, final result) are displayed
4. Workflow completes

**Postconditions**:
- Clean, minimal output
- Still shows that system is working (perhaps via spinner or minimal status)

## Functional Requirements

### FR-001: Step Progress Display
The system MUST display which step is currently executing during workflow.

**Acceptance Criteria**:
- Each major workflow step is labeled with its position (e.g., "Step 2/5")
- Step name clearly describes what is happening
- Progress updates appear in real-time as steps transition

### FR-002: Verbose Mode Flag
The system MUST support a `--verbose` flag to enable detailed progress output.

**Acceptance Criteria**:
- `--verbose` flag is recognized by CLI
- When enabled, shows sub-step progress within major steps
- Displays additional execution details (timing, operations)
- Works with all document debate commands

### FR-003: Default Verbosity Level
The system MUST display detailed step-by-step progress by default (without flags).

**Acceptance Criteria**:
- No flags required for basic progress visibility
- Shows each major step with position indicator
- Balance between informative and not overwhelming

### FR-004: Progress Indicator During Waits
The system MUST show activity during long-running operations (LLM calls, processing).

**Acceptance Criteria**:
- Visual indicator (spinner, pulsing text, or similar) during waits
- Clear that system is working, not hung
- Indicator disappears when operation completes

### FR-005: Quiet Mode Flag
The system MAY support a `--quiet` flag for minimal output.

**Acceptance Criteria**:
- `--quiet` flag is recognized by CLI
- Only critical messages and final results displayed
- Still shows minimal activity indicator during waits

## Non-Functional Requirements

### NFR-001: Performance
Progress indicators MUST NOT significantly slow workflow execution.
- Progress display overhead: < 5% of total execution time
- No blocking I/O for progress updates

### NFR-002: Compatibility
Progress display MUST work across supported platforms.
- Compatible with macOS, Linux, Windows terminals
- Handles terminal width variations gracefully
- No progress-related crashes on any platform

### NFR-003: Output Clarity
Progress messages MUST be clear and actionable.
- Human-readable step descriptions
- Consistent formatting throughout workflow
- No technical jargon without context

## Out of Scope

The following are explicitly out of scope for this feature:

- Web-based progress tracking dashboard
- Real-time progress streaming to external systems
- Progress persistence or resume capability
- Historical progress tracking across multiple runs

## Assumptions

1. The current workflow runs sequentially through discrete steps
2. Long-running operations are primarily LLM API calls
3. Users primarily interact via terminal/CLI
4. Terminal supports basic ANSI codes for cursor control
5. Current logging infrastructure can be extended for progress

## Dependencies

- Existing document debate workflow infrastructure
- LLM API integration layer
- CLI argument parsing system

## Success Criteria

1. **Reduced User Uncertainty**: Users can always see which step is executing
2. **No Hanging Perception**: Visual activity during all operations > 5 seconds
3. **Verbosity Flexibility**: Three levels available (quiet, default, verbose)
4. **Platform Compatibility**: Progress display works on macOS, Linux, Windows
5. **Minimal Overhead**: Progress tracking adds less than 5% execution time

## Key Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| Workflow Step | A discrete stage in the debate workflow | Name, position (current/total), status, sub-steps |
| Progress Level | User's preference for output detail | quiet, default, verbose |
| Progress Event | A real-time update about execution | Step name, sub-step (optional), timestamp |
