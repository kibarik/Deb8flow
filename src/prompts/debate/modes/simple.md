# Simple Mode Debate Template

You are simulating a product committee debate about the following question:

## Question

{question}

## Context (PRD excerpt)

{topic}

## Full PRD Content

{prd_content}

---

## Language

LANGUAGE: {language}

## Participants

You need to generate a realistic debate between two participants:
- **PRO** (arguing FOR the project): {pro_prompt}
- **CON** (arguing AGAINST the project): {con_prompt}

## Debate Structure

Generate a debate following this exact structure:

**PRO (opening):** [200-300 words arguing for the project]

**CON (opening):** [200-300 words arguing against the project]

**PRO (rebuttal):** [150-200 words responding to CON's opening]

**CON (rebuttal):** [150-200 words responding to PRO's rebuttal]

**PRO (final):** [100-150 words closing argument]

**CON (final):** [100-150 words closing argument]

**JUDGE:** After reviewing both arguments, WINNER: [PRO or CON]. [Brief 2-3 sentence explanation]

## Guidelines

- Make the arguments specific to the actual PRD content
- The PRO should focus on technical feasibility and benefits
- The CON should focus on risks, costs, and concerns
- The winner should be determined by who made stronger, more convincing arguments
- Be detailed and specific, not generic

Begin the debate now:
