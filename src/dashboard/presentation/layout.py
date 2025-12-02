"""レイアウト構築モジュール。

ダッシュボードのメインレイアウトを構築するオーケストレーション層。
"""

from typing import Any

from dash import dcc, html
from google.api_core.exceptions import GoogleAPIError

from src.dashboard.domain.logging import Logger
from src.dashboard.domain.models import TableUsage
from src.dashboard.domain.repositories import TableRepository
from src.dashboard.domain.services import TableUsageService
from src.dashboard.infra.bigquery import BigQueryTableRepository
from src.dashboard.infra.lineage import LineageRepository, LineageRepositoryProtocol
from src.dashboard.logging_config import get_logger
from src.dashboard.presentation.components import create_error_message, create_usage_datatable

# ダッシュボードタイトル定数
TITLE: str = "BigQueryテーブル利用状況"


def build_layout(
    project_id: str | None = None,
    region: str = "region-us",
    repository: TableRepository | None = None,
    lineage_repository: LineageRepositoryProtocol | None = None,
    logger: Logger | None = None,
) -> html.Div:
    """ダッシュボードレイアウトを構築する。

    テーブル一覧取得、利用統計取得、データ結合、DataTable生成の一連の処理を実行する。
    GoogleAPIError発生時はエラーメッセージを表示する。

    Args:
        project_id: GCPプロジェクトID。Noneの場合はテーブル表示をスキップ。
        region: BigQueryリージョン（INFORMATION_SCHEMAクエリ用）。デフォルトはregion-us。
        repository: テーブルリポジトリ。Noneの場合はBigQueryTableRepositoryを使用。
        lineage_repository: リネージリポジトリ。Noneの場合はLineageRepositoryを使用。
        logger: ロガーインスタンス（省略時はデフォルトロガーを使用）

    Returns:
        ダッシュボードのルートDivコンポーネント。
        エラー発生時はエラーメッセージを含むDivを返却。
    """
    _logger = logger or get_logger()
    _logger.info("レイアウト構築開始", project_id=project_id, region=region)

    # 設定情報をStoreに保存（コールバックで使用）
    config_store = dcc.Store(
        id="app-config",
        data={"project_id": project_id, "region": region},
    )

    # 更新ボタン
    refresh_button = html.Button(
        "データを更新",
        id="refresh-button",
        n_clicks=0,
        style={
            "marginBottom": "10px",
            "padding": "8px 16px",
            "cursor": "pointer",
        },
    )

    children: list[Any] = [
        html.H1(children=TITLE),
        config_store,
        refresh_button,
    ]

    if project_id is None:
        _logger.debug("project_id未設定、データ表示をスキップ")
        return html.Div(children=children)

    # リポジトリのデフォルト実装を設定
    if repository is None:
        repository = BigQueryTableRepository()

    # データコンテナを追加（コールバックで更新される）
    data_content = build_data_content(project_id, region, repository, lineage_repository, _logger)
    children.append(html.Div(id="data-container", children=data_content))

    _logger.info("レイアウト構築完了")
    return html.Div(children=children)


def build_data_content(
    project_id: str,
    region: str,
    repository: TableRepository,
    lineage_repository: LineageRepositoryProtocol | None = None,
    logger: Logger | None = None,
) -> Any:
    """データコンテンツを構築する。

    Args:
        project_id: GCPプロジェクトID
        region: BigQueryリージョン
        repository: テーブルリポジトリ
        lineage_repository: リネージリポジトリ。Noneの場合はLineageRepositoryを使用。
        logger: ロガーインスタンス（省略時はデフォルトロガーを使用）

    Returns:
        DataTableまたはエラーメッセージを含むコンポーネント
    """
    _logger = logger or get_logger()
    _logger.debug("データコンテンツ構築開始")

    try:
        # テーブル一覧を取得
        tables = repository.fetch_tables(project_id)
        _logger.debug("テーブル取得完了", count=len(tables))

        if not tables:
            _logger.info("テーブルが存在しません")
            return html.P("テーブルが存在しません")

        # 利用統計を取得
        usage_stats = repository.fetch_usage_stats(project_id, region)
        _logger.debug("利用統計取得完了", count=len(usage_stats))

        # ドメインサービスでデータを結合
        merged = TableUsageService.merge_usage_data(tables, usage_stats)

        # リネージ情報を取得・結合
        if lineage_repository is None:
            lineage_repository = LineageRepository()

        table_fqns = [
            f"bigquery:{project_id}.{u.dataset_id}.{u.table_id}" for u in merged
        ]

        # Lineage APIのロケーションはregionから変換（region-us -> us）
        lineage_location = (
            region.replace("region-", "") if region.startswith("region-") else region
        )

        leaf_fqns = lineage_repository.get_leaf_tables(
            project_id=project_id,
            location=lineage_location,
            table_fqns=table_fqns,
        )

        merged_with_leaf = TableUsageService.merge_with_leaf_info(
            merged, leaf_fqns, project_id
        )

        _logger.debug("データコンテンツ構築完了", table_count=len(merged_with_leaf))
        # DataTableを生成して返却
        return create_usage_datatable(merged_with_leaf)

    except GoogleAPIError as e:
        _logger.error("BigQuery APIエラー", error=str(e))
        return create_error_message(f"BigQuery APIエラー: {e}")


def build_data_content_from_data(
    tables_data: list[TableUsage],
) -> Any:
    """取得済みデータからデータコンテンツを構築する。

    Args:
        tables_data: 結合済みのテーブル利用統計リスト

    Returns:
        DataTableコンポーネント
    """
    if not tables_data:
        return html.P("テーブルが存在しません")
    return create_usage_datatable(tables_data)
