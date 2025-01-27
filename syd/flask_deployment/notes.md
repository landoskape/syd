Should probably include something like this -- that might make the routing and directory management of flask a little bit easier...
```python
def create_powerpoint_viewer(viewer):
    # Create minimal Flask server
    app = Flask(__name__)
    
    @app.route('/plot')
    def get_plot():
        # Get parameters from request
        # Run Python analysis
        # Return plot as SVG/PNG
        
    # Package server with viewer
    return PowerPointViewer(app)
```