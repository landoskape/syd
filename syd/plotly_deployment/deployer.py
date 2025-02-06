from typing import Any, Dict, List, Optional, Literal
import uuid
import warnings
from dataclasses import dataclass
from functools import wraps
from time import time
from contextlib import contextmanager
import socket

from dash import Dash, html, Input, Output, callback, dcc, ALL, callback_context
import plotly.graph_objects as go
from plotly.tools import mpl_to_plotly
import matplotlib as mpl
from matplotlib import pyplot as plt
from flask import Flask


from ..parameters import ButtonAction, ParameterUpdateWarning
from ..viewer import Viewer
from .components import BaseComponent, create_component


def debounce(wait_time):
    """
    Decorator to prevent a function from being called more than once every wait_time seconds.
    """

    def decorator(fn):
        last_called = [0.0]  # Using list to maintain state in closure

        @wraps(fn)
        def debounced(*args, **kwargs):
            current_time = time()
            if current_time - last_called[0] >= wait_time:
                fn(*args, **kwargs)
                last_called[0] = current_time

        return debounced

    return decorator


@dataclass
class LayoutConfig:
    """Configuration for the viewer layout."""

    controls_position: str = "left"  # Options are: 'left', 'top', 'right', 'bottom'
    controls_width_percent: int = 30

    def __post_init__(self):
        valid_positions = ["left", "top", "right", "bottom"]
        if self.controls_position not in valid_positions:
            raise ValueError(
                f"Invalid controls position: {self.controls_position}. Must be one of {valid_positions}"
            )

    @property
    def is_horizontal(self) -> bool:
        return self.controls_position in ["left", "right"]


@contextmanager
def _plot_context():
    """Context manager to temporarily switch matplotlib backend."""
    original_backend = mpl.get_backend()
    plt.switch_backend("Agg")  # Switch to non-interactive backend
    try:
        yield
    finally:
        plt.switch_backend(original_backend)


class PlotlyDeployer:
    """
    A deployment system for Viewer using Plotly/Dash.
    Built around the parameter component system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        controls_width_percent: int = 30,
        component_width: str = "300px",
        component_margin: str = "10px",
        label_width: str = "150px",
        continuous: bool = False,
        suppress_warnings: bool = False,
        title: str = "Syd Plotly App",
        server: Optional[Flask] = None,
    ):
        """
        Initialize the Plotly deployer.

        Args:
            viewer: The viewer instance to deploy
            controls_position: Position of controls ('left', 'top', 'right', 'bottom')
            controls_width_percent: Width of controls as percentage when horizontal
            component_width: Default width for components
            component_margin: Default margin for components
            label_width: Default width for labels
            continuous: Whether to update continuously during user interaction
            suppress_warnings: Whether to suppress parameter update warnings
            title: Title of the Dash application
            server: Optional Flask server to use
        """
        self.viewer = viewer
        self.config = LayoutConfig(
            controls_position=controls_position,
            controls_width_percent=controls_width_percent,
        )
        self.continuous = continuous
        self.suppress_warnings = suppress_warnings

        # Initialize Dash app
        self.app = Dash(__name__, server=server or True, title=title)

        # Component styling
        self._component_width = component_width
        self._component_margin = component_margin
        self._label_width = label_width

        # Initialize containers
        self._components: Dict[str, BaseComponent] = {}
        self._layout_ready = False
        self._callback_registered = False
        self._updating = False  # Flag to prevent circular updates

    def _create_parameter_components(self) -> None:
        """Create component instances for all parameters."""
        for name, param in self.viewer.parameters.items():
            component_id = f"{name}-{str(uuid.uuid4())[:8]}"
            component = create_component(
                param,
                component_id,
                width=self._component_width,
                margin=self._component_margin,
                label_width=self._label_width,
            )
            self._components[name] = component

    @debounce(0.2)
    def _handle_parameter_update(self, name: str, value: Any) -> None:
        """Handle updates to parameter values."""
        if self._updating:
            print(
                "Already updating -- there's a circular dependency! "
                "This is probably caused by failing to disable callbacks for a parameter. "
                "It's a bug --- tell the developer on github issues please."
            )
            return

        try:
            self._updating = True

            # Optionally suppress warnings during parameter updates
            with warnings.catch_warnings():
                if self.suppress_warnings:
                    warnings.filterwarnings("ignore", category=ParameterUpdateWarning)

                component = self._components[name]
                if component._is_action:
                    parameter = self.viewer.parameters[name]
                    parameter.callback(self.viewer.state)
                else:
                    self.viewer.set_parameter_value(name, value)

                # Update any components that changed due to dependencies
                self._sync_components_with_state(exclude=name)

        finally:
            self._updating = False

    def _sync_components_with_state(self, exclude: Optional[str] = None) -> None:
        """Sync component values with viewer state."""
        for name, parameter in self.viewer.parameters.items():
            if name == exclude:
                continue

            component = self._components[name]
            if not component.matches_parameter(parameter):
                component.update_from_parameter(parameter)

    def create_layout(self) -> html.Div:
        """Create the layout for the Dash application."""
        # Create parameter controls section
        param_components = [comp.component for comp in self._components.values()]
        controls = html.Div(
            [html.H3("Parameters", style={"marginBottom": "10px"})] + param_components,
            style={
                "width": (
                    f"{self.config.controls_width_percent}%"
                    if self.config.is_horizontal
                    else "100%"
                ),
                "padding": "20px",
                "borderRight": (
                    "1px solid #e5e7eb"
                    if self.config.controls_position == "left"
                    else None
                ),
                "borderLeft": (
                    "1px solid #e5e7eb"
                    if self.config.controls_position == "right"
                    else None
                ),
            },
        )

        # Create plot container
        plot_container = html.Div(
            id="plot-container",
            style={
                "width": (
                    f"{100 - self.config.controls_width_percent}%"
                    if self.config.is_horizontal
                    else "100%"
                ),
                "padding": "20px",
            },
        )

        # Add hidden div for state synchronization
        state_sync = html.Div(
            id={"type": "state_sync", "id": "sync"}, style={"display": "none"}
        )

        # Create final layout based on configuration
        if self.config.controls_position == "left":
            container = html.Div(
                [controls, plot_container, state_sync], style={"display": "flex"}
            )
        elif self.config.controls_position == "right":
            container = html.Div(
                [plot_container, controls, state_sync], style={"display": "flex"}
            )
        elif self.config.controls_position == "top":
            container = html.Div([controls, plot_container, state_sync])
        else:  # bottom
            container = html.Div([plot_container, controls, state_sync])

        return html.Div(
            container,
            style={
                "maxWidth": "1200px",
                "margin": "auto",
                "fontFamily": "sans-serif",
            },
        )

    def setup_callbacks(self) -> None:
        """Set up callbacks for all components."""
        if self._callback_registered:
            return

        # Create callback for each parameter
        for name, component in self._components.items():
            parameter = self.viewer.parameters[name]

            if not isinstance(parameter, ButtonAction):

                @callback(
                    Output(component.id, "value"),
                    [
                        Input(component.id, "value"),
                        Input({"type": "state_sync", "id": ALL}, "data"),
                    ],
                    prevent_initial_call=True,
                )
                def update_parameter(value: Any, sync_data: List[Dict], n=name) -> Any:
                    # If this is a state sync update, get the new value from viewer
                    triggered = [p["prop_id"] for p in callback_context.triggered]
                    if any(p.startswith("{") for p in triggered):
                        return self.viewer.parameters[n].value

                    # Otherwise handle parameter update normally
                    self._handle_parameter_update(n, value)
                    return value

            else:

                @callback(
                    Output(component.id, "n_clicks"),
                    Input(component.id, "n_clicks"),
                    prevent_initial_call=True,
                )
                def handle_click(n_clicks: int, n=name) -> int:
                    if n_clicks is not None and n_clicks > 0:
                        self._handle_parameter_update(n, None)
                    return 0  # Reset clicks

        # Create callback for plot updates
        @callback(
            [
                Output("plot-container", "children"),
                Output({"type": "state_sync", "id": "sync"}, "data"),
            ],
            [Input(comp.id, "value") for comp in self._components.values()],
        )
        def update_plot(*values):
            with _plot_context():
                fig = self.viewer.plot(self.viewer.state)

                # If it's already a Plotly figure, use it directly
                if isinstance(fig, (go.Figure, dict)):
                    plotly_fig = fig
                else:
                    # Convert matplotlib figure to plotly
                    plotly_fig = mpl_to_plotly(fig)
                    plt.close(fig)  # Clean up the matplotlib figure

            return dcc.Graph(figure=plotly_fig), {"timestamp": time()}

        self._callback_registered = True

    def find_available_port(self, start_port=8050, max_attempts=100):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("", port))
                    return port
                except socket.error:
                    continue
        raise RuntimeError(
            f"No available ports found between {start_port} and {start_port + max_attempts}"
        )

    def deploy(
        self,
        mode: Literal["notebook", "server"] = "notebook",
        host: str = "127.0.0.1",
        port: int = 8050,
        debug: bool = False,
        max_port_attempts: int = 100,
    ) -> None:
        """
        Deploy the Dash application.

        Args:
            mode: How to deploy the app - 'notebook' for Jupyter integration or 'server' for standalone web server
            host: Host address to run the server on (only used in server mode)
            port: Starting port to try running the server on (only used in server mode)
            debug: Whether to run in debug mode
            max_port_attempts: Maximum number of ports to try if initial port is taken
        """
        with self.viewer._deploy_app():
            # Create components
            self._create_parameter_components()

            # Set up layout
            if not self._layout_ready:
                self.app.layout = self.create_layout()
                self._layout_ready = True

            # Set up callbacks
            if not self._callback_registered:
                self.setup_callbacks()

            # Find available port if in server mode
            if mode == "server":
                port = self.find_available_port(
                    start_port=port, max_attempts=max_port_attempts
                )

            # Handle warnings based on debug mode
            with warnings.catch_warnings():
                if not debug:
                    warnings.filterwarnings("ignore", category=UserWarning)

                if mode == "notebook":
                    # Configure JupyterDash for notebook display
                    self.app.run_server(mode="inline", port=port, debug=debug)
                else:  # server mode
                    # Run as a standalone server
                    self.app.run(jupyter_mode="tab", host=host, port=port, debug=debug)
