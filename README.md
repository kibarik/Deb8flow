# Deb8flow: Multi-Agent AI Debate Framework

**Deb8flow** is a multi-agent AI debate framework built with [LangGraph](https://github.com/langchain-ai/langgraph). It simulates structured debates between two autonomous AI agents (PRO and CON), orchestrated by a moderator and finalized with a judge's verdict. The system includes integrated fact-checking and supports both standard and document-based debates.

**Inspired by the original framework by [Iason Solomos](https://github.com/iason-solomos)** — thank you for creating this foundational project!

---

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API key:

```
OPENAI_API_KEY=your_openai_key_here
```

Optional (for tracing):
```
LANGCHAIN_API_KEY=your_langchain_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=deb8flow
```

### 3. Run a Standard Debate

```bash
python main.py
```

---

## Document-Based Debates

The `document_debate_cli.py` enables debates based on documents or custom topics.

### Basic Usage

```bash
# Quick debate on a direct topic
python3 document_debate_cli.py --text "GitHub полезен для разработчиков"

# Debate based on a document with a specific question
python3 document_debate_cli.py --docx '/path/to/document.docx' --request "какой потенциал у этого проекта?"
```

### Custom Role-Based Debates

Customize debater roles using prompt files (e.g., TPM vs CPO, Developer vs Designer):

```bash
python3 document_debate_cli.py \
  --docx '/path/to/PRD.docx' \
  --request "какой потенциал у этого проекта?" \
  --pro-prompt 'prompts/tpm.txt' \
  --con-prompt 'prompts/cpo.txt'
```

#### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--text <topic>` | Direct debate topic (quick mode) |
| `--docx <file>` | Path to .docx file for context |
| `--request <question>` | Debate topic/question (required with --docx) |
| `--pro-prompt <file>` | Path to custom PRO debater prompt file |
| `--con-prompt <file>` | Path to custom CON debater prompt file |
| `--verbose` | Show detailed prompt content for verification |

---

## Debate Structure

```
topic_generation → opening (PRO) → fact_check → rebuttal (CON) → fact_check
→ counter (PRO) → fact_check → final_argument (CON) → fact_check → judge_verdict
```

### Key Features

- **Multi-LLM Support**: OpenAI, Azure OpenAI, Zhipu AI, Requesty/DeepSeek
- **Fact-Checking**: Validates every claim with web search; 3 failures = disqualification
- **Custom Prompts**: Inject custom role-based prompts for specialized debates

---

## Project Structure

```
Deb8flow/
├── nodes/              # LangGraph node implementations
├── prompts/            # System prompts for each agent role
├── workflow/           # LangGraph workflow definitions
├── configurations/     # LLM configs and debate constants
├── tests/              # E2E tests (19/19 passing)
├── main.py             # Entry point for standard debates
├── document_debate_cli.py  # CLI for document-based debates
└── debate_state.py     # TypedDict state definitions
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_full_workflow.py
```

---

## Built With

- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangChain](https://python.langchain.com/)
- OpenAI GPT-4.1
- Python 3.12+

## License

MIT License
