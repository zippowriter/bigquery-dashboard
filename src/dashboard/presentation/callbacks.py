"""コールバック定義モジュール。

Dashアプリケーションのコールバックを定義する。
"""

from typing import Any

from dash import Input, Output, State, callback, html  # pyright: ignore[reportUnknownVariableType]
from google.api_core.exceptions import GoogleAPIError

from src.dashboard.domain.services import TableUsageService
from src.dashboard.infra.cached_repository import CachedTableRepository
from src.dashboard.presentation.components import create_error_message, create_usage_datatable

# モジュールレベルでリポジトリを保持（コールバックからアクセス）
_repository: CachedTableRepository | None = None


def register_callbacks(repository: CachedTableRepository) -> None:
    """コールバックを登録する。

    Args:
        repository: キャッシュ付きテーブルリポジトリ
    """
    global _repository
    _repository = repository

    @callback(
        Output("data-container", "children"),
        Input("refresh-button", "n_clicks"),
        State("app-config", "data"),
        prevent_initial_call=True,
    )
    def refresh_data(n_clicks: int, config: dict[str, Any] | None) -> Any:
        """データを更新するコールバック。

        更新ボタンがクリックされたときにBigQuery APIからデータを再取得し、
        CSVキャッシュを更新する。

        Args:
            n_clicks: ボタンのクリック回数
            config: アプリケーション設定（project_id, region）

        Returns:
            更新されたデータコンテナの内容
        """
        if _repository is None:
            return create_error_message("リポジトリが初期化されていません")

        if config is None:
            return create_error_message("設定が読み込めませんでした")

        project_id = config.get("project_id")
        region = config.get("region", "region-us")

        if project_id is None:
            return create_error_message("project_idが設定されていません")

        try:
            # BigQueryからデータを再取得してキャッシュを更新
            tables, usage_stats = _repository.refresh(project_id, region)

            if not tables:
                return html.P("テーブルが存在しません")

            # ドメインサービスでデータを結合
            merged = TableUsageService.merge_usage_data(tables, usage_stats)

            # DataTableを生成して返却
            return create_usage_datatable(merged)

        except GoogleAPIError as e:
            return create_error_message(f"BigQuery APIエラー: {e}")
        except Exception as e:
            return create_error_message(f"予期しないエラー: {e}")
