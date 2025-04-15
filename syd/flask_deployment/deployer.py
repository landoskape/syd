import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import matplotlib as mpl
import matplotlib.pyplot as plt
import io
import time
from functools import wraps
import webbrowser
import threading
import socket
import warnings

from flask import (
    Flask,
    send_file,
    request,
    make_response,
    jsonify,
    render_template,
)
from werkzeug.serving import run_simple

# Use Deployer base class
from ..deployer import Deployer, _plot_context
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
    ParameterUpdateWarning,
)

mpl.use("Agg")


@dataclass
class FlaskLayoutConfig:
    """Configuration for the Flask viewer layout."""

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
        return self.controls_position == "left" or self.controls_position == "right"


# Inherit from Deployer
class FlaskDeployer(Deployer):
    """
    A deployment system for Viewer as a Flask web application using the Deployer base class.
    Creates a Flask app with routes for the UI, data API, and plot generation.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        fig_dpi: int = 300,
        controls_width_percent: int = 30,
        static_folder: Optional[str] = None,
        template_folder: Optional[str] = None,
        suppress_warnings: bool = False,  # Added from base class
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
            Approximate width for template layout guidance (inches)
        figure_height : float, optional
            Approximate height for template layout guidance (inches)
        controls_width_percent : int, optional
            Width of the controls panel as a percentage of the total width
        static_folder : str, optional
            Custom path to static files
        template_folder : str, optional
            Custom path to template files
        suppress_warnings : bool, optional
            Whether to suppress ParameterUpdateWarning during updates
        debug : bool, optional
            Whether to enable debug mode for Flask
        """
        # Call base class constructor
        super().__init__(viewer, suppress_warnings)

        # Flask specific configurations
        self.config = FlaskLayoutConfig(
            controls_position=controls_position,
            controls_width_percent=controls_width_percent,
        )
        self.fig_dpi = fig_dpi
        self.debug = debug

        # Determine static and template folder paths
        package_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_folder = static_folder or os.path.join(package_dir, "static")
        self.template_folder = template_folder or os.path.join(package_dir, "templates")

        # Flask app instance - will be created in build_layout
        self.app: Optional[Flask] = None

        # Server details - will be set in display
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.url: Optional[str] = None

    def build_components(self) -> None:
        """Builds components - No-op for Flask as components are in HTML."""
        # In Flask, components are primarily defined in the HTML templates.
        # The necessary parameter info is fetched via the /init-data endpoint.
        pass

    def build_layout(self) -> None:
        """Create and configure the Flask application and its routes."""
        # Avoid re-building the app if called multiple times
        if self.app:
            return

        app = Flask(
            "SydFlaskDeployer",
            static_folder=self.static_folder,
            template_folder=self.template_folder,
        )
        self.app = app

        # Configure logging
        if not self.debug:
            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)

        # --- Define Flask Routes ---

        @app.route("/")
        def home():
            """Render the main page using the index.html template."""
            # Pass the layout config to the template
            return render_template("index.html", config=self.config)

        @app.route("/init-data")
        def init_data():
            """Provide initial parameter information to the frontend."""
            param_info = {
                name: self._get_parameter_info(param)
                for name, param in self.viewer.parameters.items()
            }
            # Also include the initial state
            return jsonify({"params": param_info, "state": self.viewer.state})

        @app.route("/plot")
        def plot():
            """Generate and return the plot image based on the current viewer state."""
            if self._updating:
                # Avoid plot generation during an update cycle if possible,
                # though frontend usually waits for update response before fetching plot.
                # Return a placeholder or error? For now, just proceed.
                app.logger.warning("Plot requested while parameters are updating.")

            try:
                # Generate the plot using the current state from the viewer instance
                # The _plot_context ensures plt state is managed correctly.
                with _plot_context():
                    # Use the viewer's plot method with its current state
                    fig = self.viewer.plot(self.viewer.state)
                    if not isinstance(fig, mpl.figure.Figure):
                        raise TypeError(
                            f"viewer.plot() must return a matplotlib Figure, but got {type(fig)}"
                        )

                # Save the plot to a buffer
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=self.fig_dpi)
                buf.seek(0)
                plt.close(fig)  # Ensure figure is closed

                # Return the image as a response
                response = make_response(send_file(buf, mimetype="image/png"))
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            except Exception as e:
                app.logger.error(f"Error generating plot: {str(e)}", exc_info=True)
                # Return a JSON error for easier frontend handling
                return jsonify({"error": f"Error generating plot: {str(e)}"}), 500

        @app.route("/update-param", methods=["POST"])
        def update_param():
            """Handle parameter updates or actions triggered from the frontend."""
            if self._updating:
                # Prevent processing new updates if already updating (potential cycle)
                app.logger.warning(
                    "Update requested while already processing an update."
                )
                # Return current state to avoid frontend hanging? Or an error?
                # Returning current state might be safer.
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Server busy processing previous update.",
                            "state": self.viewer.state,
                        }
                    ),
                    429,
                )  # Too Many Requests

            try:
                self._updating = True  # Set base class flag

                data = request.get_json()
                name = data.get("name")
                value = data.get("value")
                is_action = data.get("is_action", False)  # Check is_action flag

                if not name or name not in self.viewer.parameters:
                    app.logger.error(f"Invalid parameter name received: {name}")
                    return jsonify({"error": f"Parameter '{name}' not found"}), 404

                parameter = self.viewer.parameters[name]

                # Optionally suppress warnings during updates
                with warnings.catch_warnings():
                    if self.suppress_warnings:
                        warnings.filterwarnings(
                            "ignore", category=ParameterUpdateWarning
                        )

                    if is_action:
                        # Handle button actions: directly call the callback
                        if isinstance(parameter, ButtonAction) and parameter.callback:
                            # Pass the current state dictionary to the callback
                            parameter.callback(self.viewer.state)
                        else:
                            app.logger.warning(
                                f"Received action request for non-action parameter: {name}"
                            )
                    else:
                        # Handle regular parameter updates: parse and set value
                        try:
                            parsed_value = self._parse_parameter_value(name, value)
                            # Use base class method to set value and trigger callbacks
                            self.viewer.set_parameter_value(name, parsed_value)
                        except (ValueError, TypeError, json.JSONDecodeError) as e:
                            app.logger.error(
                                f"Error parsing value for parameter '{name}': {e}"
                            )
                            return (
                                jsonify(
                                    {"error": f"Invalid value format for {name}: {e}"}
                                ),
                                400,
                            )

                # State might have changed due to callbacks, return the *final* state
                final_state = self.viewer.state
                return jsonify({"success": True, "state": final_state})

            except Exception as e:
                app.logger.error(
                    f"Error updating parameter '{name}': {str(e)}", exc_info=True
                )
                # Return the state *before* the error if possible? Or just error.
                return (
                    jsonify(
                        {
                            "error": f"Server error updating parameter: {str(e)}",
                            "state": self.viewer.state,
                        }
                    ),
                    500,
                )
            finally:
                self._updating = False  # Clear base class flag

    def display_new_plot(self, figure: mpl.figure.Figure) -> None:
        """Handles displaying a new plot - No-op for Flask."""
        # In Flask, the plot is requested by the client via the /plot endpoint.
        # The backend doesn't push the plot directly.
        # The figure object passed here is generated by the base update_plot method,
        # but we don't need to do anything with it here.
        plt.close(figure)  # Close the figure generated by base update_plot

    def display(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        open_browser: bool = True,
        **kwargs,
    ) -> None:
        """Starts the Flask development server."""
        if not self.app:
            raise RuntimeError(
                "Flask app not built. Call build_layout() before display()."
            )

        # Find an available port if none is specified
        self.port = port or _find_available_port()
        self.host = host
        self.url = f"http://{self.host}:{self.port}"
        print(f" * Syd Flask server running on {self.url}")

        if open_browser:
            print(f" * Opening browser...")

            # Open browser in a separate thread after a small delay
            def open_browser_tab():
                time.sleep(1.0)  # Slightly longer delay
                webbrowser.open(self.url)

            threading.Thread(target=open_browser_tab, daemon=True).start()

        # Run the Flask server using Werkzeug's run_simple
        # Pass debug status to run_simple for auto-reloading
        run_simple(
            self.host,
            self.port,
            self.app,
            use_reloader=self.debug,
            use_debugger=self.debug,
            **kwargs,
        )

    # --- Overridden Methods ---

    def deploy(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        open_browser: bool = True,
        **kwargs,
    ) -> None:
        """
        Deploy the viewer using Flask.

        Builds components (no-op), layout (Flask app/routes),
        and then starts the server.
        """
        print("Building Flask components and layout...")
        # build_components is intentionally simple for Flask
        self.build_components()
        # build_layout creates the Flask app and routes
        self.build_layout()

        # Initial plot generation is handled implicitly when the first client connects
        # and requests /plot. We don't need an explicit initial self.update_plot() call here,
        # though the base class might call it if not overridden. Let's rely on the
        # frontend fetching the initial plot based on the initial state from /init-data.

        print("Starting Flask server...")
        # Display starts the server
        self.display(host=host, port=port, open_browser=open_browser, **kwargs)

    def _get_parameter_info(self, param: Parameter) -> Dict[str, Any]:
        """
        Convert a Parameter object to a dictionary of information for the frontend.
        (Identical to original, kept for clarity)
        """
        # Add name/label
        info = {
            "name": param.name,
            "value": param.value,
        }

        if isinstance(param, TextParameter):
            info.update({"type": "text"})
        elif isinstance(param, BooleanParameter):
            info.update({"type": "boolean"})
        elif isinstance(param, SelectionParameter):
            info.update({"type": "selection", "options": param.options})
        elif isinstance(param, MultipleSelectionParameter):
            info.update(
                {
                    "type": "multiple-selection",
                    "options": param.options,
                }
            )
        elif isinstance(param, IntegerParameter):
            info.update(
                {
                    "type": "integer",
                    "min": param.min,
                    "max": param.max,
                }
            )
        elif isinstance(param, FloatParameter):
            info.update(
                {
                    "type": "float",
                    "min": param.min,
                    "max": param.max,
                    "step": param.step,
                }
            )
        elif isinstance(param, IntegerRangeParameter):
            info.update(
                {
                    "type": "integer-range",
                    "min": param.min,
                    "max": param.max,
                }
            )
        elif isinstance(param, FloatRangeParameter):
            info.update(
                {
                    "type": "float-range",
                    "min": param.min,
                    "max": param.max,
                    "step": param.step,
                }
            )
        elif isinstance(param, UnboundedIntegerParameter):
            info.update({"type": "unbounded-integer"})
        elif isinstance(param, UnboundedFloatParameter):
            info.update({"type": "unbounded-float", "step": param.step})
        elif isinstance(param, ButtonAction):
            # Button doesn't have a 'value' in the same way, label is important
            info.update({"type": "button", "is_action": True})
            # Remove 'value' as it's not applicable
            info.pop("value", None)
        else:
            # Fallback for unknown types
            info.update(
                {"type": "unknown", "value": str(param.value)}
            )  # Keep value as string

        return info

    # def _parse_request_args(self, args) -> Dict[str, Any]:
    # ... (removed - /plot now uses self.viewer.state directly) ...

    def _parse_parameter_value(self, name: str, value: Any) -> Any:
        """
        Parse a parameter value from the frontend based on its type.
        Handles type conversions (e.g., string 'true' to bool True, string '5' to int 5).

        Raises ValueError or TypeError on parsing failure.
        """
        if name not in self.viewer.parameters:
            # Should not happen if checked before calling, but defensive check
            raise ValueError(f"Parameter '{name}' not found during parsing.")

        param = self.viewer.parameters[name]

        # Handle specific types
        try:
            if isinstance(param, TextParameter):
                return str(value)  # Ensure it's a string
            elif isinstance(param, BooleanParameter):
                # Handle 'true'/'false' strings robustly
                if isinstance(value, str):
                    if value.lower() == "true":
                        return True
                    if value.lower() == "false":
                        return False
                    # Try converting string numbers to bool (e.g., "1" -> True)
                    try:
                        return bool(int(value))
                    except ValueError:
                        pass  # Ignore if not int-like string
                return bool(value)  # Standard bool conversion
            elif isinstance(param, (IntegerParameter, UnboundedIntegerParameter)):
                return int(value)
            elif isinstance(param, (FloatParameter, UnboundedFloatParameter)):
                return float(value)
            elif isinstance(param, (IntegerRangeParameter, FloatRangeParameter)):
                # Expect a list/tuple from JSON, e.g., [min, max]
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    # Ensure types match the parameter type
                    if isinstance(param, IntegerRangeParameter):
                        return [int(v) for v in value]
                    else:  # FloatRangeParameter
                        return [float(v) for v in value]
                # Allow JSON string representation '[min, max]'
                elif isinstance(value, str):
                    try:
                        parsed_list = json.loads(value)
                        if isinstance(parsed_list, list) and len(parsed_list) == 2:
                            if isinstance(param, IntegerRangeParameter):
                                return [int(v) for v in parsed_list]
                            else:
                                return [float(v) for v in parsed_list]
                        else:
                            raise ValueError(
                                "Range requires a list/tuple of two numbers."
                            )
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON string for range: {value}")
                else:
                    raise ValueError(
                        f"Invalid format for range parameter '{name}'. Expected list/tuple of two numbers or JSON string."
                    )

            elif isinstance(param, MultipleSelectionParameter):
                # Expect a list from JSON, e.g., ['a', 'b']
                if isinstance(value, list):
                    # Ensure options are valid? Base Parameter class might do this.
                    # Return as is for now.
                    return value
                # Allow JSON string representation '["a", "b"]'
                elif isinstance(value, str):
                    try:
                        parsed_list = json.loads(value)
                        if isinstance(parsed_list, list):
                            return parsed_list
                        else:  # Allow single non-list value to be wrapped? No, spec is list.
                            raise ValueError("Multiple selection requires a list.")
                    except json.JSONDecodeError:
                        # Handle case where a single string value might be sent for a multi-select
                        # if the frontend logic is imperfect. Treat as a list with one item?
                        # Let's be strict for now.
                        raise ValueError(
                            f"Invalid JSON string for multiple selection: {value}"
                        )
                else:
                    # If it's not a list or valid JSON string, treat as empty list? Or error?
                    # Error seems safer.
                    raise ValueError(
                        f"Invalid format for multiple selection parameter '{name}'. Expected list or JSON string list."
                    )

            elif isinstance(param, SelectionParameter):
                # Value needs to match one of the options *by type* if possible.
                # The original logic was quite complex. Let's simplify:
                # Try direct match first.
                if value in param.options:
                    return value

                # Try converting the incoming value to the types present in options.
                option_types = {type(opt) for opt in param.options}

                # Prioritize type conversion based on options
                if float in option_types:
                    try:
                        float_val = float(value)
                        # Check if float matches any option (handle float inaccuracies)
                        for opt in param.options:
                            if (
                                isinstance(opt, (int, float))
                                and abs(float_val - float(opt)) < 1e-9
                            ):
                                return opt  # Return the original option instance
                        # If no close match, but float conversion worked, maybe return float_val?
                        # Let's stick to returning existing options.
                    except (ValueError, TypeError):
                        pass

                if int in option_types:
                    try:
                        int_val = int(value)
                        if int_val in param.options:
                            return int_val
                    except (ValueError, TypeError):
                        pass

                if str in option_types:
                    str_val = str(value)
                    if str_val in param.options:
                        return str_val

                # If no match after trying conversions, raise error. Let Parameter handle validation.
                # Returning the original value might bypass validation.
                raise ValueError(
                    f"Value '{value}' is not a valid option for '{name}'. Valid options: {param.options}"
                )

            elif isinstance(param, ButtonAction):
                # Actions don't have a value to parse
                return None  # Or raise error? None seems okay.

            else:
                # Fallback for unknown - return as is, let Parameter validate
                return value

        except (ValueError, TypeError, json.JSONDecodeError) as e:
            # Re-raise with more context
            raise ValueError(
                f"Failed to parse value '{value}' for parameter '{name}' ({type(param).__name__}): {e}"
            )

    # run method is removed, replaced by display & deploy
    # def run(self, host: str = "127.0.0.1", port: Optional[int] = None, **kwargs):
    # ... (removed) ...


def _find_available_port(start_port=5000, max_attempts=100):
    """
    Find an available port starting from start_port.
    (Identical to original)
    """
    for port in range(start_port, start_port + max_attempts):
        # Use localhost address explicitly
        address = "127.0.0.1"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Check if the port is usable
                s.bind((address, port))
                # If bind succeeds, the port is available
                return port
        except OSError as e:
            # If error is Address already in use, try next port
            if e.errno == socket.errno.EADDRINUSE:
                # print(f"Port {port} already in use.") # Optional debug msg
                continue
            else:
                # Re-raise other OS errors
                raise e

    # If loop finishes without finding a port
    raise RuntimeError(
        f"Could not find an available port between {start_port} and {start_port + max_attempts - 1}"
    )


# Updated deploy_flask function
def deploy_flask(
    viewer: Viewer,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    controls_position: str = "left",
    controls_width_percent: int = 30,
    fig_dpi: int = 300,  # Passed to FlaskDeployer constructor
    suppress_warnings: bool = False,  # Passed to FlaskDeployer constructor
    debug: bool = False,
    open_browser: bool = True,
    **kwargs,
):
    """
    Deploy a Viewer as a Flask web application using the refactored FlaskDeployer.

    Parameters
    ----------
    viewer : Viewer
        The viewer instance to deploy.
    host : str, optional
        Host address for the server (default: '127.0.0.1').
    port : int, optional
        Port for the server. If None, finds an available port (default: None).
    controls_position : str, optional
        Layout position for controls ('left', 'top', 'right', 'bottom', default: 'left').
    controls_width_percent : int, optional
        Percentage width of the controls panel (default: 30).
    fig_dpi : int, optional
        Resolution (dots per inch) for the generated plot images (default: 300).
    suppress_warnings : bool, optional
        Suppress ParameterUpdateWarning during backend updates (default: False).
    debug : bool, optional
        Enable Flask debug mode (reloader, debugger, default: False).
    open_browser : bool, optional
        Automatically open the web application in a browser tab (default: True).
    **kwargs
        Additional keyword arguments passed to `werkzeug.serving.run_simple`.

    Returns
    -------
    FlaskDeployer
        The deployer instance (server runs until interrupted).
    """
    # Instantiate the refactored deployer
    deployer = FlaskDeployer(
        viewer=viewer,
        controls_position=controls_position,
        controls_width_percent=controls_width_percent,
        fig_dpi=fig_dpi,
        suppress_warnings=suppress_warnings,
        debug=debug,
        # static_folder and template_folder use defaults unless passed in kwargs?
        # Let's assume defaults are fine unless user overrides via kwargs if needed.
        # For now, not explicitly passing them from here.
    )

    if "continuous" in kwargs:
        kwargs.pop("continuous")

    # Use the deployer's deploy method to handle build and display steps
    # Pass server-specific arguments to deploy
    deployer.deploy(host=host, port=port, open_browser=open_browser, **kwargs)

    # The server runs within deployer.deploy() until stopped (e.g., Ctrl+C)
    # Return the instance if needed, although the primary action is running the server.
    return deployer
