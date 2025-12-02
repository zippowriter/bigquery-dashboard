"""Server runner module for Dash application."""

from dash import Dash


def run_server(
    app: Dash,
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = True,
) -> None:
    """Start the Dash server.

    Args:
        app: Dash application instance.
        host: Host address to bind (default: 127.0.0.1).
        port: Port number to listen on (default: 8050).
        debug: Enable debug mode with hot reload (default: True).

    Note:
        This function is blocking. It will not return until
        the server is stopped (e.g., with Ctrl+C).
    """
    print(f"Starting Dash server at http://{host}:{port}/")
    print(f"Debug mode: {'enabled' if debug else 'disabled'}")

    app.run(
        host=host,
        port=str(port),
        debug=debug,
    )
