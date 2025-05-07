import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import matplotlib as mpl
import matplotlib.pyplot as plt
import io
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
from werkzeug.serving import make_server

# Use Deployer base class
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
)
from ..support import ParameterUpdateWarning, plot_context

mpl.use("Agg")


class ServerManager:
    def __init__(self):
        self.servers: dict[int, "ServerThread"] = {}

    def register_server(self, server: "ServerThread", port: int):
        self.servers[port] = server

    def close_app(self, port: int | None = None):
        if port is None:
            for server in self.servers.values():
                server.shutdown()
            self.servers.clear()
        else:
            if port in self.servers:
                self.servers[port].shutdown()
                del self.servers[port]


server_manager = ServerManager()


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int, app, debug: bool):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app, threaded=True)
        self.port = port
        self.debug = debug
        self.ready = threading.Event()

        num_open_servers = len(server_manager.servers)
        if num_open_servers >= 10:
            open_servers = "\n".join([f"{port}" for port in server_manager.servers])
            print(
                f"\nYou have {num_open_servers} open servers!\n"
                f"Open servers:\n{open_servers}\n"
                "You can close them with syd.close_servers() or a particular one with syd.close_servers(port).\n"
                "To see a list, use: syd.show_open_servers()."
            )

    def run(self):
        server_manager.register_server(self, self.port)
        self.ready.set()
        self.server.serve_forever()

    def shutdown(self):
        # Call this to stop the server cleanly
        self.server.shutdown()


@dataclass
class FlaskLayoutConfig:
    """Configuration for the Flask viewer layout."""

    controls_position: str = "left"  # Options are: 'left', 'top', 'right', 'bottom'
    controls_width_percent: int = 15
    plot_margin_percent: float = 10

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
    A deployment system for Viewer as a Flask web application using the Deployer base class.
    Creates a Flask app with routes for the UI, data API, and plot generation.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        fig_dpi: int = 300,
        controls_width_percent: int = 20,
        plot_margin_percent: float = 2.5,
        suppress_warnings: bool = True,
        debug: bool = False,
        host: Optional[str] = None,
        port: Optional[int] = None,
        open_browser: bool = True,
        update_threshold: float = 1.0,
        timeout_threshold: float = 10.0,
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
        plot_margin_percent : float, optional
            Margin around the plot (inches)
        suppress_warnings : bool, optional
            Whether to suppress ParameterUpdateWarning during updates
        debug : bool, optional
            Whether to enable debug mode for Flask
        host : str, optional
            Host address for the server (default: '127.0.0.1')
        port : int, optional
            Port for the server. If None, finds an available port (default: None).
        open_browser : bool, optional
            Whether to open the web application in a browser tab (default: True).
        update_threshold : float, optional
            Time in seconds to wait before showing the loading indicator (default: 1.0)
        timeout_threshold : float, optional
            Time in seconds to wait for the browser to open (default: 10.0).
        """
        self.viewer = viewer
        self.suppress_warnings = suppress_warnings
        self._updating = False  # Flag to check circular updates
        self.update_threshold = update_threshold  # Store update threshold
        self.timeout_threshold = timeout_threshold  # Store timeout threshold

        # Flask specific configurations
        self.config = FlaskLayoutConfig(
            controls_position=controls_position,
            controls_width_percent=controls_width_percent,
            plot_margin_percent=plot_margin_percent,
        )
        self.fig_dpi = fig_dpi
        self.debug = debug

        # Determine static and template folder paths
        package_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_folder = os.path.join(package_dir, "static")
        self.template_folder = os.path.join(package_dir, "templates")

        # Flask app instance - will be created in build_layout
        self.app: Optional[Flask] = None

        # Server details - will be set in display
        self.host: Optional[str] = host
        self.port: Optional[int] = port
        self.url: Optional[str] = None
        self.open_browser: bool = open_browser

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

        @app.route("/")
        def home():
            """Render the main page using the index.html template."""
            # Pass the layout config to the template
            return render_template("index.html", title="Syd Viewer", config=self.config)

        @app.route("/init-data")
        def init_data():
            """Provide initial parameter information to the frontend."""
            param_info = {
                name: self._get_parameter_info(param)
                for name, param in self.viewer.parameters.items()
            }
            # Get the order of parameters
            param_order = list(self.viewer.parameters.keys())
            # Also include the initial state and configuration
            return jsonify(
                {
                    "params": param_info,
                    "param_order": param_order,
                    "state": self.viewer.state,
                    "config": {
                        "controls_position": self.config.controls_position,
                        "controls_width_percent": self.config.controls_width_percent,
                        "update_threshold": self.update_threshold,
                    },
                }
            )

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
                with plot_context():
                    # Use the viewer's plot method with its current state
                    fig = self.viewer.plot(self.viewer.state)
                    self.viewer._figure = fig
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
                # Return current state to avoid frontend hanging.
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
                value = data.get("value", None)
                action = data.get("action", False)

                if not name or name not in self.viewer.parameters:
                    app.logger.error(f"Invalid parameter name received: {name}")
                    return jsonify({"error": f"Parameter '{name}' not found"}), 404

                parameter = self.viewer.parameters[name]
                replot = True

                # Optionally suppress warnings during updates
                with warnings.catch_warnings():
                    if self.suppress_warnings:
                        warnings.filterwarnings(
                            "ignore", category=ParameterUpdateWarning
                        )

                    if action:
                        # Handle button actions: directly call the callback
                        if isinstance(parameter, ButtonAction) and parameter.callback:
                            # Pass the current state dictionary to the callback
                            parameter.callback(self.viewer.state)
                            replot = parameter.replot
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
                final_param_info = {
                    name: self._get_parameter_info(param)
                    for name, param in self.viewer.parameters.items()
                }
                return jsonify(
                    {
                        "success": True,
                        "state": final_state,
                        "params": final_param_info,
                        "replot": replot,
                    }
                )

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

    def display(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        open_browser: bool = True,
    ) -> None:
        """Starts the Flask development server."""
        if not self.app:
            raise RuntimeError(
                "Flask app not built. Call build_layout() before display()."
            )

        # Find an available port if none is specified
        self.port = port or _find_available_port()
        self.host = host or socket.gethostbyname(socket.gethostname())
        self.url = f"http://{self.host}:{self.port}"
        print(f" * Syd Flask server running on {self.url}")

        # if open_browser:

        #     def wait_until_responsive(url, timeout=self.timeout_threshold):
        #         start_time = time.time()
        #         while time.time() - start_time < timeout:
        #             try:
        #                 r = requests.get(url, timeout=0.5)
        #                 if r.status_code == 200:
        #                     return True
        #             except requests.exceptions.RequestException:
        #                 pass
        #             time.sleep(0.1)
        #         return False

        #     def open_browser_tab_when_ready():
        #         if wait_until_responsive(self.url):
        #             out = webbrowser.open(self.url, new=1, autoraise=True)
        #         else:
        #             print(
        #                 f"Could not open browser: server at {self.url} not responding."
        #                 f"Increase the timeout_threshold to fix this! It's set to {self.timeout_threshold} seconds."
        #                 "You can do this from viewer.show(timeout_threshold=...) or in the FlaskDeployer constructor."
        #                 "Also, this is unexpected so please report this issue on GitHub."
        #             )

        #     threading.Thread(target=open_browser_tab_when_ready, daemon=True).start()

        # # Run the Flask server using Werkzeug's run_simple
        # # Pass debug status to run_simple for auto-reloading
        # run_simple(
        #     self.host,
        #     self.port,
        #     self.app,
        #     use_reloader=False,
        #     use_debugger=self.debug,
        # )

        # 1) Spin up the server thread
        srv_thread = ServerThread(self.host, self.port, self.app, debug=self.debug)
        srv_thread.start()

        # 2) Wait for the socket‐bind event (not for an HTTP 200)
        if not srv_thread.ready.wait(timeout=self.timeout_threshold):
            print(
                f"[!] Server did not bind within {self.timeout_threshold:.1f}s; it may already be in use."
            )
        else:
            # 3) Now we know the app is truly listening; open a focused window
            if open_browser:
                webbrowser.open(self.url, new=1, autoraise=True)

        # 4) Keep the thread handle around so you can call srv_thread.shutdown()
        self._server_thread = srv_thread

    def deploy(self) -> None:
        """
        Deploy the viewer using Flask.

        Builds components (no-op), layout (Flask app/routes),
        and then starts the server.
        """
        # build_layout creates the Flask app and routes
        self.build_layout()

        # Initial plot generation is handled implicitly when the first client connects
        # and requests /plot. We don't need an explicit initial self.update_plot() call here,
        # though the base class might call it if not overridden. Let's rely on the
        # frontend fetching the initial plot based on the initial state from /init-data.

        print("Starting Flask server...")
        # Display starts the server
        self.display(
            host=self.host,
            port=self.port,
            open_browser=self.open_browser,
        )

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


def _find_available_port(start_port=5000, max_attempts=1000):
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
