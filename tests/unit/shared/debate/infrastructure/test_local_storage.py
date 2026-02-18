"""Tests for LocalFileStorage class."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage
from src.shared.debate.domain.entities import DebateRoom, DebateMessage, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus, RunId


@pytest.fixture
def storage():
    """Create a LocalFileStorage instance."""
    return LocalFileStorage()


@pytest.fixture
def sample_room():
    """Create a sample DebateRoom for testing."""
    return DebateRoom(
        room_id=RoomId("TPM_vs_CPO"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[
            DebateMessage(
                speaker=Speaker.PRO,
                content="Opening statement",
                stage="opening",
                timestamp="2024-01-01T00:00:00Z",
                validated=True
            )
        ],
        verdict=Verdict(
            winner=Speaker.PRO,
            explanation="TPM made stronger arguments"
        ),
        takeaways=["Good point 1", "Good point 2"]
    )


@pytest.fixture
def sample_run():
    """Create a sample RunId for testing."""
    return RunId.generate("What is the potential of this project?")


class TestLocalFileStorage:
    """Test suite for LocalFileStorage."""

    @pytest.mark.asyncio
    async def test_create_run_directory(self, storage, tmp_path, sample_run):
        """Should create run directory using asyncio.to_thread."""
        base_dir = tmp_path / "output"

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = None

            result = await storage.create_run_directory(base_dir, sample_run)

            expected_path = base_dir / sample_run.value
            mock_to_thread.assert_called_once()
            # Verify the path matches expected structure
            assert result == expected_path

    @pytest.mark.asyncio
    async def test_save_dialogue_json(self, storage, tmp_path, sample_room):
        """Should save room dialogue as JSON file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        await storage.save_dialogue_json(output_dir, sample_room)

        expected_file = output_dir / f"{sample_room.room_id.value}_dialogue.json"
        assert expected_file.exists()

        content = expected_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert data["room_id"] == sample_room.room_id.value
        assert data["pro_participant"] == "TPM"
        assert data["con_participant"] == "CPO"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["speaker"] == "PRO"

    @pytest.mark.asyncio
    async def test_save_dialogue_json_uses_to_thread(self, storage, tmp_path, sample_room):
        """Should use asyncio.to_thread for non-blocking I/O."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = None

            await storage.save_dialogue_json(output_dir, sample_room)

            # Verify to_thread was called with write_text
            assert mock_to_thread.called
            call_args = mock_to_thread.call_args
            assert call_args[0][1]  # Second arg is content
            assert call_args[1] == {"encoding": "utf-8"}

    @pytest.mark.asyncio
    async def test_save_report(self, storage, tmp_path):
        """Should save markdown report file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_content = "# Test Report\n\nThis is a test."
        report_name = "final_report.md"

        await storage.save_report(output_dir, report_name, report_content)

        report_path = output_dir / report_name
        assert report_path.exists()
        assert report_path.read_text(encoding="utf-8") == report_content

    @pytest.mark.asyncio
    async def test_save_metadata(self, storage, tmp_path):
        """Should save metadata as JSON file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "run_id": "RUN_20240101_120000_test",
            "question": "What is the potential?",
            "start_time": "2024-01-01T12:00:00Z",
            "end_time": "2024-01-01T12:30:00Z",
            "model": "gpt-4"
        }

        await storage.save_metadata(output_dir, metadata)

        metadata_path = output_dir / "metadata.json"
        assert metadata_path.exists()

        content = metadata_path.read_text(encoding="utf-8")
        data = json.loads(content)

        assert data == metadata
        assert json.dumps(data, indent=2)  # Verify it's pretty-printed

    @pytest.mark.asyncio
    async def test_save_metadata_with_complex_data(self, storage, tmp_path):
        """Should handle complex metadata with nested structures."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "run_id": "RUN_test",
            "room_statuses": {
                "tpm_cpo": "success",
                "tpm_cfo": "failed"
            },
            "errors": [
                {"room": "TPM_vs_CFO", "message": "Timeout error"}
            ]
        }

        await storage.save_metadata(output_dir, metadata)

        metadata_path = output_dir / "metadata.json"
        content = metadata_path.read_text(encoding="utf-8")
        data = json.loads(content)

        assert data["room_statuses"]["tpm_cpo"] == "success"
        assert len(data["errors"]) == 1

    @pytest.mark.asyncio
    async def test_save_report_with_unicode(self, storage, tmp_path):
        """Should correctly handle unicode content in reports."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_content = "# Отчёт\n\nПроверка русского языка: проверка"
        report_name = "russian_report.md"

        await storage.save_report(output_dir, report_name, report_content)

        report_path = output_dir / report_name
        content = report_path.read_text(encoding="utf-8")

        assert "Отчёт" in content
        assert "проверка" in content
