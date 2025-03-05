from typing import Dict, Any, Optional
import warnings
from functools import wraps
from dataclasses import dataclass
from contextlib import contextmanager
from time import time

import ipywidgets as widgets
from IPython.display import display
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..parameters import ParameterUpdateWarning
from ..viewer import Viewer
from .widgets import BaseWidget, create_widget


@contextmanager
def _plot_context():
    plt.ioff()
    try:
        yield
    finally:
        plt.ion()


def get_backend_type():
    """
    Determines the current matplotlib backend type and returns relevant info
    """
    backend = mpl.get_backend().lower()

    if "inline" in backend:
        return "inline"
    elif "widget" in backend or "ipympl" in backend:
        return "widget"
    elif "qt" in backend:
        return "qt"
    else:
        return "other"


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


class NotebookDeployer:
    """
    A deployment system for Viewer in Jupyter notebooks using ipywidgets.
    Built around the parameter widget system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: str = "left",
        figure_width: float = 8.0,
        figure_height: float = 6.0,
        controls_width_percent: int = 30,
        continuous: bool = False,
        suppress_warnings: bool = False,
    ):
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
        self.backend_type = get_backend_type()
        if self.backend_type not in ["inline", "widget"]:
            warnings.warn(
                "The current backend is not supported. Please use %matplotlib widget or %matplotlib inline.\n"
                "The behavior of the viewer will almost definitely not work as expected."
            )
        self.parameter_widgets: Dict[str, BaseWidget] = {}
        self.plot_output = widgets.Output()

        # Create layout for controls
        self.layout_widgets = self._create_layout_controls()

        # Flag to prevent circular updates
        self._updating = False

        # Last figure to close when new figures are created
        self._last_figure = None

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

    @debounce(0.1)
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
                    parameter.callback(self.viewer.state)
                else:
                    self.viewer.set_parameter_value(name, widget.value)

                # Update any widgets that changed due to dependencies
                self._sync_widgets_with_state()

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
        state = self.viewer.state

        with _plot_context():
            figure = self.viewer.plot(state)

        # Close the last figure if it exists to keep matplotlib clean
        # (just moved this from after clear_output.... noting!)
        if self._last_figure is not None:
            plt.close(self._last_figure)

        self.plot_output.clear_output(wait=True)
        with self.plot_output:
            if self.backend_type == "inline":
                display(figure)

                # Also required to make sure a second figure window isn't opened
                plt.close(figure)

            elif self.backend_type == "widget":
                display(figure.canvas)

            else:
                raise ValueError(f"Unsupported backend type: {self.backend_type}")

        self._last_figure = figure

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
        self.backend_type = get_backend_type()

        # We used to use the deploy_app context, but notebook deployment works
        # differently because it's asynchronous and this doesn't really behave
        # as intended. (e.g. with self.viewer._deploy_app() ...)

        # Create widgets
        self._create_parameter_widgets()

        # Create and display layout
        self.layout = self._create_layout()
        display(self.layout)

        # Create initial plot
        self._update_plot()
