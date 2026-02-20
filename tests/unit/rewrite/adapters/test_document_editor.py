"""
Unit tests for document editors.
"""
import pytest
from src.rewrite.adapters.document_editor import MarkdownEditor, TextEditor
from src.rewrite.domain.entities import RevisionItem
from src.rewrite.domain.value_objects import RevisionAction


class TestMarkdownEditor:
    """Test markdown document editing."""

    @pytest.fixture
    def editor(self):
        return MarkdownEditor()

    @pytest.fixture
    def sample_markdown(self):
        return """# Document

## Introduction

This is the intro.

## Features

Feature one description.
Feature two description.

## Conclusion

Final thoughts.
"""

    def test_parse_sections(self, editor, sample_markdown):
        """Test section parsing."""
        editor.parse_sections(sample_markdown)

        assert len(editor.sections) >= 3
        assert editor.sections[0][1] == "Document"  # Root h1
        assert any(s[1] == "Introduction" for s in editor.sections)
        assert any(s[1] == "Features" for s in editor.sections)

    def test_find_section_exact_match(self, editor, sample_markdown):
        """Test finding section by exact name."""
        pos_range = editor.find_section(sample_markdown, "Features")

        assert pos_range is not None
        assert "Feature one" in sample_markdown[pos_range[0]:pos_range[1]]

    def test_find_section_fuzzy_match(self, editor, sample_markdown):
        """Test fuzzy section matching."""
        pos_range = editor.find_section(sample_markdown, "feature")  # Lowercase

        assert pos_range is not None

    def test_insert_revision(self, editor, sample_markdown):
        """Test inserting content into section."""
        revision = RevisionItem(
            id="R001",
            content="New feature description.",
            section="Features",
            action=RevisionAction.INSERT
        )

        result = editor.apply_revision(sample_markdown, revision)

        assert "New feature description" in result
        assert result.count("Feature") >= sample_markdown.count("Feature")

    def test_update_revision(self, editor, sample_markdown):
        """Test updating content in section."""
        revision = RevisionItem(
            id="R001",
            content="Updated feature description.",
            section="Features",
            action=RevisionAction.UPDATE
        )

        result = editor.apply_revision(sample_markdown, revision)

        assert "Updated feature description" in result

    def test_delete_revision(self, editor, sample_markdown):
        """Test deleting content from section."""
        # Get initial count
        initial_count = sample_markdown.count("Feature one")

        revision = RevisionItem(
            id="R001",
            content="Feature one description",
            section="Features",
            action=RevisionAction.DELETE
        )

        result = editor.apply_revision(sample_markdown, revision)

        # Check that deletion was attempted
        assert "Feature one description" not in result or result.count("Feature one description") < initial_count


class TestTextEditor:
    """Test text document editing."""

    @pytest.fixture
    def editor(self):
        return TextEditor()

    @pytest.fixture
    def sample_text(self):
        return """Line one
Line two with keyword
Line three
Another line with keyword
"""

    def test_find_target_location(self, editor, sample_text):
        """Test finding location by keyword."""
        revision = RevisionItem(
            id="R001",
            content="New line",
            section="keyword",
            action=RevisionAction.INSERT
        )

        pos = editor.find_target_location(sample_text, revision)

        assert pos > 0
        assert "keyword" in sample_text[:pos]

    def test_insert_revision(self, editor, sample_text):
        """Test inserting into text file."""
        revision = RevisionItem(
            id="R001",
            content="Inserted line",
            section="Line two",
            action=RevisionAction.INSERT
        )

        result = editor.apply_revision(sample_text, revision)

        assert "Inserted line" in result
        assert result.count("\n") >= sample_text.count("\n")

    def test_update_revision(self, editor, sample_text):
        """Test updating line in text file."""
        revision = RevisionItem(
            id="R001",
            content="Updated line two",
            section="keyword",
            action=RevisionAction.UPDATE
        )

        result = editor.apply_revision(sample_text, revision)

        assert "Updated line two" in result

    def test_delete_revision(self, editor, sample_text):
        """Test deleting line from text file."""
        revision = RevisionItem(
            id="R001",
            content="Line two with keyword",
            section="keyword",
            action=RevisionAction.DELETE
        )

        result = editor.apply_revision(sample_text, revision)

        assert "Line two with keyword" not in result
