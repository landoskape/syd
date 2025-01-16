from typing import Dict, Any, Tuple
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
from .parameters import (
    Parameter,
    TextParameter,
    SingleSelectionParameter,
    MultipleSelectionParameter,
    BooleanParameter,
    IntegerParameter,
    FloatParameter,
    IntegerPairParameter,
    FloatPairParameter,
)
from .interactive_viewer import InteractiveViewer


class NotebookDeployment:
    """
    Deployment system for InteractiveViewer in Jupyter notebooks using ipywidgets.
    Includes enhanced layout control and figure size management.
    """

    def __init__(
        self,
        viewer: InteractiveViewer,
        figsize: Tuple[float, float] = (8, 6),
        controls_position: str = "left",
        continuous=False,
    ):
        """Initialize with an InteractiveViewer instance."""
        self.viewer = viewer
        self.widgets: Dict[str, widgets.Widget] = {}
        self._widget_callbacks = {}
        self._current_figure = None

        # Default figure size
        self.fig_width = figsize[0]
        self.fig_height = figsize[1]
        if controls_position not in ["left", "right", "top", "bottom"]:
            raise ValueError(f"Invalid controls position: {controls_position}, must be one of ['left', 'right', 'top', 'bottom']")
        self.controls_position = controls_position
        self.horizontal_layout = controls_position in ["left", "right"]
        self.continuous = continuous

    def _create_text_widget(self, param: TextParameter) -> widgets.Text:
        """Create a text input widget."""
        w = widgets.Text(value=param.default, description=param.name, layout=widgets.Layout(width="95%"), style={"description_width": "initial"})
        return w

    def _create_selection_widget(self, param: SingleSelectionParameter) -> widgets.Dropdown:
        """Create a dropdown selection widget."""
        w = widgets.Dropdown(
            options=param.options,
            value=param.default if param.default else param.options[0],
            description=param.name,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )
        return w

    def _create_multiple_selection_widget(self, param: MultipleSelectionParameter) -> widgets.SelectMultiple:
        """Create a multiple selection widget."""
        w = widgets.SelectMultiple(
            options=param.options,
            value=param.default if param.default else [],
            description=param.name,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )
        return w

    def _create_boolean_widget(self, param: BooleanParameter) -> widgets.Checkbox:
        """Create a checkbox widget."""
        w = widgets.Checkbox(value=param.default, description=param.name, layout=widgets.Layout(width="95%"), style={"description_width": "initial"})
        return w

    def _create_integer_widget(self, param: IntegerParameter) -> widgets.IntSlider:
        """Create an integer slider widget."""
        w = widgets.IntSlider(
            value=param.default if param.default is not None else param.min_value,
            min=param.min_value,
            max=param.max_value,
            description=param.name,
            continuous_update=self.continuous,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )
        return w

    def _create_float_widget(self, param: FloatParameter) -> widgets.FloatSlider:
        """Create a float slider widget."""
        w = widgets.FloatSlider(
            value=param.default if param.default is not None else param.min_value,
            min=param.min_value,
            max=param.max_value,
            step=param.step,
            description=param.name,
            continuous_update=self.continuous,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )
        return w

    def _create_integer_pair_widget(self, param: IntegerPairParameter) -> widgets.HBox:
        """Create a pair of integer input widgets."""
        low = widgets.IntText(
            value=param.default[0],
            description=f"{param.name} (low)",
            layout=widgets.Layout(width="47%"),
            style={"description_width": "initial"},
        )
        high = widgets.IntText(
            value=param.default[1],
            description=f"{param.name} (high)",
            layout=widgets.Layout(width="47%"),
            style={"description_width": "initial"},
        )
        # Simply set attributes directly
        setattr(low, "_param_name", param.name)
        setattr(low, "_pair_type", "low")
        setattr(high, "_param_name", param.name)
        setattr(high, "_pair_type", "high")

        return widgets.VBox([low, high], layout=widgets.Layout(width="95%"))

    def _create_float_pair_widget(self, param: FloatPairParameter) -> widgets.HBox:
        """Create a pair of float input widgets."""
        low = widgets.FloatText(
            value=param.default[0],
            description=f"{param.name} (low)",
            layout=widgets.Layout(width="47%"),
            style={"description_width": "initial"},
        )
        high = widgets.FloatText(
            value=param.default[1],
            description=f"{param.name} (high)",
            layout=widgets.Layout(width="47%"),
            style={"description_width": "initial"},
        )
        # Simply set attributes directly
        setattr(low, "_param_name", param.name)
        setattr(low, "_pair_type", "low")
        setattr(high, "_param_name", param.name)
        setattr(high, "_pair_type", "high")

        return widgets.VBox([low, high], layout=widgets.Layout(width="95%"))

    def _create_widget_for_parameter(self, param: Parameter) -> widgets.Widget:
        """Create the appropriate widget based on parameter type."""
        widget_creators = {
            TextParameter: self._create_text_widget,
            SingleSelectionParameter: self._create_selection_widget,
            MultipleSelectionParameter: self._create_multiple_selection_widget,
            BooleanParameter: self._create_boolean_widget,
            IntegerParameter: self._create_integer_widget,
            FloatParameter: self._create_float_widget,
            IntegerPairParameter: self._create_integer_pair_widget,
            FloatPairParameter: self._create_float_pair_widget,
        }

        creator = widget_creators.get(type(param))
        if not creator:
            raise ValueError(f"Unsupported parameter type: {type(param)}")

        return creator(param)

    def _create_size_controls(self) -> widgets.VBox:
        """Create controls for adjusting the figure size."""
        self.width_slider = widgets.FloatSlider(
            value=self.fig_width,
            min=4,
            max=20,
            step=0.5,
            description="Figure Width",
            continuous_update=True,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

        self.height_slider = widgets.FloatSlider(
            value=self.fig_height,
            min=3,
            max=15,
            step=0.5,
            description="Figure Height",
            continuous_update=True,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

        if self.horizontal_layout:
            self.container_width = widgets.IntSlider(
                value=30,
                min=20,
                max=80,
                description="Controls Width %",
                continuous_update=True,
                layout=widgets.Layout(width="95%"),
                style={"description_width": "initial"},
            )

        # Add callbacks for size changes
        self.width_slider.observe(self._handle_size_change, names="value")
        self.height_slider.observe(self._handle_size_change, names="value")
        if self.horizontal_layout:
            self.container_width.observe(self._handle_container_width_change, names="value")

        # Widgets box
        widgets_to_box = [widgets.HTML("<b>Layout Controls</b>"), self.width_slider, self.height_slider]
        if self.horizontal_layout:
            widgets_to_box.append(self.container_width)
        return widgets.VBox(widgets_to_box, layout=widgets.Layout(margin="10px 0px"))

    def _handle_size_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to figure size."""
        self.fig_width = self.width_slider.value
        self.fig_height = self.height_slider.value
        self._current_fig.set_size_inches(self.fig_width, self.fig_height)
        self.plot_output.clear_output(wait=True)
        with self.plot_output:
            display(self._current_fig)

    def _handle_container_width_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to container widths."""
        controls_width = f"{self.container_width.value}%"
        plot_width = f"{100 - self.container_width.value}%"

        self.widgets_container.layout.width = controls_width
        self.plot_container.layout.width = plot_width

    def _handle_widget_change(self, name: str, change: Dict[str, Any]) -> None:
        """Handle widget value changes and update the viewer parameter."""
        # Check if this is a pair widget component
        if hasattr(change["owner"], "_param_name"):
            # This is part of a pair widget
            param_name = change["owner"]._param_name
            widget = self.widgets[param_name]
            low_value = widget.children[0].value
            high_value = widget.children[1].value
            value = (low_value, high_value)
            name = param_name  # Use the parameter name instead of the individual widget name
        else:
            value = change["new"]

        # Update the viewer parameter that the user just interacted with
        self.viewer.set_parameter_value(name, value)

        # Retrieve the new state of the viewer\
        # Which might have more changes due to callbacks
        state = self.viewer.get_state()

        # Detect and update any widgets affected by the new state
        for param_name, param_value in state.items():
            if param_name == name:
                # Skip the widget that triggered the change
                continue

            widget = self.widgets[param_name]
            if isinstance(widget, widgets.VBox) or isinstance(widget, widgets.HBox):
                current_value = (widget.children[0].value, widget.children[1].value)
                if param_value != current_value:
                    # Update pair widgets without triggering callbacks
                    for i, child in enumerate(widget.children):
                        child.unobserve(**self._widget_callbacks[param_name])
                        child.value = param_value[i]
                        child.observe(**self._widget_callbacks[param_name])
            else:
                if param_value != widget.value:
                    # Update single widgets without triggering callbacks
                    widget.unobserve(**self._widget_callbacks[param_name])
                    if hasattr(self.viewer.parameters[param_name], "options"):
                        widget.options = self.viewer.parameters[param_name].options
                    widget.value = param_value
                    widget.observe(**self._widget_callbacks[param_name])

        # Update the plot with the new state
        self._update_plot(state)

    def _update_plot(self, state: Dict[str, Any]) -> None:
        """Update the plot with current parameters and size."""
        self._current_fig.clear()
        self._current_fig.set_size_inches(self.fig_width, self.fig_height)
        plt.ioff()
        self._current_fig = self.viewer.plot(state=state)
        plt.close(self._current_fig)
        plt.ion()

        self.plot_output.clear_output(wait=True)
        with self.plot_output:
            display(self._current_fig)

    def create_widgets(self) -> None:
        """Create widgets for all parameters in the viewer."""
        for name, param in self.viewer.parameters.items():
            widget = self._create_widget_for_parameter(param)
            self.widgets[name] = widget
            callback = dict(handler=lambda change, n=name: self._handle_widget_change(n, change), names="value")
            self._widget_callbacks[name] = callback

            # Set up callback
            if isinstance(widget, (widgets.HBox, widgets.VBox)):
                # For pair widgets, observe both components
                widget.children[0].observe(**self._widget_callbacks[name])
                widget.children[1].observe(**self._widget_callbacks[name])
            else:
                widget.observe(**self._widget_callbacks[name])

    def display_widgets(self) -> None:
        """Display all widgets and plot in an organized layout."""
        # Create size controls
        size_controls = self._create_size_controls()

        # Create widgets container with parameters and size controls
        all_widgets = list(self.widgets.values()) + [size_controls]
        width = "30%" if self.controls_position in ["left", "right"] else "100%"
        self.widgets_container = widgets.VBox(all_widgets, layout=widgets.Layout(width=width, padding="10px", overflow_y="auto"))

        # Create output widget for plot
        self.plot_output = widgets.Output()
        width = "70%" if self.controls_position in ["left", "right"] else "100%"
        self.plot_container = widgets.VBox([self.plot_output], layout=widgets.Layout(width=width, padding="10px"))

        if self.controls_position == "left":
            layout = widgets.HBox(
                [self.widgets_container, self.plot_container], layout=widgets.Layout(width="100%", height="auto")  # Dynamic height based on content
            )
        elif self.controls_position == "right":
            layout = widgets.HBox(
                [self.plot_container, self.widgets_container], layout=widgets.Layout(width="100%", height="auto")  # Dynamic height based on content
            )
        elif self.controls_position == "top":
            layout = widgets.VBox([self.widgets_container, self.plot_container], layout=widgets.Layout(width="100%", height="auto"))
        elif self.controls_position == "bottom":
            layout = widgets.VBox([self.plot_container, self.widgets_container], layout=widgets.Layout(width="100%", height="auto"))
        else:
            raise ValueError(f"Invalid controls position: {self.controls_position}")
        display(layout)

        # Create initial plot
        # plt.close(self._current_fig)  # close the figure to prevent it from being displayed
        plt.ioff()
        self._current_fig = self.viewer.plot(state=self.viewer.get_state())
        plt.close(self._current_fig)
        plt.ion()
        with self.plot_output:
            display(self._current_fig)

    def deploy(self) -> None:
        """Create and display all widgets with proper deployment state management."""
        with self.viewer.deploy_app():
            self.create_widgets()
            self.display_widgets()
