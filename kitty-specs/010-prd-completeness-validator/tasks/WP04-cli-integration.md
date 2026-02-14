---
work_package_id: WP04
title: CLI Integration
lane: planned
dependencies: []
subtasks: [T017, T018, T019, T020]
history:
- date: 2025-02-15
  action: Created
  reason: Initial task breakdown
---

# Work Package: CLI Integration

**Work Package ID**: WP04
**Feature**: 010-prd-completeness-validator
**Status**: Planned
**Estimated Size**: ~250 lines

## Objective

Wire up the PRD validator to main.py CLI with proper argument handling, threshold checking, and user prompts for below-threshold PRDs. This completes the user-facing CLI integration.

## Context

You are integrating the PRD validator into the main.py CLI entry point. This work package connects all the previous work (WP01-WP03) to create a complete user experience.

**Key References**:
- CLI Contract: `kitty-specs/010-prd-completeness-validator/contracts/cli-interface.md`
- Quickstart: `kitty-specs/010-prd-completeness-validator/quickstart.md`

**Dependencies**:
- WP02: Needs complete PRDValidatorNode implementation
- WP03: Needs report generation for full output

**Technical Context**:
- Modify main.py to add --check-prd mode
- Handle exit codes correctly (0=success, 1=error, 2=invalid args)
- Integrate with existing debate workflow (optional)
- Preserve existing CLI functionality

## Subtasks

### T017: Wire Up --check-prd Mode in main.py

**Purpose**: Integrate PRD validator into main.py with proper conditional flow.

**Implementation Steps**:

1. **Locate the main function in main.py**:
   ```python
   async def main():
       setup_logging()
       validate_env()
       logger = logging.getLogger("main")
       # ... existing code ...
   ```

2. **Add PRD validation mode check**:
   ```python
   async def main():
       setup_logging()
       validate_env()
       logger = logging.getLogger("main")

       args = parse_args()

       # PRD validation mode
       if args.check_prd:
           from nodes.prd_validator_node import PRDValidatorNode
           from configurations.llm_config import OpenAILLMConfig
           import sys

           try:
               # Initialize LLM config
               llm_config = OpenAILLMConfig(
                   model_name="gpt-4",
                   openai_api_key=os.getenv("OPENAI_API_KEY")
               )

               # Create validator
               validator = PRDValidatorNode(llm_config=llm_config)

               # Validate PRD
               result = validator.validate_prd(
                   prd_path=args.check_prd,
                   output_format=args.output_format
               )

               # Check threshold if specified
               if args.min_score:
                   from utils.console_formatter import print_warning
                   score = result['validation_result'].overall_score
                   if score < args.min_score:
                       print_warning(
                           f"PRD score {score}/10 is below threshold {args.min_score}/10"
                       )
                       # Continue to user choice prompt in T018
                       handle_low_score(result, args.min_score)

               # Success exit
               sys.exit(0)

           except FileNotFoundError as e:
               from utils.console_formatter import print_error
               print_error(str(e))
               sys.exit(1)

           except Exception as e:
               logger.error(f"Validation failed: {e}", exc_info=True)
               from utils.console_formatter import print_error
               print_error(f"Validation failed: {str(e)}")
               sys.exit(1)

       # Existing debate workflow
       logger.info("[bold green]Starting debate workflow...[/]")
       workflow = DebateWorkflow()
       # ... rest of existing code ...
   ```

3. **Create helper for LLM config initialization**:
   ```python
   def get_llm_config():
       """
       Get LLM configuration from environment.

       Returns OpenAILLMConfig with API key from environment.
       """
       api_key = os.getenv("OPENAI_API_KEY")
       if not api_key:
           raise EnvironmentError("OPENAI_API_KEY environment variable not set")

       return OpenAILLMConfig(
           model_name="gpt-4",
           openai_api_key=api_key
       )
   ```

**Files Modified**:
- `main.py` (~80 lines added)

**Validation**:
- [ ] `python main.py --check-prd path/to/prd.md` runs validation
- [ ] `python main.py --check-prd path/to/prd.md --output-format console` works
- [ ] `python main.py --check-prd path/to/prd.md --output-format file` works
- [ ] Existing debate workflow still works
- [ ] Exit code 0 on successful validation
- [ ] Exit code 1 on error
- [ ] ImportError handled if node not found

**Notes**:
- Add PRD validation BEFORE existing debate workflow
- Use sys.exit() to prevent debate workflow from running
- Preserve all existing CLI functionality
- Follow existing error handling patterns in main.py

---

### T018: Implement handle_low_score Threshold Check

**Purpose**: Create user interaction flow when PRD score is below threshold.

**Implementation Steps**:

1. **Add handle_low_score function to main.py**:
   ```python
   def handle_low_score(validation_result: dict, min_score: int) -> None:
       """
       Handle PRD score below minimum threshold.

       Prompts user with options when validation score is below threshold.

       Args:
           validation_result: Result from PRD validation
           min_score: Minimum acceptable score
       """
       from utils.console_formatter import console
       import sys

       score = validation_result['validation_result'].overall_score

       # Display warning panel
       console.print("\n[bold yellow]⚠️  PRD Score Below Threshold[/]\n")
       console.print(f"Score: [bold]{score}/10[/] (Threshold: [bold]{min_score}/10[/])\n")
       console.print(
           "The PRD appears incomplete. Continuing may result in an unfocused debate.\n"
       )

       # Get recommendations
       recommendations = validation_result['validation_result'].recommendations[:3]

       # Display options
       console.print("Options:")
       console.print("  [bold]1.[/] View recommendations and abort")
       console.print("  [bold]2.[/] View recommendations and continue anyway")
       console.print("  [bold]3.[/] Continue without viewing\n")

       # Get user choice
       while True:
           try:
               choice = input("Enter choice (1-3): ").strip()

               if choice == "1":
                   # Show recommendations and abort
                   console.print("\n[bold]Top Recommendations:[/]")
                   for i, rec in enumerate(recommendations, 1):
                       console.print(f"  {i}. {rec}")
                   console.print("\n[yellow]Aborting debate. Please improve the PRD and re-validate.[/]")
                   sys.exit(1)

               elif choice == "2":
                   # Show recommendations and continue
                   console.print("\n[bold]Top Recommendations:[/]")
                   for i, rec in enumerate(recommendations, 1):
                       console.print(f"  {i}. {rec}")
                   console.print("\n[green]Continuing with debate despite low score...[/]")
                   break

               elif choice == "3":
                   # Continue without viewing
                   console.print("\n[green]Continuing with debate...[/]")
                   break

               else:
                   console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/]")

           except (KeyboardInterrupt, EOFError):
               console.print("\n\n[yellow]Aborted by user.[/]")
               sys.exit(1)
   ```

2. **Update T017 code to call handle_low_score**:
   ```python
   # In main.py, within the --check-prd block
   if args.min_score:
       score = result['validation_result'].overall_score
       if score < args.min_score:
           from utils.console_formatter import print_warning
           print_warning(
               f"PRD score {score}/10 is below threshold {args.min_score}/10"
           )
           handle_low_score(result, args.min_score)
   ```

**Files Modified**:
- `main.py`

**Validation**:
- [ ] Function displays when score < threshold
- [ ] Option 1 shows recommendations and exits with code 1
- [ ] Option 2 shows recommendations and continues
- [ ] Option 3 continues without showing recommendations
- [ ] Invalid choices are rejected with message
- [ ] Ctrl+C handles gracefully
- [ ] Top 3 recommendations shown

**Notes**:
- This is for pipeline integration scenario
- User can always override low score
- Recommendations limited to top 3 for readability
- Follow CLI contract from contracts/cli-interface.md

---

### T019: Add User Choice Prompt for Below-Threshold PRDs

**Purpose**: Refine the user interaction for below-threshold PRDs with better UX.

**Implementation Steps**:

1. **Enhance handle_low_score with more context**:
   ```python
   def handle_low_score(validation_result: dict, min_score: int) -> None:
       """Handle PRD score below minimum threshold with enhanced UX."""
       from utils.console_formatter import console
       from rich.panel import Panel
       import sys

       score = validation_result['validation_result'].overall_score
       result = validation_result['validation_result']

       # Calculate gap
       gap = min_score - score

       # Build context message
       missing_count = len(result.missing_sections)
       underdeveloped_count = len(result.underdeveloped_sections)

       context_msg = f"""
   Score Gap: {gap} points needed
   Missing Sections: {missing_count}
   Underdeveloped Sections: {underdeveloped_count}
   """

       # Display warning panel with context
       console.print(Panel.fit(
           f"[bold yellow]⚠️  PRD Score Below Threshold[/]\n\n"
           f"Score: [bold]{score}/10[/] (Threshold: [bold]{min_score}/10[/])\n"
           f"{context_msg}"
           f"The PRD appears incomplete. Continuing may result in an unfocused debate.",
           title="Low Score Warning",
           border_style="yellow"
       ))

       # Show preview of recommendations
       console.print("\n[dim]Preview of recommendations:[/]")
       for i, rec in enumerate(result.recommendations[:2], 1):
           console.print(f"  {dim}{i}. {rec}[/]")

       # Display options
       console.print("\n[bold]Options:[/]")
       console.print("  [cyan]1[/]. View all recommendations and abort")
       console.print("  [cyan]2[/]. View all recommendations and continue anyway")
       console.print("  [cyan]3[/]. Continue without viewing recommendations")

       # Get user choice
       choice = get_user_choice()

       # Handle choice
       handle_user_choice(choice, validation_result, sys)
   ```

2. **Add helper functions**:
   ```python
   def get_user_choice() -> str:
       """Get and validate user choice input."""
       from utils.console_formatter import console

       while True:
           try:
               choice = input("\n[bold]Enter choice (1-3): [/]").strip()

               if choice in ["1", "2", "3"]:
                   return choice

               console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/]")

           except (KeyboardInterrupt, EOFError):
               console.print("\n\n[yellow]Aborted by user.[/]")
               sys.exit(1)

   def handle_user_choice(choice: str, validation_result: dict, sys_module) -> None:
       """Handle user's choice from low score prompt."""
       from utils.console_formatter import console
       import sys

       recommendations = validation_result['validation_result'].recommendations

       if choice == "1":
           # Show all recommendations and abort
           console.print("\n[bold]All Recommendations:[/]")
           for i, rec in enumerate(recommendations, 1):
               console.print(f"  {i}. {rec}")

           console.print("\n[yellow]Aborting debate. Please improve the PRD and re-validate.[/]")
           console.print(f"\n[dim]Re-run: python main.py --check-prd <prd_path>[/]")
           sys.exit(1)

       elif choice == "2":
           # Show all recommendations and continue
           console.print("\n[bold]All Recommendations:[/]")
           for i, rec in enumerate(recommendations, 1):
               console.print(f"  {i}. {rec}")

           console.print("\n[green]Continuing with debate despite low score...[/]")
           console.print("[dim](You may want to address the recommendations above)[/]")

       else:  # choice == "3"
           # Continue without viewing
           console.print("\n[green]Continuing with debate...[/]")
           console.print("[dim](Recommendations available in prd_review.md)[/]")
   ```

**Files Modified**:
- `main.py`

**Validation**:
- [ ] Warning panel shows score gap and section counts
- [ ] Preview shows first 2 recommendations
- [ ] All 3 options work correctly
- [ ] Choice 1 shows all recommendations before aborting
- [ ] Choice 2 shows all recommendations before continuing
- [ ] Choice 3 continues without showing recommendations
- [ ] Invalid choices rejected with clear message
- [ ] Keyboard interrupts handled gracefully

**Notes**:
- Enhanced UX with more context
- Preview helps user decide
- Clear re-run instruction in abort message
- Reference to prd_review.md in choice 3

---

### T020: Set Proper Exit Codes for Different Scenarios

**Purpose**: Ensure CLI returns correct exit codes for all scenarios.

**Implementation Steps**:

1. **Define exit code constants**:
   ```python
   # Exit codes
   EXIT_SUCCESS = 0
   EXIT_ERROR = 1
   EXIT_INVALID_ARGS = 2
   ```

2. **Update main.py with proper exit codes**:
   ```python
   async def main():
       setup_logging()
       validate_env()

       # Validate environment first
       try:
           validate_env()
       except EnvironmentError as e:
           from utils.console_formatter import print_error
           print_error(str(e))
           sys.exit(EXIT_ERROR)

       args = parse_args()

       # PRD validation mode
       if args.check_prd:
           try:
               # ... validation logic ...

               # Success
               sys.exit(EXIT_SUCCESS)

           except FileNotFoundError as e:
               from utils.console_formatter import print_error
               print_error(f"File not found: {args.check_prd}")
               print_error(f"Usage: python main.py --check-prd <path-to-prd>")
               sys.exit(EXIT_ERROR)

           except ValueError as e:
               from utils.console_formatter import print_error
               print_error(f"Invalid input: {str(e)}")
               sys.exit(EXIT_INVALID_ARGS)

           except Exception as e:
               logger.error(f"Validation failed: {e}", exc_info=True)
               from utils.console_formatter import print_error
               print_error(f"Validation failed: {str(e)}")
               sys.exit(EXIT_ERROR)

       # Existing debate workflow
       try:
           logger.info("[bold green]Starting debate workflow...[/]")
           workflow = DebateWorkflow()
           workflow_result = await workflow.run()
           # ... existing code ...
           sys.exit(EXIT_SUCCESS)

       except Exception as e:
           logger.error("Workflow failed: %s", str(e), exc_info=True)
           sys.exit(EXIT_ERROR)
   ```

3. **Add argument validation**:
   ```python
   def parse_args():
       """Parse and validate command line arguments."""
       parser = argparse.ArgumentParser(description="Deb8flow - AI Debate Framework")

       # ... existing arguments ...

       args = parser.parse_args()

       # Validate argument combinations
       if args.check_prd:
           if not os.path.exists(args.check_prd):
               parser.error(f"PRD file not found: {args.check_prd}")

           if args.min_score is not None and args.debate_mode:
               # Both --check-prd with --min-score AND --debate-mode is valid
               # This is the pipeline integration scenario
               pass

       return args
   ```

4. **Add exit code documentation**:
   ```python
   """
   Deb8flow - AI Debate Framework

   Exit Codes:
       0: Success
       1: Error (file not found, API failure, etc.)
       2: Invalid arguments

   Usage:
       # Validate PRD
       python main.py --check-prd path/to/prd.md

       # Validate with threshold
       python main.py --check-prd path/to/prd.md --min-score 6

       # Run debate
       python main.py --debate-mode=standard
   """
   ```

**Files Modified**:
- `main.py`

**Validation**:
- [ ] Exit code 0 on successful validation
- [ ] Exit code 1 on file not found
- [ ] Exit code 1 on API failure
- [ ] Exit code 2 on invalid arguments
- [ ] Exit code 1 on user abort (choice 1)
- [ ] Exit code 0 on user continue (choices 2, 3)
- [ ] Exit codes documented in docstring
- [ ] Error messages include usage hint

**Notes**:
- Exit codes per CLI contract in contracts/cli-interface.md
- Use sys.exit() not return (exit async main properly)
- File validation in parse_args() for early feedback
- Include usage hint in error messages

---

## Implementation Notes

**Order of Implementation**:
1. T017 first (main integration - skeleton)
2. T018 second (threshold handling - core logic)
3. T019 third (UX refinement - can parallel with T018)
4. T020 last (exit codes - final polish)

**Testing Strategy**:
- Manual testing of all CLI argument combinations
- Test exit codes with `$?` in bash
- Test user interaction flow manually
- Verify existing debate workflow still works

**Integration Points**:
- Uses PRDValidatorNode from WP02
- Uses console formatter from WP01
- Uses report generation from WP03
- Modifies main.py entry point
- Must preserve existing functionality

## Definition of Done

- [ ] All 4 subtasks completed
- [ ] `--check-prd` flag works standalone
- [ ] `--output-format` variations work
- [ ] `--min-score` threshold checking works
- [ ] User choice prompt displays correctly
- [ ] All exit codes correct
- [ ] Existing debate workflow preserved
- [ ] Error messages user-friendly
- [ ] Usage examples work per quickstart.md

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing debate workflow | Medium | High | Test all existing CLI arguments |
| Exit code confusion | Low | Medium | Document exit codes clearly |
| User input handling issues | Low | Low | Test with various inputs |
| Integration conflicts | Low | Medium | Add PRD mode before debate mode |

## Reviewer Guidance

**What to Verify**:
1. All `--check-prd` argument combinations work
2. Exit codes match CLI contract exactly
3. User choice prompt displays correctly
4. Existing debate workflow unchanged
5. Error messages are user-friendly
6. File validation happens early

**Common Issues to Check**:
- Exit code 0 vs 1 confusion
- Missing usage hints in error messages
- Debate workflow still runs without --check-prd
- User input validation (non-numeric input)
- File path handling (relative vs absolute)

**Testing Checklist**:
- [ ] `python main.py --check-prd valid_prd.md`
- [ ] `python main.py --check-prd nonexistent.md`
- [ ] `python main.py --check-prd valid_prd.md --min-score 9` (below threshold)
- [ ] `python main.py --check-prd valid_prd.md --min-score 3` (above threshold)
- [ ] Test each user choice (1, 2, 3)
- [ ] Test Ctrl+C during prompt
- [ ] Test existing `python main.py` (no args)
- [ ] Verify exit codes: `echo $?`

## Next Steps

After completing this work package:
1. Run `spec-kitty review WP04` to mark as ready for review
2. Proceed to WP05: Testing Coverage (depends on this WP)
3. Implementation command: `spec-kitty implement WP04 --base WP03`
