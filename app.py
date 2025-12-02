"""Main entry point for the Dash dashboard application."""

from src.dashboard.app import create_app
from src.dashboard.config import AppConfig
from src.dashboard.server import run_server


def main() -> None:
    """Initialize and run the Dash dashboard application.

    Creates the application with default configuration and starts
    the development server on localhost.
    """
    config = AppConfig()
    app = create_app(config)
    run_server(
        app,
        host=config.host,
        port=config.port,
        debug=config.debug,
    )


if __name__ == "__main__":
    main()
