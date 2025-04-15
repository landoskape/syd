from typing import Literal
import warnings
from dataclasses import dataclass
import ipywidgets as widgets
from IPython.display import display
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..support import ParameterUpdateWarning
from ..viewer import Viewer
from ..deployer import Deployer
from .widgets import create_widget


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


class NotebookDeployer(Deployer):
    """
    A deployment system for Viewer in Jupyter notebooks using ipywidgets.
    Built around the parameter widget system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: Literal["left", "top", "right", "bottom"] = "left",
        controls_width_percent: int = 20,
        continuous: bool = False,
        suppress_warnings: bool = True,
    ):
        super().__init__(viewer, suppress_warnings)
        self.controls_position = controls_position
        self.controls_width_percent = controls_width_percent
        self.continuous = continuous

        # Initialize containers
        self.backend_type = get_backend_type()
        if self.backend_type not in ["inline", "widget"]:
            warnings.warn(
                f"The current backend ({self.backend_type}) is not supported. Please use %matplotlib widget or %matplotlib inline.\n"
                "The behavior of the viewer will almost definitely not work as expected!"
            )
        self._last_figure = None

    def build_components(self) -> None:
        """Create widget instances for all parameters and equip callbacks."""
        for name, param in self.viewer.parameters.items():
            widget = create_widget(param, continuous=self.continuous)
            self.components[name] = widget
            callback = lambda _, n=name: self.handle_component_engagement(n)
            widget.observe(callback)

    def build_layout(self) -> None:
        """Create the main layout combining controls and plot."""

        self.plot_output = widgets.Output()

        # Controls width slider for horizontal layouts
        self.controls = {}
        if self.controls_position in ["left", "right"]:
            self.controls["controls_width"] = widgets.IntSlider(
                value=self.controls_width_percent,
                min=10,
                max=50,
                description="Controls Width %",
                continuous=True,
                layout=widgets.Layout(width="95%"),
                style={"description_width": "initial"},
            )

        # Create parameter controls section
        param_box = widgets.VBox(
            [widgets.HTML("<b>Parameters</b>")]
            + [w.widget for w in self.components.values()],
            layout=widgets.Layout(margin="10px 0px"),
        )

        # Combine all controls
        if self.controls_position in ["left", "right"]:
            # Create layout controls section if horizontal (might include for vertical later when we have more permanent controls...)
            layout_box = widgets.VBox(
                [widgets.HTML("<b>Syd Controls</b>")] + list(self.controls.values()),
                layout=widgets.Layout(margin="10px 0px"),
            )

            # Register the controls_width slider's observer
            if "controls_width" in self.controls:
                self.controls["controls_width"].observe(
                    self._handle_container_width_change, names="value"
                )

            widgets_elements = [param_box, layout_box]
        else:
            widgets_elements = [param_box]

        self.widgets_container = widgets.VBox(
            widgets_elements,
            layout=widgets.Layout(
                width=(
                    f"{self.controls_width_percent}%"
                    if self.controls_position in ["left", "right"]
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
                    f"{100 - self.controls_width_percent}%"
                    if self.controls_position in ["left", "right"]
                    else "100%"
                ),
                padding="10px",
            ),
        )

        # Create final layout based on configuration
        if self.controls_position == "left":
            self.layout = widgets.HBox([self.widgets_container, self.plot_container])
        elif self.controls_position == "right":
            self.layout = widgets.HBox([self.plot_container, self.widgets_container])
        elif self.controls_position == "bottom":
            self.layout = widgets.VBox([self.plot_container, self.widgets_container])
        else:
            self.layout = widgets.VBox([self.widgets_container, self.plot_container])

    def display(self) -> None:
        """Display the layout -- pretty easy since it's just a widget layout in a notebook!"""
        self.backend_type = get_backend_type()
        display(self.layout)

    def display_new_plot(self, figure: mpl.figure.Figure) -> None:
        """Display a new plot."""
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

    def _handle_container_width_change(self, _) -> None:
        """Handle changes to container width proportions."""
        width_percent = self.controls["controls_width"].value
        self.controls_width_percent = width_percent

        # Update container widths
        self.widgets_container.layout.width = f"{width_percent}%"
        self.plot_container.layout.width = f"{100 - width_percent}%"
