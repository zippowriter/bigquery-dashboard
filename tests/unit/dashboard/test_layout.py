"""Tests for LayoutBuilder module."""

import pandas as pd
import plotly.graph_objects as go
from dash import html


class TestLayoutBuilder:
    """Tests for layout construction functions."""

    def test_build_layout_returns_div(self) -> None:
        """Verify build_layout returns html.Div component."""
        from src.dashboard.layout import build_layout

        layout = build_layout()
        assert isinstance(layout, html.Div)

    def test_build_layout_with_project_id_returns_div(self) -> None:
        """project_idを渡した場合もhtml.Divを返却することを検証する。"""
        from unittest.mock import patch

        from src.dashboard.layout import build_layout

        mock_df = pd.DataFrame(
            {
                "dataset_id": ["dataset1"],
                "table_id": ["table1"],
            }
        )

        with patch("src.dashboard.layout.fetch_table_list", return_value=mock_df):
            layout = build_layout(project_id="test-project")

        assert isinstance(layout, html.Div)

    def test_build_layout_shows_error_message_on_api_error(self) -> None:
        """BigQuery API接続エラー時にエラーメッセージが表示されることを検証する。"""
        from unittest.mock import patch

        from google.api_core.exceptions import GoogleAPIError

        from src.dashboard.layout import build_layout

        with patch(
            "src.dashboard.layout.fetch_table_list",
            side_effect=GoogleAPIError("API Error"),
        ):
            layout = build_layout(project_id="test-project")

        # エラーメッセージが含まれていることを確認（html.Divの中身を検査）
        assert isinstance(layout, html.Div)
        # childrenにエラーメッセージを含むコンポーネントがあることを確認
        layout_str = str(layout)
        assert "エラー" in layout_str or "Error" in layout_str

    def test_build_layout_shows_empty_message_when_no_tables(self) -> None:
        """テーブル情報が0件の場合にメッセージが表示されることを検証する。"""
        from unittest.mock import patch

        from src.dashboard.layout import build_layout

        empty_df = pd.DataFrame(columns=["dataset_id", "table_id"])

        with patch("src.dashboard.layout.fetch_table_list", return_value=empty_df):
            layout = build_layout(project_id="test-project")

        assert isinstance(layout, html.Div)
        # 空のテーブルに関するメッセージが含まれていることを確認
        layout_str = str(layout)
        assert "存在しません" in layout_str or "テーブルが" in layout_str


class TestCreateTableFigure:
    """Tests for create_table_figure function."""

    def test_returns_go_figure(self) -> None:
        """create_table_figureがgo.Figureを返却することを検証する。"""
        from src.dashboard.layout import create_table_figure

        df = pd.DataFrame(
            {
                "dataset_id": ["dataset1", "dataset2"],
                "table_id": ["table1", "table2"],
            }
        )
        fig = create_table_figure(df)

        assert isinstance(fig, go.Figure)

    def test_figure_contains_table_trace(self) -> None:
        """作成されたFigureがTableトレースを含むことを検証する。"""
        from src.dashboard.layout import create_table_figure

        df = pd.DataFrame(
            {
                "dataset_id": ["dataset1"],
                "table_id": ["table1"],
            }
        )
        fig = create_table_figure(df)

        # Figureに少なくとも1つのトレースがあることを確認
        assert len(fig.data) > 0
        # そのトレースがTableであることを確認
        assert isinstance(fig.data[0], go.Table)
