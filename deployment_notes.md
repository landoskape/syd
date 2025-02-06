# Adding Plotly and Pandas Support to Syd

## Overview
This document outlines how to extend the Syd visualization library to support Plotly and Pandas plotting alongside existing Matplotlib functionality.

## Key Changes

### Plot Method Signature
```python
def plot(self, state: Dict[str, Any]) -> Union[Figure, "go.Figure", "pd.plotting.PlotAccessor"]:
    """Create and return a matplotlib, plotly, or pandas figure."""
```

### Plot Update Logic
```python
def _update_plot(self) -> None:
    state = self.viewer.state
    using_widget = 'widget' in plt.get_backend().lower()
    
    with _plot_context():
        new_fig = self.viewer.plot(state)
        if isinstance(new_fig, plt.Figure):
            if not using_widget:
                plt.close(self._current_figure)
        elif isinstance(new_fig, go.Figure):
            self._current_figure = new_fig.to_html(include_plotlyjs='cdn')
        elif hasattr(new_fig, 'get_figure'):  # Pandas plot
            self._current_figure = new_fig.get_figure()
            
    self._redraw_plot()
```

### Plot Context Manager
```python
@contextmanager
def _plot_context():
    backend = plt.get_backend().lower()
    using_widget = 'widget' in backend
    
    if not using_widget:
        plt.ioff()
    try:
        yield
    finally:
        if not using_widget:
            plt.ion()
```

### Display Logic
```python
def _redraw_plot(self) -> None:
    self.plot_output.clear_output(wait=True)
    with self.plot_output:
        if isinstance(self._current_figure, str):  # HTML from Plotly
            display(HTML(self._current_figure))
        else:  # Matplotlib figure
            display(self._current_figure)
```

## Key Features
- Support for Matplotlib, Plotly, and Pandas plotting interfaces
- Automatic backend detection for Matplotlib widget mode
- Preserved interactivity for both Plotly and Matplotlib
- Seamless integration with existing Syd parameter system

## Implementation Notes
- Plotly figures are converted to interactive HTML using CDN-based JavaScript
- Matplotlib widget mode (`%matplotlib widget`) retains full figure interactivity
- Backend detection ensures proper figure cleanup and display behavior
- All changes maintain backwards compatibility with existing Syd applications