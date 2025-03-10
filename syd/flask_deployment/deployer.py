"""
Flask deployer for Syd Viewer objects.

This module provides tools to deploy Syd viewers as Flask web applications.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union, Callable, Type
from dataclasses import dataclass
from contextlib import contextmanager
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import numpy as np
import time
from functools import wraps
import webbrowser
import threading
import socket


from flask import (
    Flask,
    send_file,
    request,
    make_response,
    jsonify,
    render_template,
    url_for,
)
from werkzeug.serving import run_simple

from ..viewer import Viewer
from ..parameters import (
    Parameter,
    TextParameter,
    BooleanParameter,
    SelectionParameter,
    MultipleSelectionParameter,
    IntegerParameter,
    FloatParameter,
    IntegerRangeParameter,
    FloatRangeParameter,
    UnboundedIntegerParameter,
    UnboundedFloatParameter,
    ButtonAction,
    ParameterType,
    ActionType,
)

mpl.use("Agg")


def debounce(wait_time=0.1):
    """
    Decorator to debounce function calls.
    Prevents a function from being called too frequently.
    """

    def decorator(fn):
        last_call_time = [0]

        @wraps(fn)
        def debounced(*args, **kwargs):
            current_time = time.time()
            if current_time - last_call_time[0] > wait_time:
                last_call_time[0] = current_time
                return fn(*args, **kwargs)
            return None

        return debounced

    return decorator


@dataclass
class FlaskLayoutConfig:
    """Configuration for the Flask viewer layout."""

    controls_position: str = "left"  # Options are: 'left', 'top', 'right', 'bottom'
    figure_width: float = 8.0
    figure_height: float = 6.0
    controls_width_percent: int = 30

    def __post_init__(self):
        valid_positions = ["left", "top", "right", "bottom"]
        if self.controls_position not in valid_positions:
            raise ValueError(
                f"Invalid controls position: {self.controls_position}. Must be one of {valid_positions}"
            )

    @property
    def is_horizontal(self) -> bool:
        return self.controls_position == "left" or self.controls_position == "right"


class FlaskDeployer:
    """
    A deployment system for Viewer as a Flask web application.
    Creates a Flask app with routes for the UI, data API, and plot generation.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        fig_dpi: int = 300,
        figure_width: float = 8.0,
        figure_height: float = 6.0,
        controls_width_percent: int = 30,
        static_folder: Optional[str] = None,
        template_folder: Optional[str] = None,
        debug: bool = False,
    ):
        """
        Initialize the Flask deployer.

        Parameters
        ----------
        viewer : Viewer
            The viewer to deploy
        controls_position : str, optional
            Position of the controls ('left', 'top', 'right', 'bottom')
        fig_dpi : int, optional
            DPI of the figure - higher is better quality but takes longer to generate
        figure_width : float, optional
            Width of the figure in inches
        figure_height : float, optional
            Height of the figure in inches
        controls_width_percent : int, optional
            Width of the controls as a percentage of the total width
        static_folder : str, optional
            Custom path to static files
        template_folder : str, optional
            Custom path to template files
        debug : bool, optional
            Whether to enable debug mode
        """
        self.viewer = viewer
        self.config = FlaskLayoutConfig(
            controls_position=controls_position,
            figure_width=figure_width,
            figure_height=figure_height,
            controls_width_percent=controls_width_percent,
        )
        self.fig_dpi = fig_dpi
        self.debug = debug

        # Use default folders if not specified
        package_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_folder = static_folder or os.path.join(package_dir, "static")
        self.template_folder = template_folder or os.path.join(package_dir, "templates")

        # State tracking
        self.in_callbacks = False

        # Create Flask app
        self.app = self.create_app()

    def create_app(self) -> Flask:
        """
        Create and configure the Flask application.

        Returns
        -------
        Flask
            The configured Flask application
        """
        app = Flask(
            __name__,
            static_folder=self.static_folder,
            template_folder=self.template_folder,
        )

        # Configure logging
        if not self.debug:
            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)

        # Define routes

        @app.route("/")
        def home():
            """Render the main page."""
            return render_template("index.html", config=self.config)

        @app.route("/init-data")
        def init_data():
            """Provide initial parameter information."""
            param_info = {}

            for name, param in self.viewer.parameters.items():
                param_info[name] = self._get_parameter_info(param)

            return jsonify({"params": param_info})

        @app.route("/plot")
        def plot():
            """Generate and return a plot based on the current state."""
            try:
                # Get parameters from request
                state = self._parse_request_args(request.args)

                # Update viewer state
                for name, value in state.items():
                    if name in self.viewer.parameters:
                        self.viewer.parameters[name].value = value

                # Get the plot from the viewer
                with _plot_context():
                    fig = self.viewer.plot(self.viewer.state)

                # Save the plot to a buffer
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=self.fig_dpi)
                buf.seek(0)
                plt.close(fig)

                # Return the image
                response = make_response(send_file(buf, mimetype="image/png"))
                response.headers["Cache-Control"] = "no-cache"
                return response

            except Exception as e:
                app.logger.error(f"Error: {str(e)}")
                return f"Error generating plot: {str(e)}", 500

        @app.route("/update-param", methods=["POST"])
        def update_param():
            """Update a parameter and run its callbacks."""
            try:
                data = request.get_json()
                name = data.get("name")
                value = data.get("value")
                is_action = data.get("action", False)

                if name not in self.viewer.parameters:
                    return jsonify({"error": f"Parameter {name} not found"}), 404

                # Handle the parameter update or action
                if is_action:
                    # For button actions, run the callback
                    self._handle_action(name)
                else:
                    # For normal parameters, update value and run callbacks
                    parsed_value = self._parse_parameter_value(name, value)
                    self._handle_parameter_update(name, parsed_value)

                # Return the updated state
                return jsonify({"success": True, "state": self.viewer.state})

            except Exception as e:
                app.logger.error(f"Error updating parameter: {str(e)}")
                return jsonify({"error": str(e)}), 500

        return app

    @debounce(0.1)
    def _handle_parameter_update(self, name: str, value: Any) -> None:
        """
        Handle a parameter update, including running callbacks.

        Parameters
        ----------
        name : str
            The name of the parameter to update
        value : Any
            The new value for the parameter
        """
        # Prevent recursive callback cycles
        if self.in_callbacks:
            return

        try:
            # Update the parameter value
            self.viewer.parameters[name].value = value

            # Run callbacks for this parameter
            self.in_callbacks = True

            # The viewer's perform_callbacks method will automatically
            # pass the state dictionary to the callbacks
            self.viewer.perform_callbacks(name)
        finally:
            self.in_callbacks = False

    def _handle_action(self, name: str) -> None:
        """
        Handle a button action by executing its callback.

        Parameters
        ----------
        name : str
            The name of the button parameter
        """
        # Prevent recursive callback cycles
        if self.in_callbacks:
            return

        try:
            # Execute the button callback
            param = self.viewer.parameters[name]
            if isinstance(param, ButtonAction) and param.callback:
                self.in_callbacks = True

                # Pass the current state to the callback
                param.callback(self.viewer.state)
        finally:
            self.in_callbacks = False

    def _get_parameter_info(self, param: Parameter) -> Dict[str, Any]:
        """
        Convert a Parameter object to a dictionary of information for the frontend.

        Parameters
        ----------
        param : Parameter
            The parameter to convert

        Returns
        -------
        Dict[str, Any]
            Parameter information for the frontend
        """
        if isinstance(param, TextParameter):
            return {"type": "text", "value": param.value}
        elif isinstance(param, BooleanParameter):
            return {"type": "boolean", "value": param.value}
        elif isinstance(param, SelectionParameter):
            return {"type": "selection", "value": param.value, "options": param.options}
        elif isinstance(param, MultipleSelectionParameter):
            return {
                "type": "multiple-selection",
                "value": param.value,
                "options": param.options,
            }
        elif isinstance(param, IntegerParameter):
            return {
                "type": "integer",
                "value": param.value,
                "name": param.name,
                "min": param.min,
                "max": param.max,
            }
        elif isinstance(param, FloatParameter):
            return {
                "type": "float",
                "value": param.value,
                "name": param.name,
                "min": param.min,
                "max": param.max,
                "step": param.step,
            }
        elif isinstance(param, IntegerRangeParameter):
            return {
                "type": "integer-range",
                "value": param.value,
                "name": param.name,
                "min": param.min,
                "max": param.max,
            }
        elif isinstance(param, FloatRangeParameter):
            return {
                "type": "float-range",
                "value": param.value,
                "name": param.name,
                "min": param.min,
                "max": param.max,
                "step": param.step,
            }
        elif isinstance(param, UnboundedIntegerParameter):
            return {"type": "unbounded-integer", "value": param.value}
        elif isinstance(param, UnboundedFloatParameter):
            return {"type": "unbounded-float", "value": param.value, "step": param.step}
        elif isinstance(param, ButtonAction):
            return {"type": "button", "label": param.label, "is_action": True}
        else:
            return {"type": "unknown", "value": str(param.value)}

    def _parse_request_args(self, args) -> Dict[str, Any]:
        """
        Parse request arguments into appropriate Python types based on parameter types.

        Parameters
        ----------
        args : MultiDict
            Request arguments

        Returns
        -------
        Dict[str, Any]
            Parsed parameters
        """
        result = {}

        for name, value in args.items():
            # Skip if parameter doesn't exist
            if name not in self.viewer.parameters:
                continue

            result[name] = self._parse_parameter_value(name, value)

        return result

    def _parse_parameter_value(self, name: str, value: Any) -> Any:
        """
        Parse a parameter value based on its type.

        Parameters
        ----------
        name : str
            Parameter name
        value : Any
            Raw value

        Returns
        -------
        Any
            Parsed value
        """
        param = self.viewer.parameters[name]

        if isinstance(param, TextParameter):
            return str(value)
        elif isinstance(param, BooleanParameter):
            return value.lower() == "true" if isinstance(value, str) else bool(value)
        elif isinstance(param, (IntegerParameter, UnboundedIntegerParameter)):
            return int(value)
        elif isinstance(param, (FloatParameter, UnboundedFloatParameter)):
            return float(value)
        elif isinstance(param, (IntegerRangeParameter, FloatRangeParameter)):
            # Parse JSON array for range parameters
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid range format: {value}")
            return value
        elif isinstance(param, MultipleSelectionParameter):
            # Parse JSON array for multiple selection
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return [value] if value else []
            return value
        else:
            return value

    def run(self, host: str = "127.0.0.1", port: Optional[int] = None, **kwargs):
        """
        Run the Flask application server.

        Parameters
        ----------
        host : str, optional
            Host to run the server on
        port : int, optional
            Port to run the server on. If None, an available port will be automatically found.
        **kwargs
            Additional arguments to pass to app.run()
        """
        # Find an available port if none is specified
        if port is None:
            port = _find_available_port()

        run_simple(host, port, self.app, use_reloader=self.debug, **kwargs)


def _find_available_port(start_port=5000, max_attempts=100):
    """
    Find an available port starting from start_port.

    Parameters
    ----------
    start_port : int, optional
        Port to start searching from
    max_attempts : int, optional
        Maximum number of ports to try

    Returns
    -------
    int
        An available port number

    Raises
    ------
    RuntimeError
        If no available port is found after max_attempts
    """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    raise RuntimeError(
        f"Could not find an available port after {max_attempts} attempts starting from {start_port}"
    )


@contextmanager
def _plot_context():
    """Context manager for creating matplotlib plots."""
    try:
        fig = plt.figure()
        yield fig
    finally:
        plt.close(fig)


def deploy_flask(
    viewer: Viewer,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    controls_position: str = "left",
    figure_width: float = 8.0,
    figure_height: float = 6.0,
    controls_width_percent: int = 30,
    debug: bool = False,
    open_browser: bool = True,
    **kwargs,
):
    """
    Deploy a Viewer as a Flask web application.

    Parameters
    ----------
    viewer : Viewer
        The viewer to deploy
    host : str, optional
        Host to run the server on
    port : int, optional
        Port to run the server on. If None, an available port will be automatically found.
    controls_position : str, optional
        Position of the controls ('left', 'top', 'right', 'bottom')
    figure_width : float, optional
        Width of the figure in inches
    figure_height : float, optional
        Height of the figure in inches
    controls_width_percent : int, optional
        Width of the controls as a percentage of the total width
    debug : bool, optional
        Whether to enable debug mode
    open_browser : bool, optional
        Whether to open the browser automatically
    **kwargs
        Additional arguments to pass to app.run()

    Returns
    -------
    FlaskDeployer
        The deployer instance
    """
    deployer = FlaskDeployer(
        viewer,
        controls_position=controls_position,
        figure_width=figure_width,
        figure_height=figure_height,
        controls_width_percent=controls_width_percent,
        debug=debug,
    )

    # Find an available port if none is specified
    if port is None:
        port = _find_available_port()

    url = f"http://{host}:{port}"
    print(f"Interactive plot server running on {url}")

    if open_browser:
        # Open browser in a separate thread after a small delay
        # to ensure the server has started
        def open_browser_tab():
            time.sleep(1.0)  # Short delay to allow server to start
            webbrowser.open(url)

        threading.Thread(target=open_browser_tab).start()

    # This is included as an argument in some deployers but will break the Flask deployer
    kwargs.pop("continuous", None)
    deployer.run(host=host, port=port, **kwargs)

    return deployer
