"""
Unit tests for application layer ports.

Tests that the protocol interfaces are properly defined and can be implemented.
"""

import pytest
from pathlib import Path
from src.shared.debate.application.ports import DebateExecutor, ReportGenerator, FileStorage
from src.shared.debate.domain.entities import DebateRoom, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


class MockDebateExecutor:
    """Mock implementation of DebateExecutor port."""

    async def execute(self, **kwargs):
        return DebateRoom(
            room_id=RoomId("test"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.PRO, explanation="Test")
        )


@pytest.mark.asyncio
async def test_debate_executor_protocol():
    """Test that MockDebateExecutor implements DebateExecutor protocol."""
    executor: DebateExecutor = MockDebateExecutor()
    result = await executor.execute(
        room_id=RoomId("test"),
        pro_prompt_path=Path("test.txt"),
        con_prompt_path=Path("test.txt"),
        question="test",
        prd_content="test",
        model=None,
        language=None,
        max_retries=2,
        json_output_path=None
    )
    assert result.is_successful
    assert result.verdict is not None
    assert result.verdict.winner == Speaker.PRO


class MockReportGenerator:
    """Mock implementation of ReportGenerator port."""

    def generate_final_report(self, run_id, prd_path, question, rooms, metadata):
        return f"# Report for {run_id}"

    def generate_conclusion(self, question, rooms, metadata):
        return "# Conclusion"

    def generate_intermediate_report(self, run_id, question, rooms, metadata):
        return f"# Intermediate {run_id}"


def test_report_generator_protocol():
    """Test that MockReportGenerator implements ReportGenerator protocol."""
    generator: ReportGenerator = MockReportGenerator()

    final = generator.generate_final_report(
        run_id="test",
        prd_path="test.txt",
        question="test",
        rooms=[],
        metadata={}
    )
    assert "test" in final

    conclusion = generator.generate_conclusion(
        question="test",
        rooms=[],
        metadata={}
    )
    assert "Conclusion" in conclusion

    intermediate = generator.generate_intermediate_report(
        run_id="test",
        question="test",
        rooms=[],
        metadata={}
    )
    assert "test" in intermediate


class MockFileStorage:
    """Mock implementation of FileStorage port."""

    async def create_run_directory(self, base_dir, run_id):
        return base_dir / run_id.value

    async def save_prd(self, output_dir, prd_path):
        pass

    async def save_dialogue_json(self, output_dir, room):
        pass

    async def save_report(self, output_dir, report_name, content):
        pass

    async def save_metadata(self, output_dir, metadata):
        pass


@pytest.mark.asyncio
async def test_file_storage_protocol():
    """Test that MockFileStorage implements FileStorage protocol."""
    storage: FileStorage = MockFileStorage()

    path = await storage.create_run_directory(
        Path("/tmp"),
        RoomId("test")
    )
    assert "test" in str(path)

    # These should not raise errors
    await storage.save_prd(Path("/tmp"), "test.txt")

    await storage.save_dialogue_json(Path("/tmp"), DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=Verdict(winner=Speaker.PRO, explanation="Test")
    ))

    await storage.save_report(Path("/tmp"), "test.md", "# Test")

    await storage.save_metadata(Path("/tmp"), {})
