"""Dash application creation module."""

from dash import Dash

from src.dashboard.config import AppConfig
from src.dashboard.layout import build_layout


def create_app(config: AppConfig) -> Dash:
    """Dashアプリケーションインスタンスを作成・初期化する。

    Args:
        config: タイトル、ホスト、ポート、デバッグ設定、プロジェクトID、リージョンを含むアプリケーション設定。

    Returns:
        レイアウト設定済みのDashインスタンス。
    """

    app = Dash(__name__)
    app.title = config.title
    app.layout = build_layout(project_id=config.project_id, region=config.region)

    return app
