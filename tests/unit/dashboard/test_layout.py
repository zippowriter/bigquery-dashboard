"""Tests for LayoutBuilder module."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from dash import dash_table, html


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

        empty_df: pd.DataFrame = pd.DataFrame({"dataset_id": [], "table_id": []})

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
        assert len(fig.data) > 0  # pyright: ignore[reportArgumentType]
        # そのトレースがTableであることを確認
        assert isinstance(fig.data[0], go.Table)


class TestMergeTableData:
    """merge_table_data関数のテスト。"""

    def test_left_join_preserves_all_tables(self) -> None:
        """テーブル一覧の全行がLEFT JOINで保持されることを検証する。"""
        from src.dashboard.layout import merge_table_data

        # 3つのテーブルが存在
        tables_df = pd.DataFrame(
            {
                "dataset_id": ["ds1", "ds1", "ds2"],
                "table_id": ["t1", "t2", "t3"],
            }
        )

        # 1つのテーブルにのみ利用実績あり
        usage_df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        result = merge_table_data(tables_df, usage_df)

        # 全3行が保持される
        assert len(result) == 3
        assert list(result.columns) == [
            "dataset_id",
            "table_id",
            "reference_count",
            "unique_users",
        ]

    def test_zero_fill_for_missing_usage(self) -> None:
        """利用実績がないテーブルはreference_count=0、unique_users=0で補完されることを検証する。"""
        from src.dashboard.layout import merge_table_data

        tables_df = pd.DataFrame(
            {
                "dataset_id": ["ds1", "ds2"],
                "table_id": ["t1", "t2"],
            }
        )

        # ds1.t1のみ利用実績あり
        usage_df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [5],
                "unique_users": [2],
            }
        )

        result = merge_table_data(tables_df, usage_df)

        # ds2.t2の行を確認
        ds2_row: pd.DataFrame = result[  # pyright: ignore[reportUnknownVariableType, reportAssignmentType]
            (result["dataset_id"] == "ds2") & (result["table_id"] == "t2")
        ]
        assert ds2_row["reference_count"].iloc[0] == 0
        assert ds2_row["unique_users"].iloc[0] == 0

    def test_merge_with_empty_usage(self) -> None:
        """利用統計が空の場合、全テーブルが参照回数0で保持されることを検証する。"""
        from src.dashboard.layout import merge_table_data

        tables_df = pd.DataFrame(
            {
                "dataset_id": ["ds1", "ds2"],
                "table_id": ["t1", "t2"],
            }
        )

        # 利用統計なし
        usage_df = pd.DataFrame(
            {
                "dataset_id": [],
                "table_id": [],
                "reference_count": [],
                "unique_users": [],
            }
        )

        result = merge_table_data(tables_df, usage_df)

        assert len(result) == 2
        assert result["reference_count"].sum() == 0
        assert result["unique_users"].sum() == 0


class TestCreateUsageDataTable:
    """create_usage_datatable関数のテスト。"""

    def test_returns_datatable_component(self) -> None:
        """DataTableコンポーネントが返却されることを検証する。"""
        from src.dashboard.layout import create_usage_datatable

        df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        result = create_usage_datatable(df)

        assert isinstance(result, dash_table.DataTable)

    def test_datatable_has_correct_columns(self) -> None:
        """DataTableに4つのカラムが設定されていることを検証する。"""
        from src.dashboard.layout import create_usage_datatable

        df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        result = create_usage_datatable(df)

        column_ids: list[Any] = [col["id"] for col in result.columns]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert column_ids == [
            "dataset_id",
            "table_id",
            "reference_count",
            "unique_users",
        ]

    def test_datatable_has_japanese_column_names(self) -> None:
        """DataTableカラムに日本語名が設定されていることを検証する。"""
        from src.dashboard.layout import create_usage_datatable

        df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        result = create_usage_datatable(df)

        column_names: list[Any] = [col["name"] for col in result.columns]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert "データセットID" in column_names
        assert "テーブルID" in column_names
        assert "参照回数" in column_names
        assert "参照ユーザー数" in column_names

    def test_datatable_has_native_sort_enabled(self) -> None:
        """DataTableのネイティブソートが有効になっていることを検証する。"""
        from src.dashboard.layout import create_usage_datatable

        df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        result = create_usage_datatable(df)

        assert result.sort_action == "native"  # pyright: ignore[reportAttributeAccessIssue]
        assert result.sort_mode == "multi"  # pyright: ignore[reportAttributeAccessIssue]

    def test_datatable_has_conditional_style_for_zero_reference(self) -> None:
        """参照回数0件の行に条件付きスタイルが設定されていることを検証する。"""
        from src.dashboard.layout import create_usage_datatable

        df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [0],
                "unique_users": [0],
            }
        )

        result = create_usage_datatable(df)

        # style_data_conditionalに{reference_count} = 0のフィルタクエリが含まれることを確認
        has_zero_filter = False
        style_cond: dict[str, Any]
        for style_cond in result.style_data_conditional:  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
            # 条件は "if" キーの中にある
            if_cond: dict[str, Any] = style_cond.get("if", {})  # pyright: ignore[reportUnknownVariableType]
            filter_query: str = if_cond.get("filter_query", "")  # pyright: ignore[reportUnknownVariableType]
            if "{reference_count} = 0" in filter_query:
                has_zero_filter = True
                break
        assert has_zero_filter


class TestBuildLayoutWithUsageStats:
    """利用統計を統合したbuild_layout関数のテスト。"""

    def test_build_layout_with_datatable(self) -> None:
        """正常時にDataTableが含まれるhtml.Divを返却することを検証する。"""
        from unittest.mock import patch

        from src.dashboard.layout import build_layout

        mock_tables_df = pd.DataFrame(
            {
                "dataset_id": ["ds1", "ds2"],
                "table_id": ["t1", "t2"],
            }
        )

        mock_usage_df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
                "reference_count": [10],
                "unique_users": [3],
            }
        )

        with patch(
            "src.dashboard.layout.fetch_table_list", return_value=mock_tables_df
        ):
            with patch(
                "src.dashboard.layout.fetch_table_usage_stats",
                return_value=mock_usage_df,
            ):
                layout = build_layout(project_id="test-project")

        assert isinstance(layout, html.Div)
        # DataTableが含まれていることを確認
        layout_str = str(layout)
        assert "DataTable" in layout_str or "usage-table" in layout_str

    def test_build_layout_with_none_project_id_skips_table(self) -> None:
        """project_id=Noneの場合、テーブル表示をスキップすることを検証する。"""
        from src.dashboard.layout import build_layout

        layout = build_layout(project_id=None)

        assert isinstance(layout, html.Div)
        # DataTableが含まれていないことを確認
        layout_str = str(layout)
        assert "usage-table" not in layout_str

    def test_build_layout_shows_error_on_usage_stats_api_error(self) -> None:
        """利用統計取得のAPI エラー時にエラーメッセージが表示されることを検証する。"""
        from unittest.mock import patch

        from google.api_core.exceptions import GoogleAPIError

        from src.dashboard.layout import build_layout

        mock_tables_df = pd.DataFrame(
            {
                "dataset_id": ["ds1"],
                "table_id": ["t1"],
            }
        )

        with patch(
            "src.dashboard.layout.fetch_table_list", return_value=mock_tables_df
        ):
            with patch(
                "src.dashboard.layout.fetch_table_usage_stats",
                side_effect=GoogleAPIError("Usage stats API Error"),
            ):
                layout = build_layout(project_id="test-project")

        assert isinstance(layout, html.Div)
        # エラーメッセージが含まれていることを確認
        layout_str = str(layout)
        assert "エラー" in layout_str or "Error" in layout_str
