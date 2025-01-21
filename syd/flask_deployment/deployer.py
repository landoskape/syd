from typing import Dict, Any, Optional
from dataclasses import dataclass
import threading
from flask import Flask, render_template_string, jsonify, request
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for thread safety
import matplotlib.pyplot as plt
import io
import base64
from contextlib import contextmanager
import webbrowser

from ..interactive_viewer import InteractiveViewer
from .components import WebComponentCollection

# Create a template constant to hold our HTML template
PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Viewer</title>
    {% for css in required_css %}
    <link rel="stylesheet" href="{{ css }}">
    {% endfor %}
    <style>
        {{ custom_styles | safe }}
        .controls {
            {% if config.is_horizontal %}
            width: {{ config.controls_width_percent }}%;
            float: left;
            padding-right: 20px;
            {% endif %}
        }
        .plot-container {
            {% if config.is_horizontal %}
            width: {{ 100 - config.controls_width_percent }}%;
            float: left;
            {% endif %}
        }
        #plot {
            width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="controls">
                {{ components_html | safe }}
            </div>
            <div class="plot-container">
                <img id="plot" src="{{ initial_plot }}">
            </div>
        </div>
    </div>
    
    {% for js in required_js %}
    <script src="{{ js }}"></script>
    {% endfor %}
    
    <script>
        function updateParameter(name, value) {
            fetch('/update_parameter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({name, value})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    return;
                }
                // Update plot
                document.getElementById('plot').src = data.plot;
                // Apply any parameter updates
                for (const [param, js] of Object.entries(data.updates)) {
                    eval(js);
                }
            });
        }
        
        function buttonClick(name) {
            fetch('/button_click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({name})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    return;
                }
                // Update plot
                document.getElementById('plot').src = data.plot;
                // Apply any parameter updates
                for (const [param, js] of Object.entries(data.updates)) {
                    eval(js);
                }
            });
        }
        
        // Initialize components
        {{ components_init | safe }}
    </script>
</body>
</html>
"""


@dataclass
class FlaskLayoutConfig:
    """Configuration for the viewer layout in Flask deployment."""

    controls_position: str = "left"  # Options are: 'left', 'top'
    figure_width: float = 8.0
    figure_height: float = 6.0
    controls_width_percent: int = 30
    port: int = 5000
    host: str = "localhost"

    def __post_init__(self):
        valid_positions = ["left", "top"]
        if self.controls_position not in valid_positions:
            raise ValueError(
                f"Invalid controls position: {self.controls_position}. Must be one of {valid_positions}"
            )

    @property
    def is_horizontal(self) -> bool:
        return self.controls_position == "left"


class FlaskDeployment:
    """A deployment system for InteractiveViewer using Flask to create a web interface."""

    def __init__(
        self,
        viewer: InteractiveViewer,
        layout_config: Optional[FlaskLayoutConfig] = None,
    ):
        if not isinstance(viewer, InteractiveViewer):
            raise TypeError(
                f"viewer must be an InteractiveViewer, got {type(viewer).__name__}"
            )

        self.viewer = viewer
        self.config = layout_config or FlaskLayoutConfig()
        self.components = WebComponentCollection()

        # Initialize Flask app
        self.app = Flask(__name__)
        self._setup_routes()

        # Store current figure
        self._current_figure = None
        self._figure_lock = threading.Lock()

    def _setup_routes(self):
        """Set up the Flask routes for the application."""

        @self.app.route("/")
        def index():
            return self._render_page()

        @self.app.route("/update_parameter", methods=["POST"])
        def update_parameter():
            data = request.json
            name = data.get("name")
            value = data.get("value")

            print(f"Received parameter update: {name} = {value}")  # Debug log

            if name not in self.viewer.parameters:
                print(f"Parameter {name} not found in viewer parameters")  # Debug log
                return jsonify({"error": f"Parameter {name} not found"}), 404

            try:
                print(f"Setting parameter value: {name} = {value}")  # Debug log
                self.viewer.set_parameter_value(name, value)

                # Update the plot with new parameter values
                print("Updating plot with new parameters...")  # Debug log
                self._update_plot()

                updates = self._get_parameter_updates()
                plot_data = self._get_current_plot_data()
                # Debug log
                print(f"Generated updates for parameters: {list(updates.keys())}")

                return jsonify(
                    {
                        "success": True,
                        "updates": updates,
                        "plot": plot_data,
                    }
                )
            except Exception as e:
                print(f"Error updating parameter: {str(e)}")  # Debug log
                return jsonify({"error": str(e)}), 400

        @self.app.route("/button_click", methods=["POST"])
        def button_click():
            data = request.json
            name = data.get("name")

            print(f"Received button click: {name}")  # Debug log

            if name not in self.viewer.parameters:
                print(f"Button {name} not found in viewer parameters")  # Debug log
                return jsonify({"error": f"Parameter {name} not found"}), 404

            try:
                parameter = self.viewer.parameters[name]
                if hasattr(parameter, "callback"):
                    print(f"Executing callback for button: {name}")  # Debug log
                    parameter.callback(self.viewer.get_state())
                else:
                    print(f"No callback found for button: {name}")  # Debug log

                # Update the plot after button click
                print("Updating plot after button click...")  # Debug log
                self._update_plot()

                updates = self._get_parameter_updates()
                plot_data = self._get_current_plot_data()
                # Debug log
                print(f"Generated updates for parameters: {list(updates.keys())}")

                return jsonify(
                    {
                        "success": True,
                        "updates": updates,
                        "plot": plot_data,
                    }
                )
            except Exception as e:
                print(f"Error handling button click: {str(e)}")  # Debug log
                return jsonify({"error": str(e)}), 400

    def _create_components(self):
        """Create web components for all parameters."""
        for name, param in self.viewer.parameters.items():
            self.components.add_component(name, param)

    @contextmanager
    def _plot_context(self):
        """Context manager for thread-safe plotting."""
        plt.ioff()
        try:
            yield
        finally:
            plt.ion()

    def _update_plot(self) -> None:
        """Update the plot with current state."""
        state = self.viewer.get_state()
        print(f"Updating plot with state: {state}")  # Debug log

        with self._plot_context(), self._figure_lock:
            new_fig = self.viewer.plot(state)
            plt.close(self._current_figure)  # Close old figure
            self._current_figure = new_fig
            print("Plot updated successfully")  # Debug log

    def _get_current_plot_data(self) -> str:
        """Get the current plot as a base64 encoded PNG."""
        with self._figure_lock:
            if self._current_figure is None:
                return ""

            buffer = io.BytesIO()
            self._current_figure.savefig(
                buffer,
                format="png",
                bbox_inches="tight",
                dpi=300,
            )
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()

            graphic = base64.b64encode(image_png).decode("utf-8")
            return f"data:image/png;base64,{graphic}"

    def _get_parameter_updates(self) -> Dict[str, Any]:
        """Get JavaScript updates for all parameters."""
        updates = {}
        state = self.viewer.get_state()
        for name, value in state.items():
            # Skip button parameters since they don't have a meaningful value to update
            if (
                hasattr(self.viewer.parameters[name], "_is_button")
                and self.viewer.parameters[name]._is_button
            ):
                continue
            updates[name] = self.components.get_update_js(name, value)
        return updates

    def _render_page(self) -> str:
        """Render the complete HTML page."""
        # Create initial plot
        self._update_plot()

        return render_template_string(
            PAGE_TEMPLATE,
            config=self.config,
            components_html=self.components.get_all_html(),
            components_init=self.components.get_init_js(),
            initial_plot=self._get_current_plot_data(),
            required_css=self.components.get_required_css(),
            required_js=self.components.get_required_js(),
            custom_styles=self.components.get_custom_styles(),
        )

    def deploy(self) -> None:
        """Deploy the interactive viewer as a web application."""
        with self.viewer._deploy_app():
            # Create components
            self._create_components()

            # Open browser
            webbrowser.open(f"http://{self.config.host}:{self.config.port}")

            # Start Flask app
            self.app.run(
                host=self.config.host,
                port=self.config.port,
                debug=False,  # Debug mode doesn't work well with matplotlib
                use_reloader=False,  # Prevent double startup
            )
