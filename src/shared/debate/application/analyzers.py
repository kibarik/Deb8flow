"""
Takeaway analyzer for debate dialogues.

This module provides functionality to analyze debate dialogues
and extract key insights, takeaways, and action items.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
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

    def __init__(self, config: Optional[TakeawayConfig] = None):
        """
        Initialize the takeaway analyzer.

        Args:
            config: Configuration for takeaway generation
        """
        self.config = config or TakeawayConfig()

        # Initialize LLM
        llm_kwargs = {
            "model": self.config.model or "gpt-4o",
            "temperature": 0.5,  # Lower temperature for more focused analysis
            "max_tokens": 2000,
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
        """Get the system prompt for the analyst LLM."""
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

Формат输出: каждый пункт с новой строки, начиная с тире "- "."""
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
        """Build the analysis prompt for the LLM."""
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

ЗАДАЧА:
Проанализируйте дебаты и создайте список от {self.config.min_takeaways} до {self.config.max_takeaways} ключевых выводов (takeaways).

Каждый takeaway должен быть в формате: "- [Краткое описание вывода]"

Примеры:
- Сильная техническая архитектура с модульным подходом позволяет гибкую адаптацию
- Риск: размытый фокус на 5 разных сегментах может расточить ресурсы
- Необходимо уточнить конкурентную стратегию для банковского сегмента
- Хорошо проработанный план онбординга клиентов снижает риски внедрения

ВАЖНО:
- Сосредоточьтесь на конкретных, actionable инсайтах
- Используйте аргументы ОБЕИХ сторон
- Указывайте как сильные стороны, так и зоны роста
- Будьте объективны и конструктивны

Генерируйте выводы сейчас:"""
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

TASK:
Analyze the debate and create a list of {self.config.min_takeaways} to {self.config.max_takeaways} key takeaways.

Each takeaway should be in format: "- [Brief description of insight]"

Examples:
- Strong technical architecture with modular approach allows flexible adaptation
- Risk: unfocused focus on 5 different segments may drain resources
- Need to clarify competitive strategy for banking segment
- Well-developed client onboarding plan reduces implementation risks

IMPORTANT:
- Focus on specific, actionable insights
- Use arguments from BOTH sides
- Indicate both strengths and areas for improvement
- Be objective and constructive

Generate takeaways now:"""

        return prompt

    def _parse_takeaways(self, response: str) -> List[str]:
        """Parse the LLM response into a list of takeaways."""
        takeaways = []

        # Split by lines and extract items starting with dash
        for line in response.split('\n'):
            line = line.strip()

            # Check for dash prefix
            if line.startswith('- '):
                takeaway = line[2:].strip()
                if takeaway:
                    takeaways.append(takeaway)
            # Check for numbered list
            elif line and line[0].isdigit() and ('.' in line or ')' in line):
                # Remove the number prefix
                for sep in ['. ', ') ', '.)', ')']:
                    if line.startswith(sep) or (len(line) > 2 and line[1] == sep[0]):
                        parts = line.split(sep, 1)
                        if len(parts) > 1:
                            takeaway = parts[1].strip()
                            if takeaway:
                                takeaways.append(takeaway)
                                break
            # Check for bullet points
            elif line.startswith(('•', '*', '·')):
                takeaway = line[1:].strip()
                if takeaway:
                    takeaways.append(takeaway)
            # Non-empty lines that might be takeaways (if we have few items)
            elif len(line) > 20 and len(takeaways) < self.config.min_takeaways:
                # Check if it looks like a sentence (starts with capital, ends with punctuation)
                if line[0].isupper() or line[0] in '/*-•':
                    takeaways.append(line)

        return takeaways

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
    config: Optional[TakeawayConfig] = None
) -> List[str]:
    """
    Convenience function to generate takeaways from a dialogue JSON dict.

    Args:
        dialogue_json: The dialogue JSON (loaded from file)
        config: Optional configuration

    Returns:
        List of takeaway strings
    """
    analyzer = TakeawayAnalyzer(config)

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
