import matplotlib as mpl

mpl.use("Agg")

from flask import Flask, send_file, request, make_response, jsonify, render_template
import matplotlib.pyplot as plt
import io
import logging
from .viewer import SineWaveViewer


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
        return jsonify(
            {
                "default_frequency": viewer.frequency,
                "default_amplitude": viewer.amplitude,
                "default_offset": viewer.offset,
                "default_color": viewer.color,
                "color_options": SineWaveViewer.COLOR_OPTIONS,
            }
        )

    @app.route("/plot")
    def plot():
        try:
            # Get parameters from request
            frequency = float(request.args.get("frequency", 1.0))
            amplitude = float(request.args.get("amplitude", 1.0))
            offset = float(request.args.get("offset", 0.0))
            color = request.args.get("color", "#FF0000")

            # Create a state dictionary from the parameters
            state = {
                "frequency": frequency,
                "amplitude": amplitude,
                "offset": offset,
                "color": color,
            }

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
