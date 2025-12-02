"""UIコンポーネント。

Dashコンポーネントの生成を提供する。
"""

from dash import dash_table, html

from src.dashboard.domain.models import TableUsage


def create_usage_datatable(usages: list[TableUsage]) -> dash_table.DataTable:
    """利用統計からDataTableコンポーネントを生成する。

    ドメインモデルのリストからDash DataTableを生成し、ネイティブソート機能を有効化。
    参照回数0件の行には条件付きスタイルで薄い赤の背景色を適用する。

    Args:
        usages: テーブル利用統計のリスト

    Returns:
        ソート可能、条件付きスタイル適用済みのDataTableコンポーネント
    """
    data: list[dict[str, str | int]] = [
        {
            "dataset_id": u.dataset_id,
            "table_id": u.table_id,
            "reference_count": u.reference_count,
            "unique_users": u.unique_users,
        }
        for u in usages
    ]

    return dash_table.DataTable(
        id="usage-table",
        columns=[
            {"name": "データセットID", "id": "dataset_id"},
            {"name": "テーブルID", "id": "table_id"},
            {"name": "参照回数", "id": "reference_count"},
            {"name": "参照ユーザー数", "id": "unique_users"},
        ],
        data=data,
        sort_action="native",
        sort_mode="multi",
        style_data_conditional=[
            {
                "if": {"filter_query": "{reference_count} = 0"},
                "backgroundColor": "#FFCCCC",
            }
        ],
        style_header={
            "backgroundColor": "paleturquoise",
            "fontWeight": "bold",
        },
        style_cell={"textAlign": "left"},
    )


def create_error_message(message: str) -> html.P:
    """エラーメッセージコンポーネントを生成する。

    Args:
        message: 表示するエラーメッセージ

    Returns:
        赤色スタイルのParagraphコンポーネント
    """
    return html.P(message, style={"color": "red"})
