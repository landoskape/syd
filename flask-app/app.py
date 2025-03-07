import matplotlib as mpl

mpl.use("Agg")

from flask import Flask, send_file, request, make_response, jsonify, render_template
import matplotlib.pyplot as plt
import numpy as np
import io
import logging


def create_app():
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/init-data")
    def init_data():
        return jsonify(
            {
                "default_frequency": 1.0,
                "default_amplitude": 1.0,
                "default_offset": 0.0,
                "default_color": "#FF0000",
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

            # Create a sine wave plot
            fig, ax = plt.subplots(figsize=(10, 6))

            # Generate data
            x = np.linspace(0, 2 * np.pi, 1000)
            y = amplitude * np.sin(frequency * x) + offset

            # Plot the sine wave
            ax.plot(x, y, color=color, linewidth=2)

            # Add grid and labels
            ax.grid(True, linestyle="--", alpha=0.7)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_title(f"Sine Wave: A={amplitude}, f={frequency}, offset={offset}")

            # Set y-axis limits based on amplitude and offset
            y_margin = max(1, amplitude) * 1.2
            ax.set_ylim(offset - y_margin, offset + y_margin)

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
