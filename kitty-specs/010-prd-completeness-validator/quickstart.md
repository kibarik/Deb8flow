# Quickstart Guide: PRD Completeness Validator

**Feature**: 010-prd-completeness-validator
**Version**: 1.0
**Last Updated**: 2025-02-15

## Overview

The PRD Completeness Validator is a CLI tool that validates Product Requirements Documents against a predefined template using AI analysis. It provides scores, identifies gaps, and suggests improvements.

## Prerequisites

1. **Deb8flow installed**:
   ```bash
   pip install -e /path/to/Deb8flow
   ```

2. **OpenAI API key** set in environment:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

3. **PRD document** in markdown format

## Basic Usage

### Validate a PRD

```bash
python main.py --check-prd path/to/prd.md
```

**Output**:
- Console summary with score, missing sections, and top recommendations
- Detailed `prd_review.md` file generated alongside the PRD

### Console Output Only

```bash
python main.py --check-prd path/to/prd.md --output-format console
```

### File Output Only

```bash
python main.py --check-prd path/to/prd.md --output-format file
```

## Pipeline Integration

### Validate Before Debate (with threshold)

```bash
python main.py --debate-mode=committee --prd path/to/prd.md --check-prd --min-score 6
```

**Behavior**:
- Validates PRD before starting debate
- If score >= 6: Proceed to debate
- If score < 6: Prompt for user choice

## Understanding the Output

### Score Interpretation

| Score | Band | Meaning |
|-------|------|---------|
| 9-10 | Excellent | All sections present with comprehensive content |
| 7-8 | Good | All sections present with adequate content |
| 5-6 | Adequate | Most sections present, some gaps |
| 3-4 | Poor | Many sections missing or minimal |
| 0-2 | Fail | PRD is essentially empty |

### Report Sections

1. **Executive Summary**: Overall score and one-paragraph assessment
2. **Section-by-Section Analysis**: Detailed feedback for each section
3. **Recommendations by Priority**: Actionable improvements
4. **Best Practices Reference**: Links to examples
5. **Next Steps**: How to improve and re-validate

## PRD Template

The validator checks for these 10 required sections:

1. **Executive Summary** - Problem, Solution, Success Criteria
2. **Background & Context** - Market situation, User pain points
3. **Goals & Success Metrics** - SMART objectives, Key metrics
4. **User Personas** - Target users, Use cases
5. **Functional Requirements** - Core features, User stories
6. **Non-Functional Requirements** - Performance, Security, Scalability
7. **Technical Constraints** - Tech stack, Integrations
8. **Risks & Mitigations** - Known risks, Contingency plans
9. **Timeline & Milestones** - Phases, Key dates
10. **Open Questions** - Unresolved items, Decision points

## Development Workflow

### For Contributors

1. **Write a test**:
   ```bash
   # Create test file
   touch tests/test_prd_validator_node.py
   ```

2. **Implement the node**:
   ```bash
   # Create node file
   touch nodes/prd_validator_node.py
   ```

3. **Add the prompt**:
   ```bash
   # Create system prompt
   touch prompts/prd_validator_system.md
   ```

4. **Integrate CLI**:
   ```bash
   # Modify main.py
   # Add --check-prd argument parsing
   # Add validation logic
   ```

5. **Run tests**:
   ```bash
   pytest tests/test_prd_validator_node.py
   ```

6. **Manual testing**:
   ```bash
   # Create a sample PRD
   cat > test_prd.md << 'EOF'
   ## Executive Summary
   This product solves X problem...

   ## Background & Context
   Market analysis shows...
   EOF

   # Run validation
   python main.py --check-prd test_prd.md
   ```

## Examples

### Example 1: Complete PRD

**Input PRD** (`complete_prd.md`):
```markdown
## Executive Summary
Our product helps small businesses manage inventory more efficiently.
Current solutions are expensive and complex.
Success: 1000 customers in year 1.

## Background & Context
Small businesses struggle with inventory tracking.
Spreadsheets are error-prone.
Existing tools cost $500+/month.

## Goals & Success Metrics
- Acquire 1000 customers in year 1
- Achieve 80% monthly active user rate
- <5 minute onboarding time

## User Personas
- Sarah: Small business owner, 10-50 employees
- Mike: Inventory manager, needs real-time data

## Functional Requirements
- User can add/edit inventory items
- System sends low-stock alerts
- Dashboard shows inventory trends

## Non-Functional Requirements
- Performance: Dashboard loads in <2 seconds
- Security: Data encrypted at rest and in transit
- Scalability: Supports 10,000 concurrent users

## Technical Constraints
- Built with Python 3.12+
- Uses PostgreSQL for data storage
- Integrates with Shopify API

## Risks & Mitigations
- Risk: Shopify API changes
  Mitigation: Version pinning and monitoring
- Risk: Data loss
  Mitigation: Daily backups with 30-day retention

## Timeline & Milestones
- Month 1-2: MVP development
- Month 3: Beta testing with 10 users
- Month 4: Public launch

## Open Questions
- Should we support multi-currency?
- What's the pricing model?
```

**Validation Result**:
```
Score: 9/10 (Excellent)

✅ All 10 sections present
✅ Comprehensive content throughout
💡 Consider adding competitive analysis
```

### Example 2: Incomplete PRD

**Input PRD** (`incomplete_prd.md`):
```markdown
## Executive Summary
Building a todo app.

## Goals
Help users organize tasks.

## Features
- Add tasks
- Delete tasks
```

**Validation Result**:
```
Score: 2/10 (Fail)

❌ Missing Sections (7/10):
  • Background & Context
  • User Personas
  • Functional Requirements
  • Non-Functional Requirements
  • Technical Constraints
  • Risks & Mitigations
  • Timeline & Milestones
  • Open Questions

⚠️ Underdeveloped Sections:
  • Executive Summary (only 3 words)
  • Goals (no success metrics)

💡 Recommendations:
  1. Expand Executive Summary with problem statement
  2. Add Background section with market context
  3. Add User Personas with target users
  4. Add all missing sections from template
```

## Troubleshooting

### "File not found" Error

**Problem**:
```
❌ Error: PRD file not found: path/to/prd.md
```

**Solution**: Use absolute path or check relative path from current directory.

### Low Score Despite Complete PRD

**Problem**: Score is 5-6 despite having all sections.

**Solution**: Check section depth. Each section needs 50-100+ words with specific details.

### API Key Error

**Problem**:
```
EnvironmentError: Missing environment variable: OPENAI_API_KEY
```

**Solution**:
```bash
export OPENAI_API_KEY=sk-...
```

## Next Steps

1. **Run validation on your PRD**:
   ```bash
   python main.py --check-prd your_product_prd.md
   ```

2. **Review the generated report**:
   ```bash
   cat your_product_review.md
   ```

3. **Address recommendations** and re-validate

4. **Use in debate workflow** when score is 7+

## References

- **Full Specification**: `kitty-specs/010-prd-completeness-validator/spec.md`
- **Implementation Plan**: `kitty-specs/010-prd-completeness-validator/plan.md`
- **Data Model**: `kitty-specs/010-prd-completeness-validator/data-model.md`
- **CLI Contract**: `kitty-specs/010-prd-completeness-validator/contracts/cli-interface.md`
