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
    ButtonParameter,
)

T = TypeVar("T", bound=Parameter[Any])
W = TypeVar("W", bound=widgets.Widget)


class BaseParameterWidget(Generic[T, W], ABC):
    """
    Abstract base class for all parameter widgets.

    This class defines the common interface and shared functionality
    for widgets that correspond to different parameter types.
    """

    _widget: W
    _callbacks: List[Dict[str, Union[Callable, Union[str, List[str]]]]]

    def __init__(self, parameter: T, continuous_update: bool = False):
        self._widget = self._create_widget(parameter, continuous_update)
        self._updating = False  # Flag to prevent circular updates
        # List of callbacks to remember for quick disabling/enabling
        self._callbacks = []

    @abstractmethod
    def _create_widget(self, parameter: T, continuous_update: bool) -> W:
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


class TextParameterWidget(BaseParameterWidget[TextParameter, widgets.Text]):
    """Widget for text parameters."""

    def _create_widget(
        self, parameter: TextParameter, continuous_update: bool
    ) -> widgets.Text:
        return widgets.Text(
            value=parameter.value,
            description=parameter.name,
            continuous_update=continuous_update,
            layout=widgets.Layout(width="95%"),
        )


class BooleanParameterWidget(BaseParameterWidget[BooleanParameter, widgets.Checkbox]):
    """Widget for boolean parameters."""

    def _create_widget(
        self, parameter: BooleanParameter, continuous_update: bool
    ) -> widgets.Checkbox:
        return widgets.Checkbox(value=parameter.value, description=parameter.name)


class SelectionParameterWidget(
    BaseParameterWidget[SelectionParameter, widgets.Dropdown]
):
    """Widget for single selection parameters."""

    def _create_widget(
        self, parameter: SelectionParameter, continuous_update: bool
    ) -> widgets.Dropdown:
        return widgets.Dropdown(
            value=parameter.value,
            options=parameter.options,
            description=parameter.name,
            layout=widgets.Layout(width="95%"),
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


class MultipleSelectionParameterWidget(
    BaseParameterWidget[MultipleSelectionParameter, widgets.SelectMultiple]
):
    """Widget for multiple selection parameters."""

    def _create_widget(
        self, parameter: MultipleSelectionParameter, continuous_update: bool
    ) -> widgets.SelectMultiple:
        return widgets.SelectMultiple(
            value=parameter.value,
            options=parameter.options,
            description=parameter.name,
            rows=min(len(parameter.options), 4),
            layout=widgets.Layout(width="95%"),
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


class IntegerParameterWidget(BaseParameterWidget[IntegerParameter, widgets.IntSlider]):
    """Widget for integer parameters."""

    def _create_widget(
        self, parameter: IntegerParameter, continuous_update: bool
    ) -> widgets.IntSlider:
        return widgets.IntSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            description=parameter.name,
            continuous_update=continuous_update,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: IntegerParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value
            and self._widget.min == parameter.min_value
            and self._widget.max == parameter.max_value
        )

    def extra_updates_from_parameter(self, parameter: IntegerParameter) -> None:
        """Extra updates from the parameter."""
        current_value = self._widget.value
        self._widget.min = parameter.min_value
        self._widget.max = parameter.max_value
        self.value = max(parameter.min_value, min(parameter.max_value, current_value))


class FloatParameterWidget(BaseParameterWidget[FloatParameter, widgets.FloatSlider]):
    """Widget for float parameters."""

    def _create_widget(
        self, parameter: FloatParameter, continuous_update: bool
    ) -> widgets.FloatSlider:
        return widgets.FloatSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            step=parameter.step,
            description=parameter.name,
            continuous_update=continuous_update,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: FloatParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value
            and self._widget.min == parameter.min_value
            and self._widget.max == parameter.max_value
        )

    def extra_updates_from_parameter(self, parameter: FloatParameter) -> None:
        """Extra updates from the parameter."""
        current_value = self._widget.value
        self._widget.min = parameter.min_value
        self._widget.max = parameter.max_value
        self._widget.step = parameter.step
        self.value = max(parameter.min_value, min(parameter.max_value, current_value))


class IntegerRangeParameterWidget(
    BaseParameterWidget[IntegerRangeParameter, widgets.IntRangeSlider]
):
    """Widget for integer range parameters."""

    def _create_widget(
        self, parameter: IntegerRangeParameter, continuous_update: bool
    ) -> widgets.IntRangeSlider:
        return widgets.IntRangeSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            description=parameter.name,
            continuous_update=continuous_update,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: IntegerRangeParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value
            and self._widget.min == parameter.min_value
            and self._widget.max == parameter.max_value
        )

    def extra_updates_from_parameter(self, parameter: IntegerRangeParameter) -> None:
        """Extra updates from the parameter."""
        current_value = self._widget.value
        self._widget.min = parameter.min_value
        self._widget.max = parameter.max_value
        low, high = current_value
        low = max(parameter.min_value, min(parameter.max_value, low))
        high = max(parameter.min_value, min(parameter.max_value, high))
        self.value = (low, high)


class FloatRangeParameterWidget(
    BaseParameterWidget[FloatRangeParameter, widgets.FloatRangeSlider]
):
    """Widget for float range parameters."""

    def _create_widget(
        self, parameter: FloatRangeParameter, continuous_update: bool
    ) -> widgets.FloatRangeSlider:
        return widgets.FloatRangeSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            step=parameter.step,
            description=parameter.name,
            continuous_update=continuous_update,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: FloatRangeParameter) -> bool:
        """Check if the widget matches the parameter."""
        return (
            self.value == parameter.value
            and self._widget.min == parameter.min_value
            and self._widget.max == parameter.max_value
        )

    def extra_updates_from_parameter(self, parameter: FloatRangeParameter) -> None:
        """Extra updates from the parameter."""
        current_value = self._widget.value
        self._widget.min = parameter.min_value
        self._widget.max = parameter.max_value
        self._widget.step = parameter.step
        low, high = current_value
        low = max(parameter.min_value, min(parameter.max_value, low))
        high = max(parameter.min_value, min(parameter.max_value, high))
        self.value = (low, high)


class UnboundedIntegerParameterWidget(
    BaseParameterWidget[UnboundedIntegerParameter, widgets.BoundedIntText]
):
    """Widget for unbounded integer parameters."""

    def _create_widget(
        self, parameter: UnboundedIntegerParameter, continuous_update: bool
    ) -> widgets.BoundedIntText:
        return widgets.BoundedIntText(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            description=parameter.name,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: UnboundedIntegerParameter) -> bool:
        """Check if the widget matches the parameter."""
        return self.value == parameter.value

    def extra_updates_from_parameter(
        self, parameter: UnboundedIntegerParameter
    ) -> None:
        """Extra updates from the parameter."""
        if parameter.min_value is not None:
            self._widget.min = parameter.min_value
        if parameter.max_value is not None:
            self._widget.max = parameter.max_value


class UnboundedFloatParameterWidget(
    BaseParameterWidget[UnboundedFloatParameter, widgets.BoundedFloatText]
):
    """Widget for unbounded float parameters."""

    def _create_widget(
        self, parameter: UnboundedFloatParameter, continuous_update: bool
    ) -> widgets.BoundedFloatText:
        return widgets.BoundedFloatText(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            step=parameter.step,
            description=parameter.name,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )

    def matches_parameter(self, parameter: UnboundedFloatParameter) -> bool:
        """Check if the widget matches the parameter."""
        return self.value == parameter.value

    def extra_updates_from_parameter(self, parameter: UnboundedFloatParameter) -> None:
        """Extra updates from the parameter."""
        if parameter.min_value is not None:
            self._widget.min = parameter.min_value
        if parameter.max_value is not None:
            self._widget.max = parameter.max_value
        self._widget.step = parameter.step


class ButtonParameterWidget(BaseParameterWidget[ButtonParameter, widgets.Button]):
    """Widget for button parameters."""

    _is_button: bool = True

    def _create_widget(
        self, parameter: ButtonParameter, continuous_update: bool
    ) -> widgets.Button:
        button = widgets.Button(
            description=parameter.label,
            layout=widgets.Layout(width="auto"),
            style={"description_width": "initial"},
        )
        button.on_click(parameter.callback)
        return button

    def matches_parameter(self, parameter: ButtonParameter) -> bool:
        """Check if the widget matches the parameter."""
        return self._widget.description == parameter.label

    def extra_updates_from_parameter(self, parameter: ButtonParameter) -> None:
        """Extra updates from the parameter."""
        self._widget.description = parameter.label
        # Update click handler
        self._widget.on_click(parameter.callback, remove=True)  # Remove old handler
        self._widget.on_click(parameter.callback)  # Add new handler

    def observe(self, callback: Callable) -> None:
        """Observe the widget and call the callback when the value changes."""
        self._widget.on_click(callback)
        self._callbacks.append(callback)

    def unobserve(self, callback: Callable[[Any], None]) -> None:
        """Unobserve the widget and stop calling the callback when the value changes."""
        self._widget.on_click(None)
        self._callbacks.remove(callback)

    def reenable_callbacks(self) -> None:
        """Reenable all callbacks from the widget."""
        for callback in self._callbacks:
            self._widget.on_click(callback)

    def disable_callbacks(self) -> None:
        """Disable all callbacks from the widget."""
        for callback in self._callbacks:
            self._widget.on_click(None)


def create_parameter_widget(
    parameter: Parameter[Any],
    continuous_update: bool = False,
) -> BaseParameterWidget[Parameter[Any], widgets.Widget]:
    """Create and return the appropriate widget for the given parameter.

    Args:
        parameter: The parameter to create a widget for
        continuous_update: Whether to update the widget value continuously during user interaction
    """
    widget_map = {
        TextParameter: TextParameterWidget,
        SelectionParameter: SelectionParameterWidget,
        MultipleSelectionParameter: MultipleSelectionParameterWidget,
        BooleanParameter: BooleanParameterWidget,
        IntegerParameter: IntegerParameterWidget,
        FloatParameter: FloatParameterWidget,
        IntegerRangeParameter: IntegerRangeParameterWidget,
        FloatRangeParameter: FloatRangeParameterWidget,
        UnboundedIntegerParameter: UnboundedIntegerParameterWidget,
        UnboundedFloatParameter: UnboundedFloatParameterWidget,
        ButtonParameter: ButtonParameterWidget,
    }

    widget_class = widget_map.get(type(parameter))
    if widget_class is None:
        raise ValueError(
            f"No widget implementation for parameter type: {type(parameter)}"
        )

    return widget_class(parameter, continuous_update)
