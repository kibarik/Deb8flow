"""
Tests for MCP analyze_specification tool integration.
"""

import pytest
from pathlib import Path
from src.mcp.tools.analyze_specification import analyze_specification, SDDAnalyzer
from src.mcp.models import AnalyzeSpecInput


class TestAnalyzeSpecificationInput:
    """Test input validation."""

    def test_validate_spec_type(self):
        """Test spec_type validation."""
        # Valid types
        for spec_type in ['PRD', 'SDD', 'TDD', 'UNKNOWN']:
            input_data = AnalyzeSpecInput(
                spec_content="test content",
                spec_type=spec_type
            )
            assert input_data.spec_type == spec_type

    def test_validate_detail_level(self):
        """Test detail_level validation."""
        for level in ['quick', 'thorough']:
            input_data = AnalyzeSpecInput(
                spec_content="test content",
                detail_level=level
            )
            assert input_data.detail_level == level

    def test_exactly_one_input(self):
        """Test that exactly one of spec_path or spec_content is provided."""
        # Neither provided
        with pytest.raises(ValueError, match="Either spec_path or spec_content must be provided"):
            input_data = AnalyzeSpecInput()
            input_data.validate_input()

        # Both provided
        with pytest.raises(ValueError, match="Only one of spec_path or spec_content should be provided"):
            input_data = AnalyzeSpecInput(
                spec_path="test.md",
                spec_content="content"
            )
            input_data.validate_input()


class TestSDDAnalyzer:
    """Test SDDAnalyzer class."""

    def test_load_config(self):
        """Test configuration loading."""
        analyzer = SDDAnalyzer()
        analyzer._load_config()
        assert analyzer.config is not None
        assert analyzer.config.llm.model is not None

    def test_create_prompt_loader(self):
        """Test prompt loader creation."""
        analyzer = SDDAnalyzer()
        analyzer._load_config()
        prompt_loader = analyzer._create_prompt_loader()
        assert prompt_loader is not None

    def test_load_agent_prompt(self):
        """Test agent prompt loading."""
        analyzer = SDDAnalyzer()
        analyzer._load_config()

        # Load main agent prompt
        pro_prompt = analyzer._load_agent_prompt(
            analyzer.config.agents.main.prompt,
            analyzer.config.agents.main.name
        )
        assert pro_prompt is not None
        assert len(pro_prompt) > 0

    def test_validate_input_with_content(self):
        """Test input validation with spec_content."""
        analyzer = SDDAnalyzer()
        input_data = AnalyzeSpecInput(
            spec_content="This is a test specification with some content."
        )
        content = analyzer._validate_input(input_data)
        assert content == "This is a test specification with some content."

    def test_validate_input_with_empty_content(self):
        """Test input validation rejects empty content."""
        analyzer = SDDAnalyzer()
        input_data = AnalyzeSpecInput(
            spec_content="   "
        )
        with pytest.raises(ValueError, match="Specification content is empty"):
            analyzer._validate_input(input_data)

    def test_validate_input_with_file(self, tmp_path):
        """Test input validation with spec_path."""
        # Create test file
        test_file = tmp_path / "test_spec.md"
        test_file.write_text("# Test Specification\n\nSome content here.")

        analyzer = SDDAnalyzer()
        input_data = AnalyzeSpecInput(
            spec_path=str(test_file)
        )
        content = analyzer._validate_input(input_data)
        assert "# Test Specification" in content

    def test_validate_input_with_missing_file(self):
        """Test input validation with missing file."""
        analyzer = SDDAnalyzer()
        input_data = AnalyzeSpecInput(
            spec_path="/nonexistent/file.md"
        )
        with pytest.raises(ValueError, match="Specification file not found"):
            analyzer._validate_input(input_data)


class TestAnalyzeSpecification:
    """Test analyze_specification function."""

    @pytest.mark.asyncio
    async def test_returns_dict_structure(self):
        """Test that function returns proper dictionary structure."""
        result = await analyze_specification(
            spec_content="# Test SDD\n\nThis is a minimal specification.",
            spec_type="SDD",
            detail_level="quick"
        )

        # Check result structure
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'weak_points' in result
        assert 'recommendations' in result
        assert 'unclear_sections' in result
        assert 'metadata' in result

    @pytest.mark.asyncio
    async def test_metadata_fields(self):
        """Test that metadata contains required fields."""
        result = await analyze_specification(
            spec_content="# Test SDD\n\nContent here.",
            detail_level="quick"
        )

        metadata = result['metadata']
        assert 'model_used' in metadata
        assert 'agents_used' in metadata
        assert 'analysis_time_ms' in metadata
        assert 'debate_mode' in metadata
        assert 'num_rounds' in metadata

    @pytest.mark.asyncio
    async def test_agents_list_includes_configured_agents(self):
        """Test that agents_used includes Architect and opponents."""
        result = await analyze_specification(
            spec_content="# Test\n\nContent.",
            detail_level="quick"
        )

        # Check result status - might be error if no API key
        assert result['status'] in ['success', 'partial', 'error']

        # If successful, check agents
        if result['status'] == 'success':
            agents = result['metadata']['agents_used']
            assert 'Architect' in agents
            # At least one opponent should be present
            assert len(agents) > 1
        else:
            # Error case - still should have metadata
            assert 'metadata' in result
            assert 'agents_used' in result['metadata']

    @pytest.mark.asyncio
    async def test_async_execution_real(self):
        """Verify async function actually executes when awaited."""
        # Minimal test that verifies real async execution
        result = await analyze_specification(
            spec_content="Test specification",
            spec_type="SDD"
        )
        # Verify result is dict (not coroutine)
        assert isinstance(result, dict)
        # Verify status field exists
        assert "status" in result
