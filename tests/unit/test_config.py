"""Tests for AppConfig configuration class."""

import pytest
from pydantic import ValidationError


class TestAppConfig:
    """Tests for AppConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Verify AppConfig has correct default values."""
        from src.dashboard.config import AppConfig

        config = AppConfig()
        assert config.title == "BigQueryテーブル利用状況"
        assert config.host == "127.0.0.1"
        assert config.port == 8050
        assert config.debug is True

    def test_custom_title(self) -> None:
        """Verify AppConfig accepts custom title."""
        from src.dashboard.config import AppConfig

        config = AppConfig(title="Custom Dashboard")
        assert config.title == "Custom Dashboard"

    def test_empty_title_rejected(self) -> None:
        """Verify AppConfig rejects empty title."""
        from src.dashboard.config import AppConfig

        with pytest.raises(ValidationError):
            AppConfig(title="")
