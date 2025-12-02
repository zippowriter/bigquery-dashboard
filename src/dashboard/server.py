"""Server runner module for Dash application."""

from dash import Dash

from src.dashboard.domain.logging import Logger
from src.dashboard.logging_config import get_logger


def run_server(
    app: Dash,
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = True,
    logger: Logger | None = None,
) -> None:
    """Start the Dash server.

    Args:
        app: Dash application instance.
        host: Host address to bind (default: 127.0.0.1).
        port: Port number to listen on (default: 8050).
        debug: Enable debug mode with hot reload (default: True).
        logger: ロガーインスタンス（省略時はデフォルトロガーを使用）

    Note:
        This function is blocking. It will not return until
        the server is stopped (e.g., with Ctrl+C).
    """
    _logger = logger or get_logger()
    _logger.info("Dashサーバー起動", host=host, port=port, debug=debug)

    app.run(
        host=host,
        port=str(port),
        debug=debug,
    )
