"""Tests for main entry point module."""

from unittest.mock import MagicMock, patch


class TestMainModule:
    """Tests for main module entry point."""

    @patch("app.run_server")
    @patch("app.create_app")
    def test_main_creates_app(
        self, mock_create_app: MagicMock, mock_run_server: MagicMock
    ) -> None:
        """Verify main creates the Dash application."""
        from app import main
        from src.dashboard.config import AppConfig

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        main()

        # Verify create_app was called with AppConfig
        mock_create_app.assert_called_once()
        call_args = mock_create_app.call_args[0]
        assert isinstance(call_args[0], AppConfig)
