from typing import Literal, Optional
import warnings
from contextlib import contextmanager
from io import BytesIO
import ipywidgets as widgets
from IPython.display import display
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..support import ParameterUpdateWarning, plot_context
from ..viewer import Viewer
from .widgets import create_widget, BaseWidget


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


class NotebookDeployer:
    """
    A deployment system for Viewer in Jupyter notebooks using ipywidgets.
    Built around the parameter widget system for clean separation of concerns.
    """

    def __init__(
        self,
        viewer: Viewer,
        controls_position: Literal["left", "top", "right", "bottom"] = "left",
        controls_width_percent: int = 20,
        suppress_warnings: bool = True,
        update_threshold: float = 1.0,
    ):
        self.viewer = viewer
        self.components: dict[str, BaseWidget] = {}
        self.suppress_warnings = suppress_warnings
        self._updating = False  # Flag to check circular updates
        self.controls_position = controls_position
        self.controls_width_percent = controls_width_percent

        # Initialize containers
        self.backend_type = get_backend_type()
        if self.backend_type not in ["inline", "widget"]:
            warnings.warn(
                f"The current backend ({self.backend_type}) is not supported. Please use %matplotlib widget or %matplotlib inline.\n"
                "The behavior of the viewer will almost definitely not work as expected!"
            )
        self._last_figure = None
        self.update_threshold = update_threshold

    def _show_loading_indicator(self) -> None:
        """Start a browser-side spinner without replacing the current plot."""
        delay = max(0.0, float(self.update_threshold))
        self.loading_indicator.value = f"""
        <style>
            @keyframes syd-spinner-rotate {{
                to {{ transform: rotate(360deg); }}
            }}
            @keyframes syd-spinner-reveal {{
                to {{ opacity: 1; }}
            }}
            .syd-loading-indicator {{
                align-items: center;
                animation: syd-spinner-reveal 0s linear {delay}s forwards;
                color: #555;
                display: flex;
                font-size: 13px;
                gap: 8px;
                opacity: 0;
            }}
            .syd-loading-spinner {{
                animation: syd-spinner-rotate 0.8s linear infinite;
                border: 3px solid #d9d9d9;
                border-radius: 50%;
                border-top-color: #3b82f6;
                box-sizing: border-box;
                height: 18px;
                width: 18px;
            }}
        </style>
        <div class="syd-loading-indicator" role="status" aria-live="polite">
            <span class="syd-loading-spinner" aria-hidden="true"></span>
            <span>Updating plot…</span>
        </div>
        """

    def _hide_loading_indicator(self) -> None:
        """Remove the spinner, including a reveal that has not fired yet."""
        self.loading_indicator.value = ""

    @contextmanager
    def _perform_update(self, show_loading: bool = True):
        self._updating = True
        if show_loading:
            self._show_loading_indicator()

        try:
            yield
        finally:
            self._updating = False
            self._hide_loading_indicator()
            self._update_status("Ready!")

    def deploy(self) -> None:
        """Deploy the viewer."""
        self.backend_type = get_backend_type()
        self.build_components()
        self.build_layout()
        display(self.layout)
        self.update_plot()

    def build_components(self) -> None:
        """Create widget instances for all parameters and equip callbacks."""
        for name, param in self.viewer.parameters.items():
            widget = create_widget(param)
            self.components[name] = widget
            callback = lambda _, n=name: self.handle_component_engagement(n)
            widget.observe(callback)

    def build_layout(self) -> None:
        """Create the main layout combining controls and plot."""

        # Inline figures are rendered into one persistent Image widget. Unlike an
        # Output widget, replacing Image.value cannot accumulate display records.
        self.plot_image = widgets.Image(
            format="png",
            layout=widgets.Layout(align_self="flex-start", max_width="100%"),
        )
        self.plot_output = widgets.Output()
        plot_widget = (
            self.plot_image if self.backend_type == "inline" else self.plot_output
        )
        self.loading_indicator = widgets.HTML(
            value="",
            layout=widgets.Layout(height="28px"),
        )

        # Controls width slider for horizontal layouts
        self.controls = {}
        self.controls["status"] = widgets.HTML(
            value="<b>Syd Controls</b>",
            layout=widgets.Layout(width="95%"),
        )
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
        if self.backend_type == "inline":
            self.controls["update_threshold"] = widgets.FloatSlider(
                value=self.update_threshold,
                min=0.1,
                max=10.0,
                description="Loading Delay",
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
                list(self.controls.values()),
                layout=widgets.Layout(margin="10px 0px"),
            )

            # Register the controls_width slider's observer
            if "controls_width" in self.controls:
                self.controls["controls_width"].observe(
                    self._handle_container_width_change, names="value"
                )

            if "update_threshold" in self.controls:
                self.controls["update_threshold"].observe(
                    self._handle_update_threshold_change, names="value"
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
            [self.loading_indicator, plot_widget],
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

        self._update_status("Ready!")

    def handle_component_engagement(self, name: str) -> None:
        """Handle engagement with an interactive component."""
        if self._updating:
            print(
                "Already updating -- there's a circular dependency!"
                "This is probably caused by failing to disable callbacks for a parameter."
                "It's a bug --- tell the developer on github issues please."
            )
            return

        component = self.components[name]
        if component.is_action:
            will_replot = self.viewer.parameters[name].replot
        else:
            will_replot = True

        with self._perform_update(show_loading=will_replot):
            self._update_status(f"Updating {name}")
            # Optionally suppress warnings during parameter updates
            with warnings.catch_warnings():
                if self.suppress_warnings:
                    warnings.filterwarnings("ignore", category=ParameterUpdateWarning)

                # Get the component
                if component.is_action:
                    # If the component is an action, call the callback
                    parameter = self.viewer.parameters[name]
                    parameter.callback(self.viewer.state)
                    replot = parameter.replot
                else:
                    # Otherwise, update the parameter value
                    self.viewer.set_parameter_value(name, component.value)
                    replot = True

                # Update any components that changed due to dependencies
                self.sync_components_with_state()

                # Update the plot
                if replot:
                    self.update_plot()

    def sync_components_with_state(self, exclude: Optional[str] = None) -> None:
        """Sync component values with viewer state."""
        for name, parameter in self.viewer.parameters.items():
            if name == exclude:
                continue

            component = self.components[name]
            if not component.matches_parameter(parameter):
                component.update_from_parameter(parameter)

    def update_plot(self) -> None:
        """Update the plot with current state."""
        state = self.viewer.state

        with plot_context():
            figure = self.viewer.plot(state)
            self.viewer._figure = figure

        # Update components if plot function updated a parameter
        self.sync_components_with_state()

        self._display_figure(figure)

    def _display_figure(self, figure: plt.Figure) -> None:
        # Closing the Python figure does not remove its already-rendered notebook
        # output, so the previous plot remains visible until the replacement arrives.
        if self._last_figure is not None:
            plt.close(self._last_figure)

        if self.backend_type == "inline":
            image_buffer = BytesIO()
            render_dpi = figure.dpi * 2
            try:
                figure.savefig(
                    image_buffer,
                    format="png",
                    bbox_inches="tight",
                    dpi=render_dpi,
                )
                image_data = image_buffer.getvalue()
                # PNG stores its pixel width in bytes 16:20. Rendering at 2x and
                # displaying at half that width matches IPython's Retina formatter,
                # including the dimensions produced by bbox_inches="tight".
                pixel_width = int.from_bytes(image_data[16:20], byteorder="big")
                self.plot_image.value = image_data
                self.plot_image.layout.width = f"{pixel_width / 2:g}px"
            finally:
                plt.close(figure)

        else:
            self.plot_output.clear_output(wait=True)
            with self.plot_output:
                if self.backend_type == "widget":
                    display(figure.canvas)
                else:
                    display(figure)
                    plt.close(figure)
                    print(
                        f"Backend type: ({self.backend_type}) is not explicitly supported."
                        "If you encounter weird behavior, try restarting with '%matplotlib inline' or '%matplotlib widget'."
                        "And please report this issue on github please :)."
                    )

        self._last_figure = figure

    def _handle_container_width_change(self, _) -> None:
        """Handle changes to container width proportions."""
        width_percent = self.controls["controls_width"].value
        self.controls_width_percent = width_percent

        # Update container widths
        self.widgets_container.layout.width = f"{width_percent}%"
        self.plot_container.layout.width = f"{100 - width_percent}%"

    def _handle_update_threshold_change(self, _) -> None:
        """Handle changes to update threshold."""
        self.update_threshold = self.controls["update_threshold"].value

    def _update_status(self, status: str) -> None:
        """Update the status text."""
        value = "<b>Syd Controls</b>  "
        value += "<span style='background-color: #e0e0e0; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 90%;'>"
        value += f"Status: {status}"
        value += "</span>"
        self.controls["status"].value = value
