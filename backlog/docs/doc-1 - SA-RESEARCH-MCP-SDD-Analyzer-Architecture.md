---
id: doc-1
title: 'SA-RESEARCH: MCP SDD Analyzer Architecture'
type: other
created_date: '2026-03-19 21:11'
---
# SA Research: MCP SDD Analyzer Architecture

**Task:** TASK-1 - MCP сервер для анализа SDD спецификаций  
**Date:** 2026-03-19  
**Status:** Research Complete

---

## 1. Current Architecture Analysis

### 1.1 Project Structure (Clean Architecture)

```
src/
├── committee/           # Product Committee bounded context
│   ├── adapters/        # CLI, Reports
│   ├── application/     # RunProductCommittee use case
│   └── domain/          # CommitteeRun, CommitteeMetadata
├── shared/              # Shared debate framework
│   ├── config/          # ConfigLoader, Pydantic models
│   └── debate/
│       ├── application/ # Ports, PromptLoader, Use Cases
│       ├── domain/      # DebateRoom, DebateMessage, Verdict
│       └── infrastructure/ # LLM orchestrators, Storage
├── prompts/             # Markdown prompt templates
│   ├── roles/           # Agent role prompts (TPM, CPO, CFO, CTO, BDM)
│   ├── debate/          # Debate stages, judge, context
│   └── analysis/        # System prompt, takeaway analysis
└── rewrite/             # Document rewrite with debate verification
```

### 1.2 Key Components for MCP Reuse

| Component | File | Reuse Potential |
|-----------|------|-----------------|
| DebateOrchestratorFactory | `src/shared/debate/infrastructure/llm/factory.py` | HIGH - Already abstracts orchestrator creation |
| PromptLoader | `src/shared/debate/application/prompt_loader.py` | HIGH - Template loading with context substitution |
| LLMDebateOrchestrator | `src/shared/debate/infrastructure/llm/debate_orchestrator.py` | MEDIUM - Can wrap for MCP tool |
| ConfigLoader | `src/shared/config/config_loader.py` | HIGH - Environment variable substitution |
| Ports (Protocols) | `src/shared/debate/application/ports.py` | HIGH - Already defines interfaces |

### 1.3 Configuration System

Current `config/debate_config.yaml`:
```yaml
llm:
  base_url: "${DEBATE_BASE_URL:}"
  model: "${DEBATE_MODEL:gpt-4o-mini}"
  temperature: ${DEBATE_TEMPERATURE:0.8}

debate:
  mode: "standard"  # or "simple"
  max_retries: 2

agents:
  main:
    name: "PO"
    prompt: "config/prompts/roles/po.txt"
  opponents:
    - name: "TPM"
      prompt: "config/prompts/roles/tpm.txt"

prompts:
  stages:
    opening_pro: "src/prompts/debate/stages/opening_pro.md"
    # ... 8 stages total
  judge: "src/prompts/debate/judge/verdict.md"
  context: "src/prompts/debate/context/debate_context.md"
```

**Need:** Create `config/sdd_config.yaml` for SDD-specific analysis.

---

## 2. MCP SDK Analysis

### 2.1 FastMCP Library Selection

**Chosen:** FastMCP by PrefectHQ (`/prefecthq/fastmcp`)  
**Benchmark Score:** 88.28 (highest among alternatives)  
**Code Snippets:** 3782

### 2.2 FastMCP Server Pattern

```python
from fastmcp import FastMCP

mcp = FastMCP("sdd-analyzer")

@mcp.tool
def analyze_specification(spec_path: str) -> dict:
    """Analyze SDD specification for weak points."""
    # Load spec
    # Run debate analysis
    # Return structured result
    return {"weak_points": [...], "recommendations": [...]}

@mcp.prompt
def sdd_analysis_prompt(spec_content: str) -> str:
    """System prompt for SDD analysis."""
    return f"Analyze this specification:\n{spec_content}"

if __name__ == "__main__":
    mcp.run()  # stdio transport by default
```

### 2.3 MCP Integration with Claude Code

Configuration in `.claude/mcp.json`:
```json
{
  "mcpServers": {
    "sdd-analyzer": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "DEBATE_MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

---

## 3. SDD Analysis Design

### 3.1 Difference from PRD Analysis

| Aspect | PRD (Current) | SDD (New) |
|--------|---------------|-----------|
| Focus | Business value, market fit | Technical feasibility, AI-clarity |
| Agents | TPM, CPO, CFO, CTO, BDM | Architect, DevLead, QA, Security |
| Output | Verdict: PRO/CON | weak_points, recommendations, unclear_sections |
| Questions | "Should we build this?" | "Can AI build from this?" |

### 3.2 SDD Analysis Agents

1. **Architect (PRO)** - Argues specification is complete and AI-ready
2. **DevLead (CON)** - Finds gaps, ambiguities, missing details
3. **QA (CON)** - Identifies untestable requirements
4. **Security (CON)** - Points out security considerations

### 3.3 SDD Analysis Output Schema

```python
@dataclass
class SDDAnalysisResult:
    weak_points: List[WeakPoint]
    recommendations: List[Recommendation]
    unclear_sections: List[UnclearSection]
    overall_score: float  # 0.0 - 1.0
    verdict: str  # "AI-READY", "NEEDS-CLARIFICATION", "NOT-READY"

@dataclass
class WeakPoint:
    section: str
    issue: str
    severity: str  # "critical", "major", "minor"
    suggestion: str

@dataclass
class Recommendation:
    priority: str  # "high", "medium", "low"
    action: str
    rationale: str

@dataclass
class UnclearSection:
    location: str  # line range or section name
    question: str  # what's unclear
    suggested_clarification: str
```

---

## 4. Implementation Plan

### 4.1 File Structure (New Files)

```
src/mcp/
├── __init__.py
├── server.py           # FastMCP server
├── analyzer.py         # SDD analysis logic
└── models.py           # SDD-specific Pydantic models

config/
├── debate_config.yaml  # Existing (PRD)
└── sdd_config.yaml     # NEW: SDD-specific config

src/prompts/sdd/
├── architect.md        # PRO agent prompt
├── devlead.md          # CON agent prompt
├── qa.md               # CON agent prompt
├── security.md         # CON agent prompt
├── judge.md            # SDD verdict prompt
└── context.md          # SDD context template
```

### 4.2 Dependencies to Add

```toml
[tool.poetry.dependencies]
mcp = "^1.0.0"  # FastMCP
```

### 4.3 Poetry Scripts

```toml
[tool.poetry.scripts]
sdd-analyzer = "src.mcp.server:main"
```

---

## 5. Questions Resolved

| # | Question | Resolution |
|---|----------|------------|
| 1 | How MCP server registers tools? | `@mcp.tool` decorator in FastMCP |
| 2 | Transport to use? | stdio (default, works with Claude Code) |
| 3 | How to pass spec path? | Tool parameter: `analyze_specification(spec_path: str)` |
| 4 | JSON response structure? | SDDAnalysisResult dataclass, return as dict |
| 5 | Error handling in MCP tools? | Raise exceptions, FastMCP converts to MCP errors |
| 6 | Timeout for analysis? | Use existing debate timeout (120s from config) |
| 7 | Large specifications? | Truncate to config.max_tokens (5000) or chunk |
| 8 | Code reuse strategy? | Wrap existing DebateOrchestrator, create SDD config |
| 9 | SDD vs PRD agents? | New agent prompts in src/prompts/sdd/ |
| 10 | Testing approach? | Unit tests for analyzer, integration via MCP client |

---

## 6. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| FastMCP API changes | HIGH | Pin version, add integration tests |
| LLM rate limits during analysis | MEDIUM | Reuse fallback_models mechanism |
| Large spec files | MEDIUM | Add file size validation, chunking |
| Claude Code MCP config errors | LOW | Provide clear setup documentation |

---

## 7. Assumptions

1. SDD specifications are in Markdown format (same as PRD)
2. Claude Code is configured to use stdio MCP transport
3. OPENAI_API_KEY is set in environment
4. Existing debate infrastructure handles concurrent rooms correctly
5. SDD analysis can reuse simple mode (single LLM call) for speed

---

## 8. Next Steps

1. **TASK-3**: Add `mcp` dependency to pyproject.toml
2. **TASK-5**: Create `config/sdd_config.yaml`
3. **TASK-6**: Create SDD prompts in `src/prompts/sdd/`
4. **TASK-4**: Create `src/mcp/server.py` with FastMCP
5. **TASK-7**: Add poetry script entry point
6. **TASK-8**: Update `.claude/mcp.json` configuration

---

## 9. Evidence Log

| Source | Type | Key Insight |
|--------|------|-------------|
| main.py | File | CLI entry point pattern, argparse structure |
| factory.py | File | DebateOrchestratorFactory pattern for reuse |
| config_loader.py | File | Environment variable substitution syntax |
| ports.py | File | Protocol interfaces for dependency injection |
| FastMCP docs | Context7 | @mcp.tool/@mcp.prompt decorators, stdio transport |
| debate_orchestrator.py | File | LLM fallback mechanism, progressive state saving |
| prompt_loader.py | File | Template loading with PromptContext |

---

**Research Complete.** Ready for implementation phase.
