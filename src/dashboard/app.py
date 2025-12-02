"""Dash application creation module."""

from dash import Dash

from src.dashboard.config import AppConfig
from src.dashboard.layout import build_layout


def create_app(config: AppConfig) -> Dash:
    """Dashアプリケーションインスタンスを作成・初期化する。

    Args:
        config: タイトル、ホスト、ポート、デバッグ設定、プロジェクトIDを含むアプリケーション設定。

    Returns:
        レイアウト設定済みのDashインスタンス。

    Raises:
        ValueError: configがAppConfigインスタンスでない場合。
    """
    if not isinstance(config, AppConfig):
        raise ValueError(
            f"config must be an AppConfig instance, got {type(config).__name__}"
        )

    app = Dash(__name__)
    app.title = config.title
    app.layout = build_layout(project_id=config.project_id)

    return app
