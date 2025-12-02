"""Tests for Dash application creation."""

from unittest.mock import patch

import pandas as pd
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

        with pytest.raises(ValueError):
            create_app(None)  # type: ignore

    def test_create_app_passes_project_id_to_layout(self) -> None:
        """create_appがproject_idをbuild_layoutに渡すことを検証する。"""
        from src.dashboard.app import create_app
        from src.dashboard.config import AppConfig

        mock_df = pd.DataFrame(
            {
                "dataset_id": ["dataset1"],
                "table_id": ["table1"],
            }
        )

        config = AppConfig(project_id="test-project")

        with patch(
            "src.dashboard.layout.fetch_table_list", return_value=mock_df
        ) as mock_fetch:
            create_app(config)
            mock_fetch.assert_called_once_with("test-project")

    def test_create_app_skips_table_display_when_project_id_is_none(self) -> None:
        """project_idがNoneの場合、テーブル表示をスキップすることを検証する。"""
        from src.dashboard.app import create_app
        from src.dashboard.config import AppConfig

        config = AppConfig(project_id=None)

        with patch("src.dashboard.layout.fetch_table_list") as mock_fetch:
            create_app(config)
            # fetch_table_listが呼ばれないことを確認
            mock_fetch.assert_not_called()
