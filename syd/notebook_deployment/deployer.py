from typing import Dict, Any, Optional
import warnings
from functools import wraps
from dataclasses import dataclass
from contextlib import contextmanager
from time import time

import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt

from ..parameters import ParameterUpdateWarning
from ..interactive_viewer import InteractiveViewer
from .widgets import BaseWidget, create_widget


@contextmanager
def _plot_context():
    plt.ioff()
    try:
        yield
    finally:
        plt.ion()


# TODO:
# Probably make this dependent on whether the user is in %matplotlib widget mode or not
# Also probably make it dependent on whether the deployer is in continuous mode or not
# Potentially make the wait_time dynamic depending on how fast the plot method is and how
# frequently the no comm messages show up... (if we can catch them)
def debounce(wait_time):
    """
    Decorator to prevent a function from being called more than once every wait_time seconds.
    """

    def decorator(fn):
        last_called = [0.0]  # Using list to maintain state in closure

        @wraps(fn)
        def debounced(*args, **kwargs):
            current_time = time()
            if current_time - last_called[0] >= wait_time:
                fn(*args, **kwargs)
                last_called[0] = current_time

        return debounced

    return decorator


@dataclass
class LayoutConfig:
    """Configuration for the viewer layout."""

    controls_position: str = "left"  # Options are: 'left', 'top', 'right', 'bottom'
    figure_width: float = 8.0
    figure_height: float = 6.0
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


class NotebookDeployment:
    """
    A deployment system for InteractiveViewer in Jupyter notebooks using ipywidgets.
    Built around the parameter widget system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: InteractiveViewer,
        controls_position: str = "left",
        figure_width: float = 8.0,
        figure_height: float = 6.0,
        controls_width_percent: int = 30,
        continuous: bool = False,
        suppress_warnings: bool = False,
    ):
        if not isinstance(viewer, InteractiveViewer):  # type: ignore
            raise TypeError(
                f"viewer must be an InteractiveViewer, got {type(viewer).__name__}"
            )

        self.viewer = viewer
        self.config = LayoutConfig(
            controls_position=controls_position,
            figure_width=figure_width,
            figure_height=figure_height,
            controls_width_percent=controls_width_percent,
        )
        self.continuous = continuous
        self.suppress_warnings = suppress_warnings

        # Initialize containers
        self.parameter_widgets: Dict[str, BaseWidget] = {}
        self.layout_widgets = self._create_layout_controls()
        self.plot_output = widgets.Output()

        # Store current figure
        self._current_figure = None
        # Flag to prevent circular updates
        self._updating = False

    def _create_layout_controls(self) -> Dict[str, widgets.Widget]:
        """Create widgets for controlling the layout."""
        controls: Dict[str, widgets.Widget] = {}

        # Controls width slider for horizontal layouts
        if self.config.is_horizontal:
            controls["controls_width"] = widgets.IntSlider(
                value=self.config.controls_width_percent,
                min=20,
                max=80,
                description="Controls Width %",
                continuous=True,
                layout=widgets.Layout(width="95%"),
                style={"description_width": "initial"},
            )
            controls["controls_width"].observe(
                self._handle_container_width_change, names="value"
            )

        return controls

    def _create_parameter_widgets(self) -> None:
        """Create widget instances for all parameters."""
        for name, param in self.viewer.parameters.items():
            widget = create_widget(
                param,
                continuous=self.continuous,
            )

            # Store in widget dict
            self.parameter_widgets[name] = widget

    @debounce(0.2)
    def _handle_widget_engagement(self, name: str) -> None:
        """Handle engagement with an interactive widget."""
        if self._updating:
            print(
                "Already updating -- there's a circular dependency!"
                "This is probably caused by failing to disable callbacks for a parameter."
                "It's a bug --- tell the developer on github issues please."
            )
            return

        try:
            self._updating = True

            # Optionally suppress warnings during parameter updates
            with warnings.catch_warnings():
                if self.suppress_warnings:
                    warnings.filterwarnings("ignore", category=ParameterUpdateWarning)

                widget = self.parameter_widgets[name]

                if widget._is_action:
                    parameter = self.viewer.parameters[name]
                    parameter.callback(self.viewer.get_state())
                else:
                    self.viewer.set_parameter_value(name, widget.value)

                # Update any widgets that changed due to dependencies
                self._sync_widgets_with_state(exclude=name)

                # Update the plot
                self._update_plot()

        finally:
            self._updating = False

    def _handle_action(self, name: str) -> None:
        """Handle actions for parameter widgets."""

    def _sync_widgets_with_state(self, exclude: Optional[str] = None) -> None:
        """Sync widget values with viewer state."""
        for name, parameter in self.viewer.parameters.items():
            if name == exclude:
                continue

            widget = self.parameter_widgets[name]
            if not widget.matches_parameter(parameter):
                widget.update_from_parameter(parameter)

    def _handle_figure_size_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to figure dimensions."""
        if self._current_figure is None:
            return

        self._redraw_plot()

    def _handle_container_width_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to container width proportions."""
        width_percent = self.layout_widgets["controls_width"].value
        self.config.controls_width_percent = width_percent

        # Update container widths
        self.widgets_container.layout.width = f"{width_percent}%"
        self.plot_container.layout.width = f"{100 - width_percent}%"

    def _update_plot(self) -> None:
        """Update the plot with current state."""
        state = self.viewer.get_state()

        with _plot_context():
            new_fig = self.viewer.plot(state)
            plt.close(self._current_figure)  # Close old figure
            self._current_figure = new_fig

        self._redraw_plot()

    def _redraw_plot(self) -> None:
        """Clear and redraw the plot in the output widget."""
        self.plot_output.clear_output(wait=True)
        with self.plot_output:
            display(self._current_figure)

    def _create_layout(self) -> widgets.Widget:
        """Create the main layout combining controls and plot."""
        # Set up parameter widgets with their observe callbacks
        for name, widget in self.parameter_widgets.items():
            widget.observe(lambda change, n=name: self._handle_widget_engagement(n))

        # Create parameter controls section
        param_box = widgets.VBox(
            [widgets.HTML("<b>Parameters</b>")]
            + [w.widget for w in self.parameter_widgets.values()],
            layout=widgets.Layout(margin="10px 0px"),
        )

        # Combine all controls
        if self.config.is_horizontal:
            # Create layout controls section if horizontal (might include for vertical later when we have more permanent controls...)
            layout_box = widgets.VBox(
                [widgets.HTML("<b>Layout Controls</b>")]
                + list(self.layout_widgets.values()),
                layout=widgets.Layout(margin="10px 0px"),
            )
            widgets_elements = [param_box, layout_box]
        else:
            widgets_elements = [param_box]

        self.widgets_container = widgets.VBox(
            widgets_elements,
            layout=widgets.Layout(
                width=(
                    f"{self.config.controls_width_percent}%"
                    if self.config.is_horizontal
                    else "100%"
                ),
                padding="10px",
                overflow_y="scroll",
                border="1px solid #e5e7eb",
                border_radius="4px 4px 0px 0px",
            ),
        )

        # Create plot container
        self.plot_container = widgets.VBox(
            [self.plot_output],
            layout=widgets.Layout(
                width=(
                    f"{100 - self.config.controls_width_percent}%"
                    if self.config.is_horizontal
                    else "100%"
                ),
                padding="10px",
            ),
        )

        # Create final layout based on configuration
        if self.config.controls_position == "left":
            return widgets.HBox([self.widgets_container, self.plot_container])
        elif self.config.controls_position == "right":
            return widgets.HBox([self.plot_container, self.widgets_container])
        elif self.config.controls_position == "bottom":
            return widgets.VBox([self.plot_container, self.widgets_container])
        else:
            return widgets.VBox([self.widgets_container, self.plot_container])

    def deploy(self) -> None:
        """Deploy the interactive viewer with proper state management."""
        with self.viewer._deploy_app():
            # Create widgets
            self._create_parameter_widgets()

            # Create and display layout
            self.layout = self._create_layout()
            display(self.layout)

            # Create initial plot
            self._update_plot()
