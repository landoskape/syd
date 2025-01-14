from typing import Dict, Any
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

    This class creates appropriate ipywidgets for each parameter type and handles
    callback management between the widgets and the viewer.
    """

    def __init__(self, viewer: InteractiveViewer):
        """Initialize with an InteractiveViewer instance."""
        self.viewer = viewer
        self.widgets: Dict[str, widgets.Widget] = {}
        self._widget_callbacks = {}

    def _create_text_widget(self, param: TextParameter) -> widgets.Text:
        """Create a text input widget."""
        w = widgets.Text(value=param.default, description=param.name, style={"description_width": "initial"})
        return w

    def _create_selection_widget(self, param: SingleSelectionParameter) -> widgets.Dropdown:
        """Create a dropdown selection widget."""
        w = widgets.Dropdown(
            options=param.options,
            value=param.default if param.default else param.options[0],
            description=param.name,
            style={"description_width": "initial"},
        )
        return w

    def _create_multiple_selection_widget(self, param: MultipleSelectionParameter) -> widgets.SelectMultiple:
        """Create a multiple selection widget."""
        w = widgets.SelectMultiple(
            options=param.options, value=param.default if param.default else [], description=param.name, style={"description_width": "initial"}
        )
        return w

    def _create_boolean_widget(self, param: BooleanParameter) -> widgets.Checkbox:
        """Create a checkbox widget."""
        w = widgets.Checkbox(value=param.default, description=param.name, style={"description_width": "initial"})
        return w

    def _create_integer_widget(self, param: IntegerParameter) -> widgets.IntSlider:
        """Create an integer slider widget."""
        w = widgets.IntSlider(
            value=param.default if param.default is not None else param.min_value,
            min=param.min_value,
            max=param.max_value,
            description=param.name,
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
            style={"description_width": "initial"},
        )
        return w

    def _create_integer_pair_widget(self, param: IntegerPairParameter) -> widgets.HBox:
        """Create a pair of integer input widgets."""
        low = widgets.IntText(
            value=param.default_low if param.default_low is not None else param.min_value,
            description=f"{param.name} (low)",
            style={"description_width": "initial"},
        )
        high = widgets.IntText(
            value=param.default_high if param.default_high is not None else param.max_value,
            description=f"{param.name} (high)",
            style={"description_width": "initial"},
        )
        return widgets.HBox([low, high])

    def _create_float_pair_widget(self, param: FloatPairParameter) -> widgets.HBox:
        """Create a pair of float input widgets."""
        low = widgets.FloatText(
            value=param.default_low if param.default_low is not None else param.min_value,
            description=f"{param.name} (low)",
            style={"description_width": "initial"},
        )
        high = widgets.FloatText(
            value=param.default_high if param.default_high is not None else param.max_value,
            description=f"{param.name} (high)",
            style={"description_width": "initial"},
        )
        return widgets.HBox([low, high])

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

    def _handle_widget_change(self, name: str, change: Dict[str, Any]) -> None:
        """Handle widget value changes and update the viewer parameter."""
        if isinstance(self.widgets[name], widgets.HBox):
            # Handle pair widgets
            low_value = self.widgets[name].children[0].value
            high_value = self.widgets[name].children[1].value
            value = (low_value, high_value)
        else:
            value = change["new"]

        with self.viewer.deploy_app():
            self.viewer.set_parameter_value(name, value)
            # Clear previous plot and display new one in the output widget
            self.plot_output.clear_output(wait=True)
            with self.plot_output:
                fig = self.viewer.plot(state=self.viewer.param_dict())
                display(fig)

    def create_widgets(self) -> None:
        """Create widgets for all parameters in the viewer."""
        for name, param in self.viewer.parameters.items():
            widget = self._create_widget_for_parameter(param)
            self.widgets[name] = widget

            # Set up callback
            if isinstance(widget, widgets.HBox):
                # For pair widgets, observe both components
                widget.children[0].observe(lambda change, n=name: self._handle_widget_change(n, change), names="value")
                widget.children[1].observe(lambda change, n=name: self._handle_widget_change(n, change), names="value")
            else:
                widget.observe(lambda change, n=name: self._handle_widget_change(n, change), names="value")

    def display_widgets(self) -> None:
        """Display all widgets and plot in an organized layout."""
        # Create initial plot
        initial_plot = self.viewer.plot(state=self.viewer.param_dict())

        # Create output widget for plot
        self.plot_output = widgets.Output()
        with self.plot_output:
            display(initial_plot)

        # Create widgets container
        widgets_container = widgets.VBox(list(self.widgets.values()))

        # Combine widgets and plot in layout
        layout = widgets.HBox([widgets_container, self.plot_output])  # Side by side
        # Or use VBox for widgets above plot:
        # layout = widgets.VBox([widgets_container, self.plot_output])

        display(layout)

    def deploy(self) -> None:
        """Create and display all widgets with proper deployment state management."""
        with self.viewer.deploy_app():
            self.create_widgets()
            self.display_widgets()
