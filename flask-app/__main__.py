"""
Main entry point for the Sine Wave Visualizer flask app.
"""

import socket

from .app import create_app

if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 5000
    print(f"Interactive plot server running on http://{local_ip}:{port}")
    app = create_app()
    app.run(debug=True, host=local_ip, port=port)
