"""Tests for LayoutBuilder module."""

from dash import html


class TestLayoutBuilder:
    """Tests for layout construction functions."""

    def test_build_layout_returns_div(self) -> None:
        """Verify build_layout returns html.Div component."""
        from src.dashboard.layout import build_layout

        layout = build_layout()
        assert isinstance(layout, html.Div)
