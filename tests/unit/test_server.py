"""Tests for ServerRunner module."""

from unittest.mock import MagicMock
from dash import Dash


class TestRunServer:
    """Tests for run_server function."""

    def test_run_server_calls_app_run(self) -> None:
        """Verify run_server calls app.run with correct parameters."""
        from src.dashboard.server import run_server

        mock_app = MagicMock(spec=Dash)

        run_server(mock_app, host="127.0.0.1", port=8050, debug=True)

        mock_app.run.assert_called_once_with(
            host="127.0.0.1",
            port="8050",
            debug=True,
        )
