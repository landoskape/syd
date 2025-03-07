import matplotlib as mpl

mpl.use("Agg")

from flask import Flask, send_file, request, make_response, jsonify, render_template
import matplotlib.pyplot as plt
import io
import logging
import json
from .viewer import (
    SineWaveViewer,
    FloatParam,
    IntegerParam,
    SelectionParam,
    MultipleSelectionParam,
    FloatRangeParam,
    IntegerRangeParam,
)


def create_app():
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    # Initialize the SineWaveViewer instance
    viewer = SineWaveViewer()

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/init-data")
    def init_data():
        # Gather parameter information dynamically
        param_info = {}

        for name, param in viewer.params.items():
            if isinstance(param, FloatParam):
                param_info[name] = {
                    "type": "float",
                    "value": param.value,
                    "min": param.min,
                    "max": param.max,
                    "step": param.step,
                }
            elif isinstance(param, IntegerParam):
                param_info[name] = {
                    "type": "integer",
                    "value": param.value,
                    "min": param.min,
                    "max": param.max,
                    "step": 1,
                }
            elif isinstance(param, FloatRangeParam):
                param_info[name] = {
                    "type": "float-range",
                    "value": param.value,
                    "min": param.min,
                    "max": param.max,
                    "step": param.step,
                }
            elif isinstance(param, IntegerRangeParam):
                param_info[name] = {
                    "type": "integer-range",
                    "value": param.value,
                    "min": param.min,
                    "max": param.max,
                    "step": 1,
                }
            elif isinstance(param, SelectionParam):
                param_info[name] = {
                    "type": "selection",
                    "value": param.value,
                    "options": param.options,
                }
            elif isinstance(param, MultipleSelectionParam):
                param_info[name] = {
                    "type": "multiple-selection",
                    "value": param.value,
                    "options": param.options,
                }

        return jsonify({"params": param_info})

    @app.route("/plot")
    def plot():
        try:
            # Create a state dictionary from all request parameters
            state = {}

            # Process all query parameters
            for name, value in request.args.items():
                # Skip any parameters that aren't registered in the viewer
                if name not in viewer.params:
                    continue

                # Convert value based on parameter type
                if isinstance(viewer.params[name], FloatParam):
                    state[name] = float(value)
                elif isinstance(viewer.params[name], IntegerParam):
                    state[name] = int(value)
                elif isinstance(
                    viewer.params[name], (FloatRangeParam, IntegerRangeParam)
                ):
                    # Range values come as JSON-encoded arrays
                    try:
                        state[name] = json.loads(value)
                    except json.JSONDecodeError:
                        app.logger.error(f"Invalid range format: {value}")
                        continue
                elif isinstance(viewer.params[name], MultipleSelectionParam):
                    # Multiple selection values come as JSON-encoded arrays
                    try:
                        state[name] = json.loads(value)
                    except json.JSONDecodeError:
                        # Fallback to list with single value if not JSON
                        state[name] = [value] if value else []
                else:
                    state[name] = value

            # Update the viewer with new parameters
            viewer.update_parameters(state)

            # Get the plot from the viewer
            fig = viewer.plot()

            # Save the plot to a buffer
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
            buf.seek(0)
            plt.close(fig)

            # Return the image
            response = make_response(send_file(buf, mimetype="image/png"))
            response.headers["Cache-Control"] = "no-cache"
            return response

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return f"Error generating plot: {str(e)}", 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
