"""レイアウト構築モジュール。

ダッシュボードのメインレイアウトを構築するオーケストレーション層。
"""

from dash import html
from google.api_core.exceptions import GoogleAPIError

from src.dashboard.domain.repositories import TableRepository
from src.dashboard.domain.services import TableUsageService
from src.dashboard.infra.bigquery import BigQueryTableRepository
from src.dashboard.presentation.components import create_error_message, create_usage_datatable

# ダッシュボードタイトル定数
TITLE: str = "BigQueryテーブル利用状況"


def build_layout(
    project_id: str | None = None,
    region: str = "region-us",
    repository: TableRepository | None = None,
) -> html.Div:
    """ダッシュボードレイアウトを構築する。

    テーブル一覧取得、利用統計取得、データ結合、DataTable生成の一連の処理を実行する。
    GoogleAPIError発生時はエラーメッセージを表示する。

    Args:
        project_id: GCPプロジェクトID。Noneの場合はテーブル表示をスキップ。
        region: BigQueryリージョン（INFORMATION_SCHEMAクエリ用）。デフォルトはregion-us。
        repository: テーブルリポジトリ。Noneの場合はBigQueryTableRepositoryを使用。

    Returns:
        ダッシュボードのルートDivコンポーネント。
        エラー発生時はエラーメッセージを含むDivを返却。
    """
    children: list[html.H1 | html.P] = [html.H1(children=TITLE)]

    if project_id is None:
        return html.Div(children=children)

    # リポジトリのデフォルト実装を設定
    if repository is None:
        repository = BigQueryTableRepository()

    try:
        # テーブル一覧を取得
        tables = repository.fetch_tables(project_id)

        if not tables:
            children.append(html.P("テーブルが存在しません"))
        else:
            # 利用統計を取得
            usage_stats = repository.fetch_usage_stats(project_id, region)

            # ドメインサービスでデータを結合
            merged = TableUsageService.merge_usage_data(tables, usage_stats)

            # DataTableを生成して追加
            datatable = create_usage_datatable(merged)
            children.append(datatable)  # pyright: ignore[reportArgumentType]

    except GoogleAPIError as e:
        children.append(create_error_message(f"BigQuery APIエラー: {e}"))

    return html.Div(children=children)
