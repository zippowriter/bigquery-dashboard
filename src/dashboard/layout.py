"""Layout builder module for dashboard UI components."""

from google.api_core.exceptions import GoogleAPIError
from pandas import DataFrame
import plotly.graph_objects as go
from dash import dash_table, dcc, html

from src.dashboard.bigquery_client import fetch_table_list, fetch_table_usage_stats

# Dashboard title constant
TITLE: str = "BigQueryテーブル利用状況"


def build_layout(project_id: str | None = None, region: str = "region-us") -> html.Div:
    """ダッシュボードレイアウトを構築する。

    テーブル一覧取得、利用統計取得、データ結合、DataTable生成の一連の処理を実行する。
    GoogleAPIError発生時はエラーメッセージを表示する。

    Args:
        project_id: GCPプロジェクトID。Noneの場合はテーブル表示をスキップ。
        region: BigQueryリージョン（INFORMATION_SCHEMAクエリ用）。デフォルトはregion-us。

    Returns:
        ダッシュボードのルートDivコンポーネント。
        エラー発生時はエラーメッセージを含むDivを返却。
    """
    children: list[html.H1 | html.P | dcc.Graph | dash_table.DataTable] = [
        html.H1(children=TITLE)
    ]

    if project_id is not None:
        try:
            # テーブル一覧を取得
            tables_df = fetch_table_list(project_id)

            if tables_df.empty:
                children.append(html.P("テーブルが存在しません"))
            else:
                # 利用統計を取得
                usage_df = fetch_table_usage_stats(project_id, region=region)

                # データを結合
                merged_df = merge_table_data(tables_df, usage_df)

                # DataTableを生成して追加
                datatable = create_usage_datatable(merged_df)
                children.append(datatable)

        except GoogleAPIError as e:
            children.append(html.P(f"BigQuery APIエラー: {e}"))

    return html.Div(children=children)


def merge_table_data(tables_df: DataFrame, usage_df: DataFrame) -> DataFrame:
    """テーブル一覧と利用統計を結合する。

    テーブル一覧DataFrame（dataset_id, table_id）を左側基準としてLEFT JOINを行い、
    利用実績がないテーブルはreference_count=0、unique_users=0で補完する。

    Args:
        tables_df: テーブル一覧DataFrame（dataset_id, table_id）
        usage_df: 利用統計DataFrame（dataset_id, table_id, reference_count, unique_users）

    Returns:
        結合済みDataFrame。
        カラム: dataset_id (str), table_id (str),
               reference_count (int), unique_users (int)
        利用実績がないテーブルはreference_count=0、unique_users=0
    """
    # LEFT JOINでテーブル一覧を基準に結合
    merged = tables_df.merge(usage_df, on=["dataset_id", "table_id"], how="left")

    # 欠損値を0で補完
    merged["reference_count"] = merged["reference_count"].fillna(0).astype(int)
    merged["unique_users"] = merged["unique_users"].fillna(0).astype(int)

    return merged


def create_table_figure(df: DataFrame) -> go.Figure:
    """DataFrameからPlotlyテーブルFigureを生成する。

    Args:
        df: dataset_id, table_idカラムを含むDataFrame

    Returns:
        Plotly Figureオブジェクト
    """
    columns: list[str] = list(df.columns)
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=columns,
                    fill_color="paleturquoise",
                    align="left",
                ),
                cells=dict(
                    values=[df[col].tolist() for col in columns],
                    fill_color="lavender",
                    align="left",
                ),
            )
        ]
    )
    return fig


def create_usage_datatable(df: DataFrame) -> dash_table.DataTable:
    """利用統計DataFrameからDataTableコンポーネントを生成する。

    DataFrameからDash DataTableを生成し、ネイティブソート機能を有効化。
    参照回数0件の行には条件付きスタイルで薄い赤の背景色を適用する。

    Args:
        df: 結合済み利用統計DataFrame
           （dataset_id, table_id, reference_count, unique_users）

    Returns:
        ソート可能、条件付きスタイル適用済みのDataTableコンポーネント
    """
    return dash_table.DataTable(
        id="usage-table",
        columns=[
            {"name": "データセットID", "id": "dataset_id"},
            {"name": "テーブルID", "id": "table_id"},
            {"name": "参照回数", "id": "reference_count"},
            {"name": "参照ユーザー数", "id": "unique_users"},
        ],
        data=df.to_dict("records"),
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
