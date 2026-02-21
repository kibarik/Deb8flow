"""
Takeaway analyzer for debate dialogues.

This module provides functionality to analyze debate dialogues
and extract key insights, takeaways, and action items.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


logger = logging.getLogger(__name__)


@dataclass
class TakeawayConfig:
    """Configuration for takeaway generation."""
    min_takeaways: int = 3
    max_takeaways: int = 15
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    language: str = "ru"


class TakeawayAnalyzer:
    """
    Analyzes debate dialogues and extracts key takeaways.

    This analyzer uses an LLM to examine the full dialogue,
    verdict, and question to generate structured insights
    about the document's strengths and weaknesses.
    """

    def __init__(
        self,
        config: Optional[TakeawayConfig] = None,
        prompt_loader: Optional['PromptLoader'] = None
    ):
        """
        Initialize the takeaway analyzer.

        Args:
            config: Configuration for takeaway generation
            prompt_loader: Optional PromptLoader for loading analysis prompts
        """
        self.config = config or TakeawayConfig()
        self.prompt_loader = prompt_loader  # Store PromptLoader

        # Initialize LLM
        llm_kwargs = {
            "model": self.config.model or "gpt-4o",
            "temperature": 0.5,  # Lower temperature for more focused analysis
            "max_tokens": 4000,  # Increased for complete takeaway generation
        }

        if self.config.api_key:
            llm_kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            llm_kwargs["base_url"] = self.config.base_url

        self.llm = ChatOpenAI(**llm_kwargs)

    async def generate_takeaways(
        self,
        dialogue: List[Dict[str, Any]],
        question: str,
        verdict_explanation: Optional[str] = None,
        winner: Optional[str] = None
    ) -> List[str]:
        """
        Generate takeaways from a debate dialogue.

        Args:
            dialogue: List of dialogue messages with speaker, content, stage
            question: The committee question
            verdict_explanation: Optional judge's explanation
            winner: Optional winner (PRO or CON)

        Returns:
            List of takeaway strings (1-50 items)
        """
        # Build dialogue summary for analysis
        dialogue_summary = self._build_dialogue_summary(dialogue)

        # Detect language from dialogue
        language = self._detect_language(dialogue)

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(
            question=question,
            dialogue_summary=dialogue_summary,
            verdict_explanation=verdict_explanation,
            winner=winner,
            language=language
        )

        try:
            # Generate takeaways using LLM
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=self._get_system_prompt(language)),
                    HumanMessage(content=prompt)
                ]
            )

            content = response.content.strip()

            # Parse the response into takeaways
            takeaways = self._parse_takeaways(content)

            # Ensure we respect min/max limits
            if len(takeaways) < self.config.min_takeaways:
                logger.warning(f"Only {len(takeaways)} takeaways generated, minimum is {self.config.min_takeaways}")
            if len(takeaways) > self.config.max_takeaways:
                takeaways = takeaways[:self.config.max_takeaways]

            logger.info(f"Generated {len(takeaways)} takeaways")
            return takeaways

        except Exception as e:
            logger.error(f"Error generating takeaways: {e}")
            # Return fallback takeaways based on verdict
            return self._generate_fallback_takeaways(verdict_explanation, winner)

    def _build_dialogue_summary(self, dialogue: List[Dict[str, Any]]) -> str:
        """Build a structured summary of the dialogue."""
        if not dialogue:
            return "No dialogue available"

        summary_parts = []

        # Group by speaker
        pro_messages = [m for m in dialogue if m.get("speaker") == "PRO"]
        con_messages = [m for m in dialogue if m.get("speaker") == "CON"]
        judge_messages = [m for m in dialogue if m.get("speaker") == "JUDGE"]

        if pro_messages:
            summary_parts.append("PRO ARGUMENTS:")
            for msg in pro_messages[:3]:  # Limit to first 3 PRO messages
                content = msg.get("content", "")[:300]
                stage = msg.get("stage", "unknown")
                summary_parts.append(f"[{stage}] {content}...")

        if con_messages:
            summary_parts.append("\nCON ARGUMENTS:")
            for msg in con_messages[:3]:  # Limit to first 3 CON messages
                content = msg.get("content", "")[:300]
                stage = msg.get("stage", "unknown")
                summary_parts.append(f"[{stage}] {content}...")

        if judge_messages:
            summary_parts.append("\nJUDGE VERDICT:")
            for msg in judge_messages:
                content = msg.get("content", "")[:500]
                summary_parts.append(content)

        return "\n".join(summary_parts)

    def _detect_language(self, dialogue: List[Dict[str, Any]]) -> str:
        """Detect the primary language of the dialogue."""
        # Check first few messages for Russian characters
        for msg in dialogue[:3]:
            content = msg.get("content", "")
            # Simple check for Cyrillic characters
            if any(char in content for char in "абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"):
                return "ru"
        return "en"

    def _get_system_prompt(self, language: str) -> str:
        """
        Get the system prompt for the analyst LLM.

        Now loads from template instead of hardcoded strings.
        """
        if self.prompt_loader:
            try:
                # Try language-specific prompt first
                prompt_id = f"analysis.system_{language}"
                return self.prompt_loader.load(prompt_id)
            except KeyError:
                try:
                    # Fall back to English
                    return self.prompt_loader.load("analysis.system")
                except KeyError:
                    logger.warning(f"Analysis system prompt not found, using fallback")
                    return self._get_fallback_system_prompt(language)
        else:
            # Fallback to hardcoded if no PromptLoader (backward compat)
            return self._get_fallback_system_prompt(language)

    def _get_fallback_system_prompt(self, language: str) -> str:
        """Fallback hardcoded system prompt (for backward compatibility)."""
        if language == "ru":
            return """Вы аналитик продукта комитета. Ваша задача - проанализировать дебаты и извлечь ключевые выводы.

Проанализируйте диалог и выделите:
1. Ключевые сильные стороны документа (аргументы PRO)
2. Ключевые слабые стороны и риски (аргументы CON)
3. Конкретные моменты, которые требуют доработки
4. Положительные аспекты, которые стоит сохранить

Каждый takeaway должен быть:
- Кратким и конкретным (1-2 предложения)
- Основан на реальных аргументах из дебатов
- Содержать actionable инсайт

Формат вывода: каждый пункт с новой строки, начиная с тире "- "."""
        else:
            return """You are a product committee analyst. Your task is to analyze debates and extract key takeaways.

Analyze the dialogue and identify:
1. Key strengths of the document (PRO arguments)
2. Key weaknesses and risks (CON arguments)
3. Specific points that need revision
4. Positive aspects worth preserving

Each takeaway should be:
- Concise and specific (1-2 sentences)
- Based on actual arguments from the debate
- Contain actionable insights

Output format: each point on a new line starting with dash "- "."""

    def _build_analysis_prompt(
        self,
        question: str,
        dialogue_summary: str,
        verdict_explanation: Optional[str],
        winner: Optional[str],
        language: str
    ) -> str:
        """
        Build the analysis prompt for the LLM.

        Now loads from template instead of hardcoded strings.
        """
        if self.prompt_loader:
            # Import PromptContext here to avoid circular imports
            from .prompt_loader import PromptContext

            # Build verdict section
            verdict_section = ""
            if verdict_explanation:
                verdict_section = f"\n\nJUDGE VERDICT (Winner: {winner or 'N/A'}):\n{verdict_explanation}"

            # Build context with all variables
            context = PromptContext(
                question=question,
                dialogue_summary=dialogue_summary,
                verdict_explanation=verdict_section,
                winner=winner or "",
                min_takeaways=self.config.min_takeaways,
                max_takeaways=self.config.max_takeaways
            )

            # Load and render template
            try:
                prompt_id = f"analysis.takeaway_{language}"
                template = self.prompt_loader.load(prompt_id)
            except KeyError:
                try:
                    template = self.prompt_loader.load("analysis.takeaway")
                except KeyError:
                    logger.warning("Analysis takeaway prompt not found, using fallback")
                    return self._get_fallback_analysis_prompt(
                        question, dialogue_summary, verdict_explanation,
                        winner, language
                    )

            # Render with context using simple string formatting
            try:
                return template.format(**context.to_dict())
            except KeyError as e:
                logger.warning(f"Missing template variable: {e}, using fallback")
                return self._get_fallback_analysis_prompt(
                    question, dialogue_summary, verdict_explanation,
                    winner, language
                )
        else:
            # Fallback to hardcoded (backward compat)
            return self._get_fallback_analysis_prompt(
                question, dialogue_summary, verdict_explanation,
                winner, language
            )

    def _get_fallback_analysis_prompt(
        self,
        question: str,
        dialogue_summary: str,
        verdict_explanation: Optional[str],
        winner: Optional[str],
        language: str
    ) -> str:
        """Fallback hardcoded analysis prompt."""
        if language == "ru":
            prompt = f"""ВОПРОС КОМИТЕТА:
{question}

ДИАЛОГ ДЕБАТОВ:
{dialogue_summary}
"""
            if verdict_explanation:
                prompt += f"""
РЕШЕНИЕ СУДЬИ (Победитель: {winner or 'N/A'}):
{verdict_explanation}
"""
            prompt += f"""

## Задача
На основе анализа дебатов сгенерируйте от {self.config.min_takeaways} до {self.config.max_takeaways} **конкретных рекомендаций по доработке** документа.

Каждая рекомендация должна следовать формату:
- **[КАТЕГОРИЯ]**: [Раздел] → [Конкретное действие]

**Категории:**
- **ДОБАВИТЬ** = Контент для добавления
- **УТОЧНИТЬ** = Размытые места
- **ИСПРАВИТЬ** = Противоречия
- **УДАЛИТЬ** = Лишний контент
- **СОХРАНИТЬ** = Сильные стороны

## Примеры:
- **ДОБАВИТЬ**: Раздел 2.4 → Включить TAM/SAM/SOM с источниками
- **УТОЧНИТЬ**: Go-to-Market → Указать % каналов сбыта
- **ИСПРАВИТЬ**: Секция команды (5 vs 8?) → Согласовать цифры
- **СОХРАНИТЬ**: Архитектура → Не изменять

Генерируйте рекомендации сейчас:"""
        else:
            prompt = f"""COMMITTEE QUESTION:
{question}

DEBATE DIALOGUE:
{dialogue_summary}
"""
            if verdict_explanation:
                prompt += f"""
JUDGE VERDICT (Winner: {winner or 'N/A'}):
{verdict_explanation}
"""
            prompt += f"""

## Task
Generate {self.config.min_takeaways} to {self.config.max_takeaways} **actionable revision recommendations** for the document.

Each recommendation must follow:
- **[CATEGORY]**: [Section] → [Specific action]

**Categories:**
- **ADD** = Content to add
- **CLARIFY** = Vague sections
- **RESOLVE** = Contradictions
- **REMOVE** = Unnecessary content
- **KEEP** = Strengths to preserve

## Examples:
- **ADD**: Section 2.4 → Include TAM/SAM/SOM breakdown with sources
- **CLARIFY**: Go-to-Market → Specify channel mix percentages
- **RESOLVE**: Team section (5 vs 8?) → Reconcile numbers
- **KEEP**: Architecture → Preserve without changes

Generate recommendations now:"""

        return prompt

    def _parse_takeaways(self, response: str) -> List[str]:
        """Parse the LLM response into a list of takeaways.

        Handles various LLM response formats:
        - Direct list items starting with dash/number
        - Items with **CATEGORY** markers
        - Preamble text followed by list
        - Multi-line takeaways with continuation
        """
        takeaways = []
        lines = response.split('\n')

        # Find the start of the actual list (skip preamble)
        list_started = False
        preamble_end_keywords = ['вывод:', 'выводы:', 'analysis:', 'insights:', 'примеры:',
                                 'пункты:', 'recommendations:', 'пример:', 'задача:']

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Check if this line starts a list item (supports **CATEGORY** format)
            is_list_item = (
                line_stripped.startswith('- ') or
                line_stripped.startswith('•') or
                (line_stripped[0].isdigit() and ('.' in line_stripped[:5] or ')' in line_stripped[:5])) or
                ('**' in line_stripped and '**:' in line_stripped)  # **CATEGORY**: format
            )

            if is_list_item:
                list_started = True
                # Extract the takeaway content
                if line_stripped.startswith('- '):
                    takeaway = line_stripped[2:].strip()
                elif line_stripped.startswith('•'):
                    takeaway = line_stripped[1:].strip()
                elif '**' in line_stripped and '**:' in line_stripped:
                    # Handle **CATEGORY** format - keep the whole line as formatted
                    takeaway = line_stripped
                elif line_stripped[0].isdigit():
                    # Remove number prefix (1. or 1) or 1.)
                    for sep in ['. ', ') ', '.)', ')']:
                        if sep in line_stripped:
                            parts = line_stripped.split(sep, 1)
                            if len(parts) > 1:
                                takeaway = parts[1].strip()
                                break
                    else:
                        takeaway = line_stripped
                else:
                    continue

                # Clean up common LLM artifacts (but preserve **CATEGORY** format)
                takeaway = self._clean_takeaway(takeaway)
                if takeaway and len(takeaway) > 10:  # Minimum meaningful length
                    takeaways.append(takeaway)

            elif list_started:
                # We're in the list section, check for multi-line continuations
                if not line_stripped:
                    continue
                # Check if it's a continuation of previous takeaway
                # (indented, starting with lowercase, or arrow continuation)
                if takeaways and (line.startswith('  ') or line.startswith('\t') or
                    (line_stripped[0].islower() and len(line_stripped) > 20) or
                    line_stripped.startswith('→') or line_stripped.startswith('->')):
                    # Append to previous takeaway
                    takeaways[-1] += ' ' + line_stripped
                # Check for end-of-list keywords
                elif any(kw in line_stripped.lower() for kw in ['важно:', 'заметка:', 'note:',
                                                                   'summary:', '###', '## ']):
                    break

        # If no structured list found, try to extract from paragraph text
        if not takeaways:
            takeaways = self._extract_from_paragraph_text(response)

        return takeaways

    def _clean_takeaway(self, takeaway: str) -> str:
        """Clean up common LLM artifacts in takeaways."""
        # Remove trailing punctuation issues
        takeaway = takeaway.rstrip('.,;:')

        # Remove common LLM prefixes
        for prefix in ['-', '•', '*', '* ', '- ']:
            if takeaway.startswith(prefix):
                takeaway = takeaway[len(prefix):].strip()

        return takeaway

    def _extract_from_paragraph_text(self, response: str) -> List[str]:
        """Extract takeaways from unstructured paragraph text as fallback."""
        takeaways = []

        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', response)

        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out preamble sentences and very short ones
            if (len(sentence) > 30 and
                not any(kw in sentence.lower() for kw in ['проанализировал', 'вот анализ', 'following', 'here is'])):
                takeaways.append(sentence)

        return takeaways[:self.config.max_takeaways]

    def _generate_fallback_takeaways(
        self,
        verdict_explanation: Optional[str],
        winner: Optional[str]
    ) -> List[str]:
        """Generate fallback takeaways when LLM fails."""
        takeaways = []

        if verdict_explanation:
            # Add the verdict as a takeaway
            if len(verdict_explanation) > 50:
                takeaways.append(verdict_explanation[:200] + ("..." if len(verdict_explanation) > 200 else ""))

        if winner:
            if winner == "PRO":
                takeaways.append("Позиция PRO (за проект) победила в дебатах")
            else:
                takeaways.append("Позиция CON (против проекта) выявила критические проблемы")

        if not takeaways:
            takeaways.append("Автоматический анализ недоступен - требуется ручной разбор дебатов")

        return takeaways


async def generate_takeaways_from_dialogue_json(
    dialogue_json: Dict[str, Any],
    config: Optional[TakeawayConfig] = None,
    prompt_loader: Optional['PromptLoader'] = None
) -> List[str]:
    """
    Convenience function to generate takeaways from a dialogue JSON dict.

    Args:
        dialogue_json: The dialogue JSON (loaded from file)
        config: Optional configuration
        prompt_loader: Optional PromptLoader for loading analysis prompts

    Returns:
        List of takeaway strings
    """
    analyzer = TakeawayAnalyzer(config, prompt_loader)

    dialogue = dialogue_json.get("messages", [])
    verdict = dialogue_json.get("verdict", {})

    # Question is not in the JSON, will need to be passed separately
    # For now, use empty string and let the analyzer work with dialogue only
    return await analyzer.generate_takeaways(
        dialogue=dialogue,
        question="",  # Will need to be provided separately
        verdict_explanation=verdict.get("explanation"),
        winner=verdict.get("winner")
    )
