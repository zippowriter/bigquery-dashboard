"""Layout builder module for dashboard UI components."""

from google.api_core.exceptions import GoogleAPIError
from pandas import DataFrame
import plotly.graph_objects as go
from dash import dcc, html

from src.dashboard.bigquery_client import fetch_table_list

# Dashboard title constant
TITLE: str = "BigQueryテーブル利用状況"


def build_layout(project_id: str | None = None) -> html.Div:
    """ダッシュボードレイアウトを構築する。

    Args:
        project_id: GCPプロジェクトID。Noneの場合はテーブル表示をスキップ。

    Returns:
        ダッシュボードのルートDivコンポーネント。
    """
    children: list[html.H1 | html.P | dcc.Graph] = [html.H1(children=TITLE)]

    if project_id is not None:
        try:
            df = fetch_table_list(project_id)

            if df.empty:
                children.append(html.P("テーブルが存在しません"))
            else:
                fig = create_table_figure(df)
                children.append(dcc.Graph(figure=fig))

        except GoogleAPIError as e:
            children.append(html.P(f"BigQuery APIエラー: {e}"))

    return html.Div(children=children)


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
