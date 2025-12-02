"""Tests for Dash application creation."""

import pytest


class TestCreateApp:
    """Tests for create_app function."""

    def test_create_app_with_default_config(self) -> None:
        """Verify create_app works with default config."""
        from src.dashboard.app import create_app
        from src.dashboard.config import AppConfig

        config = AppConfig()
        app = create_app(config)
        assert app.title == "BigQueryテーブル利用状況"

    def test_create_app_with_invalid_config_type(self) -> None:
        """Verify create_app raises error for invalid config type."""
        from src.dashboard.app import create_app

        with pytest.raises((TypeError, ValueError)):
            create_app(None)  # type: ignore
