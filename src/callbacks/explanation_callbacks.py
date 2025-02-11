# callbacks/explanation_callbacks.py

from dash import html, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Import any necessary functions
from py_arg_visualisation.functions.import_functions.read_argumentation_framework_functions import (
    read_argumentation_framework,
)
from py_arg_visualisation.functions.graph_data_functions.get_af_dot_string import (
    get_numbered_grounded_extension,
)


# -- Callback for generating explanations --
@callback(
    Output("21-abstract-evaluation-all-args", "children"),
    State("abstract-arguments", "value"),
    State("abstract-attacks", "value"),
    Input("abstract-evaluation-accordion", "active_item"),
    Input("selected-argument-store-abstract", "data"),
    prevent_initial_call=True,
)
def generate_explanations(arguments, attacks, active_item, selected_extension):
    if active_item != "Explanation":
        raise PreventUpdate

    # Read the argumentation framework and compute grounded status.
    arg_framework = read_argumentation_framework(arguments, attacks)
    gr_status_by_arg, number_by_argument = get_numbered_grounded_extension(
        arg_framework
    )

    def determine_hex_color(arg):
        """Return the hex color code based on the argument's status and extension membership."""
        status = gr_status_by_arg.get(arg)
        if status == "undefined":
            if arg in selected_extension.get("green", []):
                return "#a6e9ff"  # light-green
            elif arg in selected_extension.get("red", []):
                return "#ffe6c9"  # light-red
            elif arg in selected_extension.get("yellow", []):
                return "#FEFE62"  # yellow for undefined
            else:
                return "#cccccc"  # fallback color
        else:
            if arg in selected_extension.get("green", []):
                return "#40cfff"  # green
            elif arg in selected_extension.get("yellow", []):
                return "#FEFE62"  # yellow
            elif arg in selected_extension.get("red", []):
                return "#ffb763"  # red
            else:
                return "#cccccc"  # fallback color

    # Create a button for each argument with colored background and hover border effect
    all_argument_buttons = [
        dbc.Button(
            arg,
            id={"type": "argument-button-abstract", "index": arg},
            className="hover-button",  # Custom class for hover effect
            style={
                "margin": "5px",
                "backgroundColor": determine_hex_color(arg),  # Set background color
                "border": f"4px solid {determine_hex_color(arg)}",  # Border matches color
                "color": "black",  # Text color
            },
        )
        for arg in sorted(arguments.split("\n"))
    ]

    # Build and return the complete Div.
    arguments_div = html.Div(
        [
            html.B("Argument Provenance:"),
            html.Br(),
            html.I("Click on an argument to display it in the graph."),
            html.Div(all_argument_buttons),
        ]
    )
    return arguments_div
