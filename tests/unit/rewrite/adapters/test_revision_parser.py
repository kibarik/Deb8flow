"""
Unit tests for ConclusionParser.
"""
import pytest
from pathlib import Path
from src.rewrite.adapters.revision_parser import ConclusionParser
from src.rewrite.domain.entities import RevisionItem
from src.rewrite.domain.value_objects import RevisionAction


@pytest.fixture
def parser():
    """Create a parser instance."""
    return ConclusionParser()


@pytest.fixture
def sample_conclusion(tmp_path):
    """Create a sample conclusion.md file."""
    content = """# Чеклист рекомендаций

**Вопрос комитета:** Should we build X?

**Сгенерировано:** 2025-02-20

## Рекомендации

1. Add error handling for timeout cases [CPO]
2. Clarify API authentication flow [CTO]
3. Add example for edge case [CFO]

---

*Подробная информация о дебатах доступна в [final_report.md](final_report.md)*
"""
    file_path = tmp_path / "conclusion.md"
    file_path.write_text(content)
    return file_path


class TestConclusionParser:
    """Test suite for ConclusionParser."""

    def test_parse_standard_format(self, parser, sample_conclusion):
        """Test parsing standard conclusion format."""
        revisions = parser.parse(sample_conclusion)

        assert len(revisions) == 3
        assert revisions[0].id == "REV001"
        assert "error handling" in revisions[0].content.lower()
        assert revisions[0].section == "CPO"
        assert revisions[0].action == RevisionAction.UPDATE
        assert revisions[0].verified is False

    def test_parse_without_room_tags(self, parser, tmp_path):
        """Test parsing items without room tags."""
        content = """## Рекомендации

1. First item
2. Second item
3. Third item
"""
        file_path = tmp_path / "conclusion.md"
        file_path.write_text(content)

        revisions = parser.parse(file_path)

        assert len(revisions) == 3
        assert revisions[0].section == "general"
        assert revisions[1].section == "general"

    def test_parse_fallback_bullet_points(self, parser, tmp_path):
        """Test fallback parsing with bullet points."""
        content = """## Рекомендации

- First item
- Second item
- Third item
"""
        file_path = tmp_path / "conclusion.md"
        file_path.write_text(content)

        revisions = parser.parse(file_path)

        assert len(revisions) == 3

    def test_file_not_found(self, parser):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/conclusion.md"))

    def test_no_recommendations_section(self, parser, tmp_path):
        """Test error when recommendations section is missing."""
        content = "# Some other content\n\nNo recommendations here."
        file_path = tmp_path / "conclusion.md"
        file_path.write_text(content)

        with pytest.raises(ValueError, match="No.*Рекомендации.*section"):
            parser.parse(file_path)

    def test_encoding_fallback(self, parser, tmp_path):
        """Test reading file with different encoding."""
        content = "## Рекомендации\n\n1. Тест на русском"
        file_path = tmp_path / "conclusion.md"
        file_path.write_text(content, encoding="cp1251")

        revisions = parser.parse(file_path)

        assert len(revisions) == 1
        assert "русск" in revisions[0].content.lower() or "тест" in revisions[0].content.lower()
