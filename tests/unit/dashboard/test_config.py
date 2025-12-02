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

    def test_project_id_accepts_custom_value(self) -> None:
        """Verify AppConfig accepts custom project_id."""
        from src.dashboard.config import AppConfig

        config = AppConfig(project_id="my-test-project")
        assert config.project_id == "my-test-project"

    def test_project_id_default_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify AppConfig has None as default project_id when env var is not set."""
        from src.dashboard.config import AppConfig

        # 環境変数をクリアして確定的にテスト
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        config = AppConfig()
        assert config.project_id is None
