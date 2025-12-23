"""Tests for configuration layer."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from openai import AuthenticationError
from src.config import Config, load_config, save_config


def test_load_config_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading config when file doesn't exist."""
    # Use a non-existent path
    fake_config_path = tmp_path / "nonexistent.json"
    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", fake_config_path)

    result = load_config()
    assert result is None


def test_load_config_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading a valid config file."""
    config_file = tmp_path / ".product_categorizer_config.json"
    config_data = {
        "openai_api_key": "sk-test-key-123",
        "model_name": "gpt-5-nano-2025-08-07",
    }
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    result = load_config()
    assert result is not None
    assert result.openai_api_key == "sk-test-key-123"
    assert result.model_name == "gpt-5-nano-2025-08-07"


def test_load_config_missing_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading config with missing required fields."""
    config_file = tmp_path / ".product_categorizer_config.json"
    # Missing model_name field
    config_data = {"openai_api_key": "sk-test-key-123"}
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    result = load_config()
    assert result is None


def test_load_config_malformed_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading config with malformed JSON."""
    config_file = tmp_path / ".product_categorizer_config.json"
    config_file.write_text("{invalid json}", encoding="utf-8")

    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    result = load_config()
    assert result is None


@pytest.mark.asyncio
async def test_save_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test saving config to file."""
    config_file = tmp_path / ".product_categorizer_config.json"
    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    mock_client = Mock()
    mock_client.models.list = AsyncMock(return_value=Mock())
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("src.config.AsyncOpenAI", mock_openai)

    config = Config(
        openai_api_key="sk-new-key-456",
        model_name="gpt-5-mini-2025-08-07",
    )

    await save_config(config)

    mock_openai.assert_called_once_with(api_key="sk-new-key-456")
    mock_client.models.list.assert_awaited_once()

    # Verify file was created
    assert config_file.exists()

    # Verify contents
    with config_file.open("r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["openai_api_key"] == "sk-new-key-456"
    assert saved_data["model_name"] == "gpt-5-mini-2025-08-07"


@pytest.mark.asyncio
async def test_save_and_load_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that saving and loading config preserves data."""
    config_file = tmp_path / ".product_categorizer_config.json"
    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    mock_client = Mock()
    mock_client.models.list = AsyncMock(return_value=Mock())
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("src.config.AsyncOpenAI", mock_openai)

    original_config = Config(
        openai_api_key="sk-roundtrip-test",
        model_name="gpt-4o-mini",
    )

    await save_config(original_config)
    loaded_config = load_config()

    assert loaded_config is not None
    assert loaded_config.openai_api_key == original_config.openai_api_key
    assert loaded_config.model_name == original_config.model_name


@pytest.mark.asyncio
async def test_save_config_invalid_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test saving config with invalid API key raises error."""
    config_file = tmp_path / ".product_categorizer_config.json"
    monkeypatch.setattr("src.config.CONFIG_FILE_PATH", config_file)

    mock_client = Mock()
    mock_client.models.list = AsyncMock(
        side_effect=AuthenticationError(
            "Invalid API key",
            response=Mock(status_code=401),
            body=None,
        )
    )
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("src.config.AsyncOpenAI", mock_openai)

    config = Config(
        openai_api_key="sk-invalid-key",
        model_name="gpt-5-nano-2025-08-07",
    )

    with pytest.raises(ValueError, match=r"Invalid API key provided"):
        await save_config(config)

    assert not config_file.exists()
