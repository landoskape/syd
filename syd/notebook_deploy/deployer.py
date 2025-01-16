from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt

from ..interactive_viewer import InteractiveViewer
from .widgets import BaseParameterWidget, create_parameter_widget


@dataclass
class LayoutConfig:
    """Configuration for the viewer layout."""

    controls_position: str = "left"  # 'left', 'top'
    figure_width: float = 8.0
    figure_height: float = 6.0
    controls_width_percent: int = 30
    continuous_update: bool = False

    def __post_init__(self):
        valid_positions = ["left", "top"]
        if self.controls_position not in valid_positions:
            raise ValueError(f"Invalid controls position: {self.controls_position}. Must be one of {valid_positions}")

    @property
    def is_horizontal(self) -> bool:
        return self.controls_position == "left"


class NotebookDeployment:
    """
    A deployment system for InteractiveViewer in Jupyter notebooks using ipywidgets.
    Built around the parameter widget system for clean separation of concerns.
    """

    def __init__(self, viewer: InteractiveViewer, layout_config: Optional[LayoutConfig] = None):
        self.viewer = viewer
        self.config = layout_config or LayoutConfig()

        # Initialize containers
        self.parameter_widgets: Dict[str, BaseParameterWidget] = {}
        self.layout_widgets = self._create_layout_controls()
        self.plot_output = widgets.Output()

        # Store current figure
        self._current_figure = None

    def _create_layout_controls(self) -> Dict[str, widgets.Widget]:
        """Create widgets for controlling the layout."""
        controls = {}

        # Figure size controls
        controls["width"] = widgets.FloatSlider(
            value=self.config.figure_width,
            min=4,
            max=20,
            step=0.5,
            description="Figure Width",
            continuous_update=True,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

        controls["height"] = widgets.FloatSlider(
            value=self.config.figure_height,
            min=3,
            max=15,
            step=0.5,
            description="Figure Height",
            continuous_update=True,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

        # Controls width slider for horizontal layouts
        if self.config.is_horizontal:
            controls["container_width"] = widgets.IntSlider(
                value=self.config.controls_width_percent,
                min=20,
                max=80,
                description="Controls Width %",
                continuous_update=True,
                layout=widgets.Layout(width="95%"),
                style={"description_width": "initial"},
            )

        # Set up callbacks
        controls["width"].observe(self._handle_figure_size_change, names="value")
        controls["height"].observe(self._handle_figure_size_change, names="value")
        if self.config.is_horizontal:
            controls["container_width"].observe(self._handle_container_width_change, names="value")

        return controls

    def _create_parameter_widgets(self) -> None:
        """Create widget instances for all parameters."""
        for name, param in self.viewer.parameters.items():
            widget = create_parameter_widget(param)

            # Register callback for parameter changes
            widget.widget.observe(lambda change, n=name: self._handle_parameter_change(n, change), names="value")

            # Store in widget dict
            self.parameter_widgets[name] = widget

    def _handle_parameter_change(self, name: str, change: Dict[str, Any]) -> None:
        """Handle changes to parameter widgets."""
        # Update the changed parameter in the viewer
        self.viewer.set_parameter_value(name, change["new"])

        # Get new state which may include dependent parameter changes
        state = self.viewer.get_state()

        # Update any widgets that changed due to dependencies
        self._sync_widgets_with_state(state, exclude=name)

        # Update the plot
        self._update_plot()

    def _sync_widgets_with_state(self, state: Dict[str, Any], exclude: Optional[str] = None) -> None:
        """Sync widget values with viewer state."""
        for name, value in state.items():
            if name == exclude:
                continue

            widget = self.parameter_widgets[name]
            if widget.parameter.value != value:
                widget.update_from_parameter()

    def _handle_figure_size_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to figure dimensions."""
        if self._current_figure is None:
            return

        self.config.figure_width = self.layout_widgets["width"].value
        self.config.figure_height = self.layout_widgets["height"].value

        self._current_figure.set_size_inches(self.config.figure_width, self.config.figure_height)
        self._redraw_plot()

    def _handle_container_width_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to container width proportions."""
        width_percent = self.layout_widgets["container_width"].value
        self.config.controls_width_percent = width_percent

        # Update container widths
        self.widgets_container.layout.width = f"{width_percent}%"
        self.plot_container.layout.width = f"{100 - width_percent}%"

    def _update_plot(self) -> None:
        """Update the plot with current state."""
        state = self.viewer.get_state()

        plt.ioff()  # Turn off interactive mode temporarily
        new_fig = self.viewer.plot(state=state)
        new_fig.set_size_inches(self.config.figure_width, self.config.figure_height)
        plt.close(self._current_figure)  # Close old figure
        self._current_figure = new_fig
        plt.ion()  # Restore interactive mode

        self._redraw_plot()

    def _redraw_plot(self) -> None:
        """Clear and redraw the plot in the output widget."""
        self.plot_output.clear_output(wait=True)
        with self.plot_output:
            display(self._current_figure)

    def _create_layout(self) -> widgets.Widget:
        """Create the main layout combining controls and plot."""
        # Create layout controls section
        layout_box = widgets.VBox(
            [widgets.HTML("<b>Layout Controls</b>")] + list(self.layout_widgets.values()), layout=widgets.Layout(margin="10px 0px")
        )

        # Create parameter controls section
        param_box = widgets.VBox(
            [widgets.HTML("<b>Parameters</b>")] + [w.widget for w in self.parameter_widgets.values()], layout=widgets.Layout(margin="10px 0px")
        )

        # Combine all controls
        self.widgets_container = widgets.VBox(
            [param_box, layout_box],
            layout=widgets.Layout(
                width=f"{self.config.controls_width_percent}%" if self.config.is_horizontal else "100%", padding="10px", overflow_y="auto"
            ),
        )

        # Create plot container
        self.plot_container = widgets.VBox(
            [self.plot_output],
            layout=widgets.Layout(width=f"{100 - self.config.controls_width_percent}%" if self.config.is_horizontal else "100%", padding="10px"),
        )

        # Create final layout based on configuration
        if self.config.controls_position == "left":
            return widgets.HBox([self.widgets_container, self.plot_container])
        else:
            return widgets.VBox([self.widgets_container, self.plot_container])

    def deploy(self) -> None:
        """Deploy the interactive viewer with proper state management."""
        with self.viewer.deploy_app():
            # Create widgets
            self._create_parameter_widgets()

            # Create and display layout
            layout = self._create_layout()
            display(layout)

            # Create initial plot
            self._update_plot()
