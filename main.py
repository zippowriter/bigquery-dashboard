import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from dash import (
    Dash,
    Input,
    Output,
    callback,  # type: ignore[reportUnknownVariableType]
    dash_table,
    dcc,
    html,
)


# Incorporate data
df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv"
)

# Initialize the app - incorporate a Dash Bootstrap theme
external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# App layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.Div(
                    children="My First App with Data, Graph, and Controls",
                    className="text-primary text-center fs-3",
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.RadioItems(
                    options=[
                        {"label": x, "value": x}
                        for x in ["pop", "lifeExp", "gdpPercap"]
                    ],
                    value="lifeExp",
                    inline=True,
                    id="radio-buttons-final",
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            data=df.to_dict("records"),
                            page_size=12,
                            style_table={"overflowX": "auto"},
                        )
                    ],
                    width=6,
                ),
                dbc.Col(
                    [dcc.Graph(figure={}, id="histo-chart-final")],
                    width=6,
                ),
            ],
        ),
    ],
    fluid=True,
)


# Add controls to build the interactivity
@callback(
    Output("histo-chart-final", "figure"),
    Input("radio-buttons-final", "value"),
)
def update_graph(col_chosen):
    return px.histogram(df, x="continent", y=col_chosen, histfunc="avg")


if __name__ == "__main__":
    app.run(debug=True)
