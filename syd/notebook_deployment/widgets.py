from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Union, Callable
import ipywidgets as widgets

from ..parameters import (
    Parameter,
    TextParameter,
    SelectionParameter,
    MultipleSelectionParameter,
    BooleanParameter,
    IntegerParameter,
    FloatParameter,
    IntegerRangeParameter,
    FloatRangeParameter,
    UnboundedIntegerParameter,
    UnboundedFloatParameter,
    ButtonAction,
)

T = TypeVar("T", bound=Parameter[Any])
W = TypeVar("W", bound=widgets.Widget)


class BaseWidget(Generic[T, W], ABC):
    """
    Abstract base class for all parameter widgets.

    This class defines the common interface and shared functionality
    for widgets that correspond to different parameter types.
    """

    _widget: W
    _callbacks: List[Dict[str, Union[Callable, Union[str, List[str]]]]]
    is_action: bool = False

    def __init__(
        self,
        parameter: T,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ):
        self._widget = self._create_widget(
            parameter,
            width,
            margin,
            description_width,
        )
        self._updating = False  # Flag to prevent circular updates
        # List of callbacks to remember for quick disabling/enabling
        self._callbacks = []

    @abstractmethod
    def _create_widget(
        self,
        parameter: T,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> W:
        """Create and return the appropriate ipywidget."""
        pass

    @property
    def widget(self) -> W:
        """Get the underlying ipywidget."""
        return self._widget

    @property
    def value(self) -> Any:
        """Get the current value of the widget."""
        return self._widget.value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the value of the widget."""
        self._widget.value = new_value

    def matches_parameter(self, parameter: T) -> bool:
        """Check if the widget matches the parameter."""
        return self.value == parameter.value

    def update_from_parameter(self, parameter: T) -> None:
        """Update the widget from the parameter."""
        try:
            self._updating = True
            self.disable_callbacks()
            self.extra_updates_from_parameter(parameter)
            self.value = parameter.value
        finally:
            self.reenable_callbacks()
            self._updating = False

    def extra_updates_from_parameter(self, parameter: T) -> None:
        """Extra updates from the parameter."""
        pass

    def observe(self, callback: Callable) -> None:
        """Observe the widget and call the callback when the value changes."""
        full_callback = dict(handler=callback, names="value")
        self._widget.observe(**full_callback)
        self._callbacks.append(full_callback)

    def unobserve(self, callback: Callable[[Any], None]) -> None:
        """Unobserve the widget and stop calling the callback when the value changes."""
        full_callback = dict(handler=callback, names="value")
        self._widget.unobserve(**full_callback)
        self._callbacks.remove(full_callback)

    def reenable_callbacks(self) -> None:
        """Reenable all callbacks from the widget."""
        for callback in self._callbacks:
            self._widget.observe(**callback)

    def disable_callbacks(self) -> None:
        """Disable all callbacks from the widget."""
        for callback in self._callbacks:
            self._widget.unobserve(**callback)


class TextWidget(BaseWidget[TextParameter, widgets.Text]):
    """Widget for text parameters."""

    def _create_widget(
        self,
        parameter: TextParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.Text:
        return widgets.Text(
            value=parameter.value,
            description=parameter.name,
            continuous=False,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )


class BooleanWidget(BaseWidget[BooleanParameter, widgets.ToggleButton]):
    """Widget for boolean parameters."""

    def _create_widget(
        self,
        parameter: BooleanParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.ToggleButton:
        return widgets.ToggleButton(
            value=parameter.value,
            description=parameter.name,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )


class SelectionWidget(BaseWidget[SelectionParameter, widgets.Dropdown]):
    """Widget for single selection parameters."""

    def _create_widget(
        self,
        parameter: SelectionParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.Dropdown:
        return widgets.Dropdown(
            value=parameter.value,
            options=parameter.options,
            description=parameter.name,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )

    def matches_parameter(self, parameter: SelectionParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value and self._widget.options == parameter.options
        )

    def extra_updates_from_parameter(self, parameter: SelectionParameter) -> None:
        """Extra updates from the parameter."""
        new_options = parameter.options
        current_value = self._widget.value
        new_value = current_value if current_value in new_options else new_options[0]
        self._widget.options = new_options
        self._widget.value = new_value


class MultipleSelectionWidget(
    BaseWidget[MultipleSelectionParameter, widgets.SelectMultiple]
):
    """Widget for multiple selection parameters."""

    def _create_widget(
        self,
        parameter: MultipleSelectionParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.SelectMultiple:
        return widgets.SelectMultiple(
            value=parameter.value,
            options=parameter.options,
            description=parameter.name,
            rows=min(len(parameter.options), 4),
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )

    def matches_parameter(self, parameter: MultipleSelectionParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value and self._widget.options == parameter.options
        )

    def extra_updates_from_parameter(
        self, parameter: MultipleSelectionParameter
    ) -> None:
        """Extra updates from the parameter."""
        new_options = parameter.options
        current_values = set(self._widget.value)
        new_values = [v for v in current_values if v in new_options]
        self._widget.options = new_options
        self._widget.value = new_values


class IntegerWidget(BaseWidget[IntegerParameter, widgets.IntSlider]):
    """Widget for integer parameters."""

    def _create_widget(
        self,
        parameter: IntegerParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.IntSlider:
        """Create the integer slider widget."""
        return widgets.IntSlider(
            value=parameter.value,
            min=parameter.min,
            max=parameter.max,
            step=1,
            description=parameter.name,
            continuous_update=False,
            style={"description_width": description_width},
            layout=widgets.Layout(width=width, margin=margin),
        )

    def matches_parameter(self, parameter: IntegerParameter) -> bool:
        """Check if the widget values match the parameter."""
        return (
            self._widget.description == parameter.name
            and self._widget.value == parameter.value
            and self._widget.min == parameter.min
            and self._widget.max == parameter.max
        )

    def extra_updates_from_parameter(self, parameter: IntegerParameter) -> None:
        """Update the widget attributes from the parameter."""
        current_value = self._widget.value
        if parameter.min > self._widget.max:
            self._widget.max = parameter.min + 1
        if parameter.max < self._widget.min:
            self._widget.min = parameter.max - 1
        self._widget.min = parameter.min
        self._widget.max = parameter.max
        self.value = max(parameter.min, min(parameter.max, current_value))


class FloatWidget(BaseWidget[FloatParameter, widgets.FloatSlider]):
    """Widget for float parameters."""

    def _create_widget(
        self,
        parameter: FloatParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.FloatSlider:
        """Create the float slider widget."""
        return widgets.FloatSlider(
            value=parameter.value,
            min=parameter.min,
            max=parameter.max,
            step=parameter.step,
            description=parameter.name,
            continuous_update=False,
            style={"description_width": description_width},
            layout=widgets.Layout(width=width, margin=margin),
        )

    def matches_parameter(self, parameter: FloatParameter) -> bool:
        """Check if the widget values match the parameter."""
        return (
            self._widget.description == parameter.name
            and self._widget.value == parameter.value
            and self._widget.min == parameter.min
            and self._widget.max == parameter.max
            and self._widget.step == parameter.step
        )

    def extra_updates_from_parameter(self, parameter: FloatParameter) -> None:
        """Update the widget attributes from the parameter."""
        current_value = self._widget.value
        if parameter.min > self._widget.max:
            self._widget.max = parameter.min + 1
        if parameter.max < self._widget.min:
            self._widget.min = parameter.max - 1
        self._widget.min = parameter.min
        self._widget.max = parameter.max
        self._widget.step = parameter.step
        self.value = max(parameter.min, min(parameter.max, current_value))


class IntegerRangeWidget(BaseWidget[IntegerRangeParameter, widgets.IntRangeSlider]):
    """Widget for integer range parameters."""

    def _create_widget(
        self,
        parameter: IntegerRangeParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.IntRangeSlider:
        """Create the integer range slider widget."""
        low, high = parameter.value
        return widgets.IntRangeSlider(
            value=[low, high],
            min=parameter.min,
            max=parameter.max,
            step=1,
            description=parameter.name,
            continuous_update=False,
            style={"description_width": description_width},
            layout=widgets.Layout(width=width, margin=margin),
        )

    def matches_parameter(self, parameter: IntegerRangeParameter) -> bool:
        """Check if the widget values match the parameter."""
        low, high = parameter.value
        return (
            self._widget.description == parameter.name
            and self._widget.value[0] == low
            and self._widget.value[1] == high
            and self._widget.min == parameter.min
            and self._widget.max == parameter.max
        )

    def extra_updates_from_parameter(self, parameter: IntegerRangeParameter) -> None:
        """Update the widget attributes from the parameter."""
        low, high = self._widget.value
        if parameter.min > self._widget.max:
            self._widget.max = parameter.min + 1
        if parameter.max < self._widget.min:
            self._widget.min = parameter.max - 1
        self._widget.min = parameter.min
        self._widget.max = parameter.max
        # Ensure values stay within bounds
        low = max(parameter.min, min(parameter.max, low))
        high = max(parameter.min, min(parameter.max, high))
        self.value = [low, high]


class FloatRangeWidget(BaseWidget[FloatRangeParameter, widgets.FloatRangeSlider]):
    """Widget for float range parameters."""

    def _create_widget(
        self,
        parameter: FloatRangeParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.FloatRangeSlider:
        """Create the float range slider widget."""
        low, high = parameter.value
        return widgets.FloatRangeSlider(
            value=[low, high],
            min=parameter.min,
            max=parameter.max,
            step=parameter.step,
            description=parameter.name,
            continuous_update=False,
            style={"description_width": description_width},
            layout=widgets.Layout(width=width, margin=margin),
        )

    def matches_parameter(self, parameter: FloatRangeParameter) -> bool:
        """Check if the widget values match the parameter."""
        low, high = parameter.value
        return (
            self._widget.description == parameter.name
            and self._widget.value[0] == low
            and self._widget.value[1] == high
            and self._widget.min == parameter.min
            and self._widget.max == parameter.max
            and self._widget.step == parameter.step
        )

    def extra_updates_from_parameter(self, parameter: FloatRangeParameter) -> None:
        """Update the widget attributes from the parameter."""
        low, high = self._widget.value
        if parameter.min > self._widget.max:
            self._widget.max = parameter.min + 1
        if parameter.max < self._widget.min:
            self._widget.min = parameter.max - 1
        self._widget.min = parameter.min
        self._widget.max = parameter.max
        self._widget.step = parameter.step
        # Ensure values stay within bounds
        low = max(parameter.min, min(parameter.max, low))
        high = max(parameter.min, min(parameter.max, high))
        self.value = [low, high]


class UnboundedIntegerWidget(BaseWidget[UnboundedIntegerParameter, widgets.IntText]):
    """Widget for unbounded integer parameters."""

    def _create_widget(
        self,
        parameter: UnboundedIntegerParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.IntText:
        return widgets.IntText(
            value=parameter.value,
            description=parameter.name,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )

    def matches_parameter(self, parameter: UnboundedIntegerParameter) -> bool:
        """Check if the widget matches the parameter."""
        return self.value == parameter.value

    def extra_updates_from_parameter(
        self, parameter: UnboundedIntegerParameter
    ) -> None:
        """Extra updates from the parameter."""
        pass


class UnboundedFloatWidget(BaseWidget[UnboundedFloatParameter, widgets.FloatText]):
    """Widget for unbounded float parameters."""

    def _create_widget(
        self,
        parameter: UnboundedFloatParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.FloatText:
        return widgets.FloatText(
            value=parameter.value,
            step=parameter.step,
            description=parameter.name,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )

    def matches_parameter(self, parameter: UnboundedFloatParameter) -> bool:
        """Check if the widget matches the parameter."""
        return self.value == parameter.value

    def extra_updates_from_parameter(self, parameter: UnboundedFloatParameter) -> None:
        """Extra updates from the parameter."""
        self._widget.step = parameter.step


class ButtonWidget(BaseWidget[ButtonAction, widgets.Button]):
    """Widget for button parameters."""

    is_action: bool = True

    def _create_widget(
        self,
        parameter: ButtonAction,
        width: str = "auto",
        margin: str = "3px 0px",
        description_width: str = "initial",
    ) -> widgets.Button:
        button = widgets.Button(
            description=parameter.label,
            layout=widgets.Layout(width=width, margin=margin),
            style={"description_width": description_width},
        )
        return button

    def matches_parameter(self, parameter: ButtonAction) -> bool:
        """Check if the widget matches the parameter."""
        return self._widget.description == parameter.label

    def extra_updates_from_parameter(self, parameter: ButtonAction) -> None:
        """Extra updates from the parameter."""
        # Callbacks are handled in the deployer, so the only relevant update is the label
        self._widget.description = parameter.label

    def observe(self, callback: Callable) -> None:
        """Observe the widget and call the callback when the value changes."""
        if self._callbacks:
            raise ValueError("ButtonWidget already has a callback!")
        self._widget.on_click(callback)
        self._callbacks = callback

    def unobserve(self, callback: Callable) -> None:
        """Unobserve the widget and stop calling the callback when the value changes."""
        self._widget.on_click(callback, remove=True)
        self._callbacks = []

    def reenable_callbacks(self) -> None:
        """Reenable all callbacks from the widget."""
        self._widget.on_click(self._callbacks)

    def disable_callbacks(self) -> None:
        """Disable all callbacks from the widget."""
        self._widget.on_click(self._callbacks, remove=True)


def create_widget(
    parameter: Union[Parameter[Any], ButtonAction],
    width: str = "auto",
    margin: str = "3px 0px",
    description_width: str = "initial",
) -> BaseWidget[Union[Parameter[Any], ButtonAction], widgets.Widget]:
    """Create and return the appropriate widget for the given parameter.

    Parameters
    ----------
    parameter : Union[Parameter[Any], ButtonAction]
        The parameter to create a widget for.
    width : str, optional
        Width of the widget. Default is 'auto'.
    margin : str, optional
        Margin of the widget. Default is '3px 0px'.
    description_width : str, optional
        Width of the description label. Default is 'initial'.

    Returns
    -------
    BaseWidget[Union[Parameter[Any], ButtonAction], widgets.Widget]
        The appropriate widget instance for the given parameter type.

    Raises
    ------
    ValueError
        If no widget implementation exists for the given parameter type.
    """
    widget_map = {
        TextParameter: TextWidget,
        SelectionParameter: SelectionWidget,
        MultipleSelectionParameter: MultipleSelectionWidget,
        BooleanParameter: BooleanWidget,
        IntegerParameter: IntegerWidget,
        FloatParameter: FloatWidget,
        IntegerRangeParameter: IntegerRangeWidget,
        FloatRangeParameter: FloatRangeWidget,
        UnboundedIntegerParameter: UnboundedIntegerWidget,
        UnboundedFloatParameter: UnboundedFloatWidget,
        ButtonAction: ButtonWidget,
    }

    # Try direct type lookup first
    widget_class = widget_map.get(type(parameter))

    # If that fails, try matching by class name
    if widget_class is None:
        param_type_name = type(parameter).__name__
        for key_class, value_class in widget_map.items():
            if key_class.__name__ == param_type_name:
                widget_class = value_class
                break

    if widget_class is None:
        raise ValueError(
            f"No widget implementation for parameter type: {type(parameter)}\n"
            f"Parameter type name: {type(parameter).__name__}\n"
            f"Available types: {[k.__name__ for k in widget_map.keys()]}"
        )

    return widget_class(
        parameter,
        width=width,
        margin=margin,
        description_width=description_width,
    )
