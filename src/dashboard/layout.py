"""Layout builder module for dashboard UI components."""

from dash import html

# Dashboard title constant
TITLE: str = "BigQueryテーブル利用状況"


def build_layout() -> html.Div:
    """Build the basic dashboard layout.

    Constructs the root layout with title and header components.

    Returns:
        Root Div component containing title and header.
    """
    return html.Div(
        children=[
            html.H1(children=TITLE),
        ]
    )
