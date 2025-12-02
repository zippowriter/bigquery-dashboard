"""Dash application creation module."""

from dash import Dash

from src.dashboard.config import AppConfig
from src.dashboard.layout import build_layout


def create_app(config: AppConfig) -> Dash:
    """Create and initialize a Dash application instance.

    Args:
        config: Application configuration with title, host, port, and debug settings.

    Returns:
        Initialized Dash instance with layout configured.

    Raises:
        ValueError: If config is not an AppConfig instance.
    """
    if not isinstance(config, AppConfig):
        raise ValueError(
            f"config must be an AppConfig instance, got {type(config).__name__}"
        )

    app = Dash(__name__)
    app.title = config.title
    app.layout = build_layout()

    return app
