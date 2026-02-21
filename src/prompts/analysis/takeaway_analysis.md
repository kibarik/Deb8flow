# Actionable Revision Recommendations

## Committee Question

{question}

---

## Debate Dialogue Summary

{dialogue_summary}

---

## Judge Verdict (Winner: {winner})

{verdict_explanation}

---

## Your Task

Based on the debate analysis, generate **{min_takeaways} to {max_takeaways} actionable revision recommendations** that will make this document strategically stronger.

Focus on: **WHAT specifically needs revision, WHERE it belongs, and HOW to improve it.**

---

## Output Format

Each recommendation must follow this exact pattern:

```
- **[CATEGORY]**: [Specific section/area] → [Actionable revision step]
```

**Valid Categories:**
- **ADD** = Content that must be added
- **CLARIFY** = Vague sections needing specificity
- **RESOLVE** = Contradictions or inconsistencies
- **REMOVE** = Unnecessary or conflicting content
- **KEEP** = Strengths to preserve (don't change these)

---

## Examples

```
- **ADD**: Section 2.4 Market Sizing → Include TAM/SAM/SOM breakdown with data sources and calculation methodology
- **CLARIFY**: Go-to-Market strategy section → Specify channel mix percentages (e.g., 60% direct sales, 40% partners) with justification
- **RESOLVE**: Team section (claims 5 engineers but budget for 8) → Either update team count or explain the discrepancy in a footnote
- **ADD**: Risk mitigation in section 4 → Include contingency plans for: (a) key vendor dependency, (b) regulatory delays, (c) talent acquisition
- **KEEP**: Technical architecture diagram → Stakeholders praised the clarity, preserve without changes
- **ADD**: Financial assumptions table → Document unit economics: CAC <$500, LTV >$3000, payback <6 months for each segment
- **CLARIFY**: Success metrics in section 5.2 → Replace "increase engagement" with specific KPIs: DAU/MAU >0.3, session duration >5min, retention D30 >40%
- **ADD**: Competitive positioning → Create feature matrix comparing against [Competitor A], [Competitor B] on price, performance, and ease of use
```

---

## Guidelines

1. **Be Specific**: Reference exact sections or content areas (e.g., "section 3.2", "the Q4 roadmap")
2. **Be Actionable**: State clearly what to add, clarify, resolve, or remove
3. **Prioritize Impact**: Focus on revisions that most affect the committee's decision
4. **Balance**: Include both critical fixes and strategic enhancements
5. **Use Debate Evidence**: Base recommendations on actual arguments raised by PRO and CON

---

## What NOT to Include

❌ Generic summaries ("The document needs more details")
❌ Vague suggestions ("Improve the competitive analysis")
❌ Debate play-by-play ("PRO said X, then CON said Y")
❌ Non-actionable observations ("The discussion was interesting")

---

## Generate Recommendations Now

List {min_takeaways}-{max_takeaways} specific, actionable revisions that will make this document stronger:
