# Interactive Viewer Documentation Guide

## Overview
This guide summarizes approaches for documenting interactive viewers built with the InteractiveViewer class using ipywidgets for notebook deployment.

## Example Viewers Created

### 1. SineWaveViewer
A basic viewer demonstrating:
- Amplitude and frequency sliders
- Grid toggle
- Color selection dropdown

### 2. ScatterPlotViewer
A more complex viewer showing:
- Point count control
- Point size adjustment
- Colormap selection
- Reset button functionality

### 3. HistogramViewer
An advanced viewer featuring:
- Distribution type selection
- Bin count control
- Parameter adjustments
- Density normalization toggle

## Documentation Approaches

### Manual Methods
1. **Screenshots with Annotations**
   - Capture both controls and figure
   - Add explanatory annotations
   - Show before/after states
   - Good for static documentation

2. **GIF Recordings**
   - Capture live interactions
   - Show dynamic updates
   - Demonstrate user workflows
   - Useful for tutorials

### Automated Methods

1. **nbconvert**
   ```bash
   jupyter nbconvert --to html --execute your_notebook.ipynb
   ```
   - Pros: Built-in tool
   - Cons: Only captures final state
   - Best for: Basic static documentation

2. **jupyter-ui-poll**
   ```python
   from jupyter_ui_poll import ui_events
   with ui_events() as poll:
       viewer.deploy()
       while not poll(1):
           continue
   ```
   - Pros: Captures widget states
   - Cons: Requires manual timing
   - Best for: Custom capture scripts

3. **voila**
   ```bash
   voila --convert=html notebook.ipynb
   ```
   - Pros: Creates standalone web apps
   - Cons: May lose some interactivity
   - Best for: Deployment documentation

4. **nbscreenshot (Recommended)**
   ```python
   from nbscreenshot import screenshot_widget, record_widget
   ```
   - Pros:
     - Automated capture
     - Supports both static and animated output
     - Integrates well with documentation tools
   - Best for: Comprehensive documentation

## Recommended Documentation Structure

```markdown
# Viewer Name

## Purpose
Brief description of the viewer's purpose and use case.

## Features
- List of key features
- Available parameters
- Special interactions

## Code Example
```python
# Example code showing viewer setup and deployment
```

## Interactive Examples
[Automatically captured images/GIFs showing different states]

## Parameter Reference
| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| param1    | float| 0-1   | Description |

## Usage Examples
Common use cases and example configurations
```

## Automated Documentation Setup

1. Install required tools:
```bash
pip install nbscreenshot
```

2. Use the automated capture functions:
```python
from auto_capture import capture_viewer_states, generate_viewer_documentation

# Define states to capture
variations = [
    {'param1': value1},
    {'param2': value2}
]

# Generate documentation
doc = generate_viewer_documentation(
    viewer,
    "Viewer Name",
    "Description",
    variations
)
```

## Best Practices

1. **Documentation Coverage**
   - Document all parameters
   - Show common configurations
   - Include edge cases
   - Demonstrate practical use cases

2. **Image Capture**
   - Use consistent window sizes
   - Ensure all controls are visible
   - Show both initial and modified states
   - Capture error states and edge cases

3. **Code Examples**
   - Include complete setup code
   - Show parameter configurations
   - Demonstrate callback usage
   - Include error handling

4. **Integration**
   - Use with Sphinx/MkDocs
   - Include in Jupyter notebooks
   - Add to package documentation
   - Create tutorial notebooks

## Next Steps

1. Set up automated documentation pipeline
2. Create example notebooks for each viewer
3. Generate comprehensive documentation
4. Add tutorials and user guides

## Resources

- [nbscreenshot Documentation](https://nbscreenshot.readthedocs.io/)
- [Jupyter Widget Documentation](https://ipywidgets.readthedocs.io/)
- [Voila Documentation](https://voila.readthedocs.io/)