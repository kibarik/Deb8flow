"""
Conclusion generator for product committee.

This adapter generates a structured summary with actionable recommendations
extracted from debate room verdicts.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from ....shared.debate.domain.entities import DebateRoom
from ....shared.debate.domain.services import categorize_error
from ....shared.debate.domain.value_objects import Speaker


logger = logging.getLogger(__name__)


class ConclusionGenerator:
    """Generates structured conclusions with recommendations for committee runs."""

    def generate_conclusion(
        self,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate a structured conclusion with recommendations for fixes.

        Args:
            question: Committee question
            rooms: All debate room results
            metadata: Run metadata

        Returns:
            Markdown conclusion content
        """
        # Get PRD path from metadata
        prd_path = metadata.get('prd_path', metadata.get('prd', 'N/A'))

        # Count winners
        successful_rooms = [r for r in rooms if r.is_successful]
        tpm_wins = sum(1 for r in successful_rooms if r.verdict and r.verdict.winner == Speaker.PRO)
        opponent_wins = len(successful_rooms) - tpm_wins

        # Determine overall answer
        if not successful_rooms:
            overall_answer = "Не удалось провести анализ (все комнаты завершились ошибкой)"
        elif tpm_wins > opponent_wins:
            overall_answer = "Проект одобрен для дальнейшей проработки"
        elif opponent_wins > tpm_wins:
            overall_answer = "Требуется значительная доработка документа"
        else:
            overall_answer = "Требуется дополнительный анализ"

        # Generate detailed description
        detailed_description = self._generate_detailed_description(rooms, successful_rooms, tpm_wins, opponent_wins)

        # Extract recommendations from judge explanations
        recommendations = self._extract_recommendations(rooms)

        # Build the document
        lines = [
            f"# Заключение комитета",
            f"",
            f"**Сгенерировано:** {metadata.get('end_time', 'N/A')}",
            f"",
            f"---",
            f"",
            f"## Вопрос",
            f"",
            f"{question}",
            f"",
            f"---",
            f"",
            f"## Документ",
            f"",
            f"`{prd_path}`",
            f"",
            f"---",
            f"",
            f"## Ответ",
            f"",
            f"**{overall_answer}**",
            f"",
            f"---",
            f"",
            f"## Детальное описание",
            f"",
        ]

        lines.extend(detailed_description)
        lines.extend([
            f"",
            f"---",
            f"",
            f"## Рекомендации по доработкам",
            f"",
        ])

        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.extend([
            f"",
            f"---",
            f"",
            f"*Подробная информация о дебатах доступна в [final_report.md](final_report.md)*",
            f""
        ])

        return '\n'.join(lines)

    def _generate_detailed_description(
        self,
        rooms: List[DebateRoom],
        successful_rooms: List[DebateRoom],
        tpm_wins: int,
        opponent_wins: int
    ) -> List[str]:
        """Generate detailed description of the committee decision."""
        lines = []

        if not successful_rooms:
            lines.append("К сожалению, ни одна из дебатных комнат не завершилась успешно. ")
            lines.append("Проверьте логи выполнения для получения подробной информации об ошибках.")
            return lines

        total_rooms = len(successful_rooms)
        lines.append(f"В ходе работы комитета было проведено {total_rooms} дебат(ов). ")

        if tpm_wins > opponent_wins:
            lines.append(f"Позиция TPM (PRO) одержала победу в {tpm_wins} из {total_rooms} дебатов. ")
            lines.append("Это indicates, что в целом позиция в пользу проекта была убедительной. ")
        elif opponent_wins > tpm_wins:
            lines.append(f"Позиция оппонентов (CON) одержала победу в {opponent_wins} из {total_rooms} дебатов. ")
            lines.append("Это указывает на наличие существенных замечаний к проекту. ")
        else:
            lines.append(f"Результаты дебатов разделились: {tpm_wins} побед TPM и {opponent_wins} побед оппонентов. ")
            lines.append("Требуется дополнительный анализ для принятия окончательного решения. ")

        lines.append("")
        lines.append("### Участники и их позиции:")

        # Add brief summary of each room
        for room in rooms:
            if not room.is_successful:
                continue

            winner = room.verdict.winner.value if room.verdict else "Unknown"
            opponent = room.con_participant

            lines.append(f"")
            lines.append(f"**TPM vs {opponent}:**")

            if winner == "PRO":
                lines.append(f"- Победитель: TPM")
            else:
                lines.append(f"- Победитель: {opponent}")

            # Extract key concern from explanation
            explanation = room.verdict.explanation if room.verdict else ""
            key_concern = self._extract_key_concern(explanation)
            if key_concern:
                lines.append(f"- Ключевое замечание: {key_concern}")

        return lines

    def _extract_key_concern(self, explanation: str) -> str:
        """Extract the key concern from judge explanation."""
        if not explanation:
            return "Нет объяснения"

        # Clean the explanation first
        cleaned = self._clean_explanation(explanation)

        # Take first meaningful sentence, truncate if too long
        sentences = re.split(r'[.!?]', cleaned)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Only meaningful sentences
                if len(sentence) > 200:
                    sentence = sentence[:197] + "..."
                return sentence

        return cleaned[:200] + "..." if len(cleaned) > 200 else cleaned

    def _extract_recommendations(self, rooms: List[DebateRoom]) -> List[str]:
        """Extract actionable recommendations from room verdicts."""
        recommendations = []

        for room in rooms:
            if not room.is_successful:
                continue

            winner = room.verdict.winner if room.verdict else None
            explanation = room.verdict.explanation if room.verdict else ""

            if not explanation:
                continue

            opponent = room.con_participant

            # If CON won, extract the concern as a recommendation
            if winner == Speaker.CON:
                rec = self._extract_con_recommendation(explanation, opponent)
                if rec:
                    recommendations.append(rec)
            # If PRO won, extract what worked positively
            elif winner == Speaker.PRO:
                rec = self._extract_pro_positive(explanation, opponent)
                if rec:
                    recommendations.append(rec)

        return recommendations

    def _extract_con_recommendation(self, explanation: str, opponent: str) -> Optional[str]:
        """Extract recommendation from CON victory explanation."""
        # Look for key concern patterns in CON victories
        concern_keywords = {
            'product': 'Продуктовая стратегия',
            'market': 'Позиционирование на рынке',
            'financial': 'Финансовая модель',
            'technical': 'Техническая архитектура',
            'operational': 'Операционные риски',
            'scalability': 'Масштабируемость',
            'focus': 'Фокус проекта',
            'business': 'Бизнес-модель',
            'cost': 'Структура затрат',
            'segment': 'Целевые сегменты',
        }

        # Truncate and format the explanation
        concern = self._clean_explanation(explanation)

        # Identify category
        category = None
        for keyword, cat in concern_keywords.items():
            if keyword.lower() in explanation.lower():
                category = cat
                break

        if category:
            return f"[{category}] {concern} (заметка от {opponent})"
        return f"{concern} (заметка от {opponent})"

    def _extract_pro_positive(self, explanation: str, opponent: str) -> Optional[str]:
        """Extract positive point from PRO victory explanation."""
        positive = self._clean_explanation(explanation)
        return f"✓ {positive} (подтверждено в дебатах с {opponent})"

    def _clean_explanation(self, explanation: str) -> str:
        """Clean and truncate explanation for readability."""
        if not explanation:
            return ""

        # Handle truncated text at the start (e.g., "e debate" -> "The debate")
        if explanation and len(explanation) > 3:
            # Check if starts with "e " (truncated "The ")
            if explanation.startswith('e '):
                explanation = 'The' + explanation[1:]
            # Check for other truncations
            elif explanation.startswith(' both'):
                explanation = explanation[1:].strip()
            # Capitalize first letter if lowercase
            elif explanation[0].islower():
                explanation = explanation[0].upper() + explanation[1:]

        # Remove common prefixes and patterns using regex
        patterns_to_remove = [
            r'^\*?\s*After reviewing both arguments,\s*',
            r'^\s*\*?\s*both arguments,\s*WINNER:\s*\*\*(CON|PRO)\*\*\.\s*',
            r'WINNER:\s*\*\*(CON|PRO)\*\*\.\s*',
            r'^\*?\s*The CON argument successfully\s*',
            r'^\*?\s*The PRO argument successfully\s*',
            r'^\s*\*?\s*both arguments,\s*',
        ]

        cleaned = explanation
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()

        # Remove any leading asterisks or spaces
        cleaned = cleaned.lstrip('*').strip()

        # If still empty or very short after cleaning, return a fallback
        if len(cleaned) < 10:
            return "Объяснение недоступно"

        # Truncate if too long - try to end at sentence boundary
        if len(cleaned) > 300:
            for punct in ['.', '!', ',']:
                idx = cleaned.rfind(punct, 200, 300)
                if idx > 200:
                    cleaned = cleaned[:idx + 1]
                    break
            else:
                cleaned = cleaned[:297] + "..."

        return cleaned

    def _generate_error_analysis(self, failed_rooms: List[DebateRoom]) -> List[str]:
        """Generate detailed error analysis section for failed runs."""
        lines = [
            f"**Status:** All debate rooms failed to complete.",
            f"",
            f"---",
            f"",
            f"## Error Analysis",
            f""
        ]

        # Categorize errors
        error_patterns: Dict[str, List[str]] = {}
        for room in failed_rooms:
            if room.error:
                category = categorize_error(room.error)
                error_patterns.setdefault(category, []).append(room.room_id.value)

        for error_type, room_list in error_patterns.items():
            lines.append(f"### {error_type}")
            lines.append(f"Affected rooms: {', '.join(room_list)}")
            lines.append("")

            # Add specific recommendations based on error type
            lines.extend(self._get_error_recommendations(error_type))
            lines.append("")

        # Show sample errors for debugging
        lines.extend([
            f"### Sample Error Details",
            f""
        ])
        for room in failed_rooms[:2]:  # Show first 2 errors
            lines.extend([
                f"**{room.room_id.value}:**",
                f"```",
                room.error or "No error message",
                "```",
                ""
            ])

        # Next steps
        lines.extend([
            f"---",
            f"",
            f"## Next Steps",
            f"",
            "1. **Check logs above** for detailed error messages",
            "2. **Verify LLM configuration** - check API keys and endpoints",
            "3. **Test with single room first** - reduce concurrency to isolate issues",
            "4. **Check role prompt files** - ensure all `.txt` files in `prompts/roles/` exist",
            "5. **Review PRD document** - ensure it's readable and contains sufficient content",
            ""
        ])

        return lines

    def _get_error_recommendations(self, error_type: str) -> List[str]:
        """Get specific recommendations for an error type."""
        recommendations = {
            "Regex/Pattern Error": [
                "**Recommendation:** Check regular expressions in filename sanitization.",
                "- Ensure character ranges are properly formatted",
                "- Escape special characters like `-` when used literally",
                "- Test regex patterns: `python3 -c 'import re; re.test()'`"
            ],
            "Timeout": [
                "**Recommendation:** Debate rooms are taking too long to complete.",
                "- Check if LLM API is responding slowly",
                "- Consider increasing timeout in configuration",
                "- Reduce debate complexity or number of rounds"
            ],
            "JSON Parsing Error": [
                "**Recommendation:** LLM responses are not valid JSON.",
                "- Check LLM prompts are requesting proper JSON format",
                "- Ensure system prompt specifies JSON output only",
                "- Consider using structured output if available"
            ],
            "LLM/API Error": [
                "**Recommendation:** LLM API issues detected.",
                "- Check API key is valid and has sufficient quota",
                "- Verify network connectivity to LLM provider",
                "- Check service status page for outages"
            ],
            "Other Error": [
                "**Recommendation:** Unknown error - check logs for details.",
                "- Review full error stack trace",
                "- Check file permissions and disk space",
                "- Verify Python environment and dependencies"
            ]
        }
        return recommendations.get(error_type, ["**Recommendation:** Review error details and logs."])

    def _extract_first_sentence(self, text: str, max_length: int = 200) -> str:
        """Extract the first meaningful sentence from text."""
        if not text:
            return "No explanation provided"

        # Split by sentence terminators
        sentences = re.split(r'[.!?]', text)
        first_sentence = sentences[0].strip() if sentences else text

        if len(first_sentence) > max_length:
            first_sentence = first_sentence[:max_length] + "..."

        return first_sentence
