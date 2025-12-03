"""UIコンポーネントのテスト。"""

from typing import Any

from dash import dash_table, html

from src.shared.domain.models import TableUsage
from src.dashboard.presentation.components import create_error_message, create_usage_datatable


class TestCreateUsageDataTable:
    """create_usage_datatable関数のテスト。"""

    def test_returns_datatable_component(self) -> None:
        """DataTableコンポーネントが返却されることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]

        result = create_usage_datatable(usages)

        assert isinstance(result, dash_table.DataTable)

    def test_datatable_has_correct_columns(self) -> None:
        """DataTableに5つのカラムが設定されていることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]

        result = create_usage_datatable(usages)

        column_ids: list[Any] = [col["id"] for col in result.columns]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert column_ids == [
            "dataset_id",
            "table_id",
            "reference_count",
            "unique_users",
            "is_leaf",
        ]

    def test_datatable_has_japanese_column_names(self) -> None:
        """DataTableカラムに日本語名が設定されていることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]

        result = create_usage_datatable(usages)

        column_names: list[Any] = [col["name"] for col in result.columns]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert "データセットID" in column_names
        assert "テーブルID" in column_names
        assert "参照回数" in column_names
        assert "参照ユーザー数" in column_names
        assert "リーフ" in column_names

    def test_datatable_has_native_sort_enabled(self) -> None:
        """DataTableのネイティブソートが有効になっていることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]

        result = create_usage_datatable(usages)

        assert result.sort_action == "native"  # pyright: ignore[reportAttributeAccessIssue]
        assert result.sort_mode == "multi"  # pyright: ignore[reportAttributeAccessIssue]

    def test_datatable_has_conditional_style_for_zero_reference(self) -> None:
        """参照回数0件の行に条件付きスタイルが設定されていることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=0, unique_users=0),
        ]

        result = create_usage_datatable(usages)

        # style_data_conditionalに{reference_count} = 0のフィルタクエリが含まれることを確認
        has_zero_filter = False
        style_cond: dict[str, Any]
        for style_cond in result.style_data_conditional:  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
            if_cond: dict[str, Any] = style_cond.get("if", {})  # pyright: ignore[reportUnknownVariableType]
            filter_query: str = if_cond.get("filter_query", "")  # pyright: ignore[reportUnknownVariableType]
            if "{reference_count} = 0" in filter_query:
                has_zero_filter = True
                break
        assert has_zero_filter


class TestCreateErrorMessage:
    """create_error_message関数のテスト。"""

    def test_returns_html_paragraph(self) -> None:
        """html.Pコンポーネントが返却されることを検証する。"""
        result = create_error_message("テストエラー")

        assert isinstance(result, html.P)

    def test_contains_message_text(self) -> None:
        """メッセージテキストが含まれることを検証する。"""
        result = create_error_message("テストエラー")

        assert "テストエラー" in str(result)


class TestDataTableIsLeafColumn:
    """is_leaf列関連のテスト。"""

    def test_is_leaf_column_shows_checkmark_for_leaf_tables(self) -> None:
        """リーフテーブルの行に✓が表示されることを検証する。"""
        usages = [
            TableUsage(
                dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3, is_leaf=True
            ),
        ]

        result = create_usage_datatable(usages)

        data: list[dict[str, str | int]] = result.data  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert data[0]["is_leaf"] == "✓"

    def test_is_leaf_column_shows_empty_for_non_leaf_tables(self) -> None:
        """非リーフテーブルの行は空欄になることを検証する。"""
        usages = [
            TableUsage(
                dataset_id="ds1",
                table_id="t1",
                reference_count=10,
                unique_users=3,
                is_leaf=False,
            ),
        ]

        result = create_usage_datatable(usages)

        data: list[dict[str, str | int]] = result.data  # pyright: ignore[reportAttributeAccessIssue,reportUnknownVariableType]
        assert data[0]["is_leaf"] == ""
