from typing import Dict, Any, Optional, List
import warnings
from functools import wraps
from dataclasses import dataclass
from contextlib import contextmanager
from time import time
import base64
from io import BytesIO
import threading
import webbrowser
from pathlib import Path

from flask import Flask, render_template, jsonify, request, Response
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..parameters import ParameterUpdateWarning
from ..viewer import Viewer
from .components import BaseComponent, ComponentStyle, create_component


@contextmanager
def _plot_context():
    plt.ioff()
    try:
        yield
    finally:
        plt.ion()


def get_backend_type():
    """
    Determines the current matplotlib backend type and returns relevant info
    """
    backend = mpl.get_backend().lower()
    if "agg" in backend:
        return "agg"
    elif "inline" in backend:
        return "inline"
    else:
        # Force Agg backend for Flask
        mpl.use("Agg")
        return "agg"


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
    figure_width: float = 8.0
    figure_height: float = 6.0
    controls_width_percent: int = 30
    template_path: Optional[str] = None
    static_path: Optional[str] = None

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
    A deployment system for Viewer in Flask web applications.
    Built around the parameter component system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        figure_width: float = 8.0,
        figure_height: float = 6.0,
        controls_width_percent: int = 30,
        continuous: bool = False,
        suppress_warnings: bool = False,
        host: str = "127.0.0.1",
        port: int = 5000,
        template_path: Optional[str] = None,
        static_path: Optional[str] = None,
    ):
        self.viewer = viewer
        self.config = LayoutConfig(
            controls_position=controls_position,
            figure_width=figure_width,
            figure_height=figure_height,
            controls_width_percent=controls_width_percent,
            template_path=template_path,
            static_path=static_path,
        )
        self.continuous = continuous
        self.suppress_warnings = suppress_warnings
        self.host = host
        self.port = port

        # Initialize containers
        self.backend_type = get_backend_type()
        self.parameter_components: Dict[str, BaseComponent] = {}
        self.app = self._create_flask_app()

        # Flag to prevent circular updates
        self._updating = False

        # Last figure to close when new figures are created
        self._last_figure = None

    def _create_flask_app(self) -> Flask:
        """Create and configure the Flask application."""
        template_path = self.config.template_path or str(
            Path(__file__).parent / "templates"
        )
        static_path = self.config.static_path or str(Path(__file__).parent / "static")

        app = Flask(__name__, template_folder=template_path, static_folder=static_path)

        # Register routes
        @app.route("/")
        def index():
            # Generate initial plot
            initial_plot = self._generate_plot()
            if initial_plot is not None:
                buffer = BytesIO()
                initial_plot.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                initial_plot_data = base64.b64encode(buffer.getvalue()).decode()
            else:
                initial_plot_data = ""

            return render_template(
                "viewer.html",
                components=self._get_component_html(),
                controls_position=self.config.controls_position,
                controls_width=self.config.controls_width_percent,
                figure_width=self.config.figure_width,
                figure_height=self.config.figure_height,
                continuous=self.continuous,
                initial_plot=initial_plot_data,
            )

        @app.route("/update/<name>", methods=["POST"])
        def update_parameter(name: str):
            if name not in self.viewer.parameters:
                return jsonify({"error": f"Parameter {name} not found"}), 404

            try:
                value = request.json["value"]
                self._handle_parameter_update(name, value)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @app.route("/state")
        def get_state():
            return jsonify(self.viewer.state)

        @app.route("/plot")
        def get_plot():
            # Generate plot and convert to base64 PNG
            figure = self._generate_plot()
            if figure is None:
                return jsonify({"error": "Failed to generate plot"}), 500

            # Save plot to bytes buffer
            buffer = BytesIO()
            figure.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            return jsonify({"image": image_base64})

        return app

    def _create_parameter_components(self) -> None:
        """Create component instances for all parameters."""
        style = ComponentStyle(
            width="100%",
            margin="10px 0",
            description_width="auto",
        )

        for name, param in self.viewer.parameters.items():
            component = create_component(
                param,
                continuous=self.continuous,
                style=style,
            )
            self.parameter_components[name] = component

    def _get_component_html(self) -> List[str]:
        """Get HTML for all components."""
        if not self.parameter_components:
            self._create_parameter_components()
        return [comp.html for comp in self.parameter_components.values()]

    @debounce(0.2)
    def _handle_parameter_update(self, name: str, value: Any) -> None:
        """Handle updates to parameter values."""
        if self._updating:
            print(
                "Already updating -- there's a circular dependency!"
                "This is probably caused by failing to disable callbacks for a parameter."
                "It's a bug --- tell the developer on github issues please."
            )
            return

        try:
            self._updating = True

            # Optionally suppress warnings during parameter updates
            with warnings.catch_warnings():
                if self.suppress_warnings:
                    warnings.filterwarnings("ignore", category=ParameterUpdateWarning)

                component = self.parameter_components[name]
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

            component = self.parameter_components[name]
            if not component.matches_parameter(parameter):
                component.update_from_parameter(parameter)

    def _generate_plot(self) -> Optional[plt.Figure]:
        """Generate the current plot."""
        try:
            with _plot_context():
                figure = self.viewer.plot(self.viewer.state)

            # Close the last figure if it exists to keep matplotlib clean
            if self._last_figure is not None:
                plt.close(self._last_figure)

            self._last_figure = figure
            return figure
        except Exception as e:
            print(f"Error generating plot: {e}")
            return None

    def deploy(self, open_browser: bool = True) -> None:
        """
        Deploy the viewer as a Flask web application.

        Parameters
        ----------
        open_browser : bool, optional
            Whether to automatically open the browser when deploying (default: True)
        """
        with self.viewer._deploy_app():
            if open_browser:
                # Open browser in a separate thread to not block
                threading.Timer(
                    1.0, lambda: webbrowser.open(f"http://{self.host}:{self.port}")
                ).start()

            # Start Flask app
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,  # Debug mode doesn't work well with matplotlib
                use_reloader=False,  # Reloader causes issues with matplotlib
            )
