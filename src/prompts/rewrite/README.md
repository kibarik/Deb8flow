# Rewrite Verification Prompts

These prompts are used for debate-based verification of document revisions.

## Files

- `pro_verification.md`: PRO agent argues revisions are properly incorporated
- `con_verification.md`: CON agent finds missing/incorrect implementations
- `judge_verdict.md`: Judge evaluates and returns verified/unverified lists

## Template Variables

When using these prompts, substitute the following variables:

- `{source_content}`: Original source document before revisions
- `{conclusion_content}`: Conclusion.md with revision items
- `{revised_content}`: Revised document after applying revisions
- `{round}`: Current debate round (e.g., "1/5")
- `{max_rounds}`: Maximum debate rounds
- `{verified_list}`: List of previously verified revision IDs
