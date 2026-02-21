"""
Multi-step AI document rewriter with structured workflow.

Follows Perplexity's recommendations for weak LLM rewriting:
1. Analyze and group recommendations by theme
2. Create diff-plan for each section
3. Rewrite section by plan with strict rules
4. Verify changes were applied
"""
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..domain.entities import RevisionItem
from ..domain.value_objects import DocumentType
from ..domain.change_record import ChangeRecord


logger = logging.getLogger(__name__)


class RevisionTheme(Enum):
    """Themes for grouping revisions."""
    FOCUS = "Фокус и приоритизация"
    VALIDATION = "Валидация и этапность"
    ARCHITECTURE = "Архитектура и технические риски"
    GTM = "GTM-стратегия и сегменты"
    BUSINESS_MODEL = "Бизнес-модель и экономика"
    RISKS = "Риски и проблемы"


@dataclass
class SectionPlan:
    """Diff-plan for a document section."""
    section_name: str
    original_content: str
    relevant_revisions: List[RevisionItem]
    additions: List[str]
    removals: List[str]
    emphasis: List[str]


@dataclass
class RewriteResult:
    """Result of rewriting a section."""
    section_name: str
    rewritten_content: str
    changes_applied: Dict[str, str]  # revision_id -> "applied/not_applied: reason"


class ConclusionAnalyzer:
    """
    Analyzes conclusion.md and groups revisions by theme.

    Maps debate room recommendations to document themes.
    """

    THEME_KEYWORDS = {
        RevisionTheme.FOCUS: [
            "фокус", "приоритет", "одновременный захват", "разнородные вертикали",
            "распыление ресурсов", "одной вертикали", "безопасный сегмент"
        ],
        RevisionTheme.VALIDATION: [
            "валидация", "проверка", "доказать", "подтвердить", "unit-экономика",
            "ручной режим", "пилоты", "этапы", "контрольные точки"
        ],
        RevisionTheme.ARCHITECTURE: [
            "архитектур", "модульная", "универсальное ядро", "адаптер",
            "масштабируемост", "интеграция", "безопасност", "самообслуживание"
        ],
        RevisionTheme.GTM: [
            "GTM", "статег", "сегмент", "рынок", "внутренн", "внешн",
            "экосистем", "партнеры", "предприятие"
        ],
        RevisionTheme.BUSINESS_MODEL: [
            "бизнес-модель", "экономик", "монетизаци", "маржинальност",
            "выручка", "подписк", "комисси", "GMV"
        ],
        RevisionTheme.RISKS: [
            "риск", "проблем", "угроз", "барьер", "сложност",
            "зависимост", "технически долг"
        ],
    }

    def group_by_theme(self, revisions: List[RevisionItem]) -> Dict[RevisionTheme, List[RevisionItem]]:
        """Group revisions by thematic category."""
        grouped: Dict[RevisionTheme, List[RevisionItem]] = {
            theme: [] for theme in RevisionTheme
        }

        for revision in revisions:
            # Find best matching theme based on keywords
            best_theme = self._classify_revision(revision)
            grouped[best_theme].append(revision)

        return grouped

    def _classify_revision(self, revision: RevisionItem) -> RevisionTheme:
        """Classify a single revision by theme."""
        content_lower = revision.content.lower()
        scores = {}

        for theme, keywords in self.THEME_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            scores[theme] = score

        # Return theme with highest score, or FOCUS as default
        if not scores or max(scores.values()) == 0:
            return RevisionTheme.FOCUS

        return max(scores, key=scores.get)

    def map_themes_to_sections(self, grouped: Dict[RevisionTheme, List[RevisionItem]]) -> Dict[str, List[RevisionItem]]:
        """Map themes to document sections."""
        section_map = {
            "Позиционирование": grouped[RevisionTheme.FOCUS] + grouped[RevisionTheme.GTM],
            "Цели": grouped[RevisionTheme.FOCUS] + grouped[RevisionTheme.BUSINESS_MODEL],
            "Ключевые проблемы": grouped[RevisionTheme.RISKS],
            "План действий": grouped[RevisionTheme.ARCHITECTURE] + grouped[RevisionTheme.VALIDATION],
            "Launch Strategy": grouped[RevisionTheme.GTM],
            "Post-Launch Plan": grouped[RevisionTheme.VALIDATION] + grouped[RevisionTheme.BUSINESS_MODEL],
        }

        # Clean empty sections
        return {k: v for k, v in section_map.items() if v}


class RewritePlanner:
    """
    Creates diff-plan for each section.

    Analyzes original content + recommendations and creates
    structured plan: what to add, remove, emphasize.
    """

    def create_plan(
        self,
        section_name: str,
        original_content: str,
        revisions: List[RevisionItem]
    ) -> SectionPlan:
        """Create diff-plan for a section."""
        additions = []
        removals = []
        emphasis = []

        for rev in revisions:
            content_lower = rev.content.lower()

            # Classify revision type
            if any(kw in content_lower for kw in [
                "риск", "проблема", "угроза", "слабость", "недостаток"
            ]):
                removals.append(rev.content)

            elif any(kw in content_lower for kw in [
                "сильная сторон", "позитив", "сохранит", "лучше"
            ]):
                emphasis.append(rev.content)

            elif any(kw in content_lower for kw in [
                "необходимо", "требует", "нужно", "доработат", "добавить", "включить"
            ]):
                additions.append(rev.content)

            else:
                # Default to addition
                additions.append(rev.content)

        return SectionPlan(
            section_name=section_name,
            original_content=original_content,
            relevant_revisions=revisions,
            additions=additions[:5],  # Limit to top 5
            removals=removals[:3],
            emphasis=emphasis[:3]
        )


class SectionRewriter:
    """
    Rewrites a single section with strict rules.

    Follows Perplexity's recommendations:
    - Preserves structure
    - Limited scope (±20% length)
    - References specific comments
    - No new entities
    """

    SYSTEM_PROMPT = """Ты – технический редактор продукта.
Твоя задача: аккуратно обновить ОДИН раздел product-vision документа на основе списка комментариев.

## Жёсткие правила:

1. **Сохраняй структуру раздела** (заголовки, списки, порядок подпунктов, объём ±20%)
2. **Меняй только то, что явно связано с комментариями** – не добавляй новые темы
3. **Каждое изменение ссылайся на конкретный пункт из COMMENTS** (ID пункта)
4. **Не выдумывай новую стратегию** – твоя задача переформулировать и донастроить акценты
5. **Не добавляй новые сущности** не упомянутые ни в исходном тексте, ни в комментариях

## Формат ответа:

SECTION_REWRITTEN:
[переписанный текст раздела]

CHANGES_APPLIED:
- [ID]: applied | not_applied — [краткое пояснение]

"""

    def __init__(self, llm: ChatOpenAI):
        """Initialize section rewriter."""
        self.llm = llm

    def rewrite_section(
        self,
        section_name: str,
        original_content: str,
        plan: SectionPlan
    ) -> RewriteResult:
        """
        Rewrite a section following the diff-plan.

        Args:
            section_name: Name of section to rewrite
            original_content: Original section content
            plan: Diff-plan for the section

        Returns:
            RewriteResult with rewritten content and changes tracking
        """
        # Build comments from plan
        comments = self._build_comments(plan)

        # Build prompt
        user_prompt = f"""SECTION_ORIGINAL:
{original_content}

COMMENTS:
{comments}

Перепиши раздел "{section_name}" согласно правилам выше."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ])

            content = response.content.strip()

            # Parse response
            rewritten, changes_applied = self._parse_response(content, plan)

            return RewriteResult(
                section_name=section_name,
                rewritten_content=rewritten,
                changes_applied=changes_applied
            )

        except Exception as e:
            logger.error(f"Failed to rewrite section '{section_name}': {e}")
            # Return original on error
            return RewriteResult(
                section_name=section_name,
                rewritten_content=original_content,
                changes_applied={}
            )

    def _build_comments(self, plan: SectionPlan) -> str:
        """Build formatted comments from plan."""
        lines = []

        for i, rev in enumerate(plan.relevant_revisions, 1):
            # Extract ID from revision (format: REV001, REV002, etc.)
            rev_id = rev.id if hasattr(rev, 'id') else f"REV{i:03d}"

            # Truncate long content
            content = rev.content[:200] + "..." if len(rev.content) > 200 else rev.content

            lines.append(f"[ID={rev_id}] {content}")

        return "\n".join(lines)

    def _parse_response(
        self,
        response: str,
        plan: SectionPlan
    ) -> Tuple[str, Dict[str, str]]:
        """Parse LLM response to extract rewritten content and changes."""
        # Split by SECTION_REWRITTEN and CHANGES_APPLIED
        parts = re.split(r'CHANGES_APPLIED:', response, maxsplit=1)

        if len(parts) == 2:
            rewritten_part, changes_part = parts

            # Extract rewritten content
            rewritten_match = re.search(r'SECTION_REWRITTEN:\s*(.+?)(?=CHANGES_APPLIED:|$)', response, re.DOTALL)
            if rewritten_match:
                rewritten = rewritten_match.group(1).strip()
            else:
                rewritten = rewritten_part.strip()

            # Parse changes
            changes_applied = self._parse_changes(changes_part, plan)

        else:
            # No CHANGES_APPLIED section, treat entire response as rewritten
            rewritten = response.strip()
            changes_applied = {}

        return rewritten, changes_applied

    def _parse_changes(self, changes_part: str, plan: SectionPlan) -> Dict[str, str]:
        """Parse changes applied section."""
        changes = {}

        for line in changes_part.strip().split('\n'):
            line = line.strip()
            if not line or not line.startswith('-'):
                continue

            # Parse: - [ID]: applied | not_applied — reason
            match = re.match(r'\[([^\]]+)\]:\s*(applied|not_applied)\s*—?\s*(.+)', line)
            if match:
                rev_id, status, reason = match.groups()
                changes[rev_id] = f"{status}: {reason}"

        return changes


class StructuredAIDocumentEditor:
    """
    Structured AI document editor following Perplexity's multi-step approach.

    Workflow:
    1. Analyze conclusions and group by theme
    2. Map themes to document sections
    3. Create diff-plan for each section
    4. Rewrite sections by plan with strict rules
    5. Verify changes were applied
    """

    def __init__(
        self,
        model: str,
        temperature: float,
        api_key: str,
        base_url: Optional[str] = None,
        batch_size: int = 5
    ):
        """Initialize structured AI editor."""
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=3000,  # Lower for more focused output
            api_key=api_key,
            base_url=base_url
        )

        self.analyzer = ConclusionAnalyzer()
        self.planner = RewritePlanner()
        self.rewriter = SectionRewriter(self.llm)
        self.batch_size = batch_size

    async def rewrite_document(
        self,
        content: str,
        revisions: List[RevisionItem]
    ) -> Tuple[str, List[ChangeRecord]]:
        """
        Rewrite entire document section by section with batch processing.

        Processes revisions in batches to avoid overwhelming the LLM.

        Args:
            content: Full document content (markdown)
            revisions: List of revisions to apply

        Returns:
            Tuple of (new_content, list_of_change_records)
        """
        logger.info(f"Starting AI rewrite with {len(revisions)} revisions (batch size: {self.batch_size})")

        # Calculate number of passes
        num_passes = (len(revisions) + self.batch_size - 1) // self.batch_size
        logger.info(f"Will process in {num_passes} passes")

        # Step 1: Group revisions by theme
        grouped = self.analyzer.group_by_theme(revisions)

        # Step 2: Map themes to sections
        section_map = self.analyzer.map_themes_to_sections(grouped)

        # Step 3: Parse document into sections
        sections = self._parse_sections(content)

        # Step 4: Process sections with batch revision limiting
        all_changes: List[ChangeRecord] = []
        current_content = content

        for pass_num in range(num_passes):
            # Get revisions for this pass
            start_idx = pass_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(revisions))
            pass_revisions = revisions[start_idx:end_idx]

            if not pass_revisions:
                break

            logger.info(f"Pass {pass_num + 1}/{num_passes}: processing revisions {start_idx + 1}-{end_idx}")

            # Group pass revisions by theme for this pass
            pass_grouped = self.analyzer.group_by_theme(pass_revisions)
            pass_section_map = self.analyzer.map_themes_to_sections(pass_grouped)

            # Process each section with revisions from this pass
            for section_name, section_content in sections.items():
                if section_name not in pass_section_map:
                    continue

                # Create plan for this pass
                plan = self.planner.create_plan(
                    section_name=section_name,
                    original_content=section_content,
                    revisions=pass_section_map[section_name]
                )

                if not plan.relevant_revisions:
                    continue

                # Rewrite section
                result = self.rewriter.rewrite_section(
                    section_name=section_name,
                    original_content=section_content,
                    plan=plan
                )

                # Update section content for next pass
                sections[section_name] = result.rewritten_content

                # Create change record
                change_record = ChangeRecord(
                    revision_id=f"PASS_{pass_num + 1}",
                    section=section_name,
                    action="UPDATE",
                    before=section_content,
                    after=result.rewritten_content
                )
                all_changes.append(change_record)

            # Update content for next iteration
            current_content = "\n\n".join(sections.values())

        # Join sections back
        new_content = current_content

        return new_content, all_changes

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections."""
        sections = {}
        current_section = "Введение"
        current_content = []

        for line in content.split('\n'):
            # Check for heading
            if line.strip().startswith('#'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                heading = line.strip().lstrip('#').strip()
                current_section = heading
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections
