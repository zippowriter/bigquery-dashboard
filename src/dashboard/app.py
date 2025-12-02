"""Dash application creation module."""

from dash import Dash

from src.dashboard.config import AppConfig
from src.dashboard.infra.cached_repository import CachedTableRepository
from src.dashboard.presentation.callbacks import register_callbacks
from src.dashboard.presentation.layout import build_layout


def create_app(config: AppConfig) -> Dash:
    """Dashアプリケーションインスタンスを作成・初期化する。

    CSVキャッシュ付きリポジトリを使用し、キャッシュが存在する場合は
    即座にデータを表示する。更新ボタンでBigQueryからデータを再取得できる。

    Args:
        config: タイトル、ホスト、ポート、デバッグ設定、プロジェクトID、リージョンを含むアプリケーション設定。

    Returns:
        レイアウト設定済みのDashインスタンス。
    """
    # キャッシュ付きリポジトリを初期化
    repository = CachedTableRepository()

    app = Dash(__name__)
    app.title = config.title
    app.layout = build_layout(
        project_id=config.project_id,
        region=config.region,
        repository=repository,
    )

    # コールバックを登録
    register_callbacks(repository)

    return app
