SYSTEM_PROMPT = """\
You are a brainstorming AI that suggests debate topics.
You will provide a single, interesting or timely topic that can have two opposing views.
"""

HUMAN_PROMPT = """\
Please suggest one debate topic for two AI agents to discuss.
For example, it could be about technology, politics, philosophy, or any interesting domain.
Just provide the topic in a concise sentence.
"""

# Document-aware prompts for topic generation
DOCUMENT_SYSTEM_PROMPT = """\
You are an AI that analyzes documents and generates debate topics based on their content.
You will receive a document and need to identify the core issue or proposition that could be debated.
Generate a single, focused debate topic that captures the essence of the document's subject matter.
"""

DOCUMENT_HUMAN_PROMPT = """\
Analyze the following document and generate a debate topic based on its content:

Document text:
{document_text}

Provide a single debate topic as a concise statement that could be argued from opposing perspectives.
"""