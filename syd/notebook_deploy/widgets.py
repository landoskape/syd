from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Union, Tuple, Protocol, Callable
import ipywidgets as widgets
from typing_extensions import TypeVar

from ..parameters import (
    Parameter,
    TextParameter,
    SelectionParameter,
    MultipleSelectionParameter,
    BooleanParameter,
    NumericParameter,
    IntegerParameter,
    FloatParameter,
    IntegerPairParameter,
    FloatPairParameter,
    UnboundedIntegerParameter,
    UnboundedFloatParameter,
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

    def __init__(self, parameter: T):
        self._widget = self._create_widget(parameter)
        self._updating = False  # Flag to prevent circular updates
        self._callbacks = []  # List of callbacks to remember here for quick disabling / reenabling

    @abstractmethod
    def _create_widget(self, parameter: T) -> W:
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
            self.value = parameter.value
            self.extra_updates_from_parameter(parameter)
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

    def _create_widget(self, parameter: TextParameter) -> widgets.Text:
        return widgets.Text(value=parameter.value, description=parameter.name, continuous_update=False)


class SelectionParameterWidget(BaseParameterWidget[SelectionParameter, widgets.Dropdown]):
    """Widget for single selection parameters."""

    def _create_widget(self, parameter: SelectionParameter) -> widgets.Dropdown:
        return widgets.Dropdown(value=parameter.value, options=parameter.options, description=parameter.name)

    def matches_parameter(self, parameter: SelectionParameter) -> bool:
        """Check if the widget matches the parameter."""
        value_correct = self.value == parameter.value
        options_correct = self._widget.options == parameter.options
        return value_correct and options_correct

    def extra_updates_from_parameter(self, parameter: SelectionParameter) -> None:
        """Extra updates from the parameter."""
        new_options = parameter.options
        current_value = self._widget.value
        new_value = current_value if current_value in new_options else new_options[0]
        self._widget.options = new_options
        self._widget.value = new_value


class MultipleSelectionParameterWidget(BaseParameterWidget[MultipleSelectionParameter, widgets.SelectMultiple]):
    """Widget for multiple selection parameters."""

    def _create_widget(self, parameter: MultipleSelectionParameter) -> widgets.SelectMultiple:
        return widgets.SelectMultiple(
            value=parameter.value,
            options=parameter.options,
            description=parameter.name,
            rows=min(len(parameter.options), 4),
        )

    def matches_parameter(self, parameter: MultipleSelectionParameter) -> bool:
        """Check if the widget matches the parameter."""
        value_correct = self.value == parameter.value
        options_correct = self._widget.options == parameter.options
        return value_correct and options_correct

    def extra_updates_from_parameter(self, parameter: MultipleSelectionParameter) -> None:
        """Extra updates from the parameter."""
        new_options = parameter.options
        current_values = set(self._widget.value)
        new_values = [v for v in current_values if v in new_options]
        self._widget.options = new_options
        self._widget.value = new_values


class BooleanParameterWidget(BaseParameterWidget[BooleanParameter, widgets.Checkbox]):
    """Widget for boolean parameters."""

    def _create_widget(self, parameter: BooleanParameter) -> widgets.Checkbox:
        return widgets.Checkbox(value=parameter.value, description=parameter.name)


class NumericWidget(Protocol):
    """Protocol defining the interface for numeric widgets."""

    min: Union[int, float]
    max: Union[int, float]
    value: Union[int, float]


N = TypeVar("N", bound=NumericParameter[Any])
NW = TypeVar("NW", bound=NumericWidget)


class NumericParameterWidgetMixin(Generic[N, NW]):
    """Mixin class for numeric parameter widgets."""

    def matches_parameter(self, parameter: N) -> bool:
        """Check if the widget matches the parameter."""
        value_correct = self.value == parameter.value
        min_correct = self._widget.min == parameter.min_value
        max_correct = self._widget.max == parameter.max_value
        return value_correct and min_correct and max_correct

    def extra_updates_from_parameter(self, parameter: N) -> None:
        """Extra updates from the parameter."""
        current_value = self._widget.value
        self._widget.min = parameter.min_value
        self._widget.max = parameter.max_value

        # Clamp current value to new bounds
        self.value = max(parameter.min_value, min(parameter.max_value, current_value))


class IntegerParameterWidget(
    BaseParameterWidget[IntegerParameter, widgets.IntSlider],
    NumericParameterWidgetMixin[IntegerParameter, widgets.IntSlider],
):
    """Widget for integer parameters."""

    def _create_widget(self, parameter: IntegerParameter) -> widgets.IntSlider:
        return widgets.IntSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            description=parameter.name,
            continuous_update=False,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )


class FloatParameterWidget(
    BaseParameterWidget[FloatParameter, widgets.FloatSlider],
    NumericParameterWidgetMixin[FloatParameter, widgets.FloatSlider],
):
    """Widget for float parameters."""

    def _create_widget(self, parameter: FloatParameter) -> widgets.FloatSlider:
        return widgets.FloatSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            step=parameter.step,
            description=parameter.name,
            continuous_update=False,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )


class IntegerPairParameterWidget(
    BaseParameterWidget[IntegerPairParameter, widgets.IntRangeSlider],
    NumericParameterWidgetMixin[IntegerPairParameter, widgets.IntRangeSlider],
):
    """Widget for integer pair parameters using IntRangeSlider."""

    def _create_widget(self, parameter: IntegerPairParameter) -> widgets.IntRangeSlider:
        return widgets.IntRangeSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            description=parameter.name,
            continuous_update=False,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )


class FloatPairParameterWidget(
    BaseParameterWidget[FloatPairParameter, widgets.FloatRangeSlider],
    NumericParameterWidgetMixin[FloatPairParameter, widgets.FloatRangeSlider],
):
    """Widget for float pair parameters using FloatRangeSlider."""

    def _create_widget(self, parameter: FloatPairParameter) -> widgets.FloatRangeSlider:
        return widgets.FloatRangeSlider(
            value=parameter.value,
            min=parameter.min_value,
            max=parameter.max_value,
            step=parameter.step,
            description=parameter.name,
            continuous_update=False,
            layout=widgets.Layout(width="95%"),
            style={"description_width": "initial"},
        )


class UnboundedNumericParameterWidgetMixin(Generic[N, NW]):
    """Mixin class for unbounded numeric parameter widgets."""

    def extra_updates_from_parameter(self, parameter: N) -> None:
        """Update widget bounds if they exist."""
        if hasattr(self._widget, "min"):
            self._widget.min = parameter.min_value if parameter.min_value is not None else -float("inf")
        if hasattr(self._widget, "max"):
            self._widget.max = parameter.max_value if parameter.max_value is not None else float("inf")


class UnboundedIntegerParameterWidget(
    BaseParameterWidget[UnboundedIntegerParameter, widgets.BoundedIntText],
    UnboundedNumericParameterWidgetMixin[UnboundedIntegerParameter, widgets.BoundedIntText],
):
    """Widget for unbounded integer parameters using BoundedIntText."""

    def _create_widget(self, parameter: UnboundedIntegerParameter) -> widgets.BoundedIntText:
        return widgets.BoundedIntText(
            value=parameter.value,
            min=-(2**31) if parameter.min_value is None else parameter.min_value,
            max=2**31 - 1 if parameter.max_value is None else parameter.max_value,
            description=parameter.name,
            layout=widgets.Layout(width="200px"),
            style={"description_width": "initial"},
        )


class UnboundedFloatParameterWidget(
    BaseParameterWidget[UnboundedFloatParameter, widgets.BoundedFloatText],
    UnboundedNumericParameterWidgetMixin[UnboundedFloatParameter, widgets.BoundedFloatText],
):
    """Widget for unbounded float parameters using BoundedFloatText."""

    def _create_widget(self, parameter: UnboundedFloatParameter) -> widgets.BoundedFloatText:
        return widgets.BoundedFloatText(
            value=parameter.value,
            min=float("-inf") if parameter.min_value is None else parameter.min_value,
            max=float("inf") if parameter.max_value is None else parameter.max_value,
            step=parameter.step if parameter.step is not None else 0.01,
            description=parameter.name,
            layout=widgets.Layout(width="200px"),
            style={"description_width": "initial"},
        )


# Factory function to create the appropriate widget for a parameter
def create_parameter_widget(parameter: Parameter[Any]) -> BaseParameterWidget[Parameter[Any], widgets.Widget]:
    """Create and return the appropriate widget for the given parameter."""
    widget_map = {
        TextParameter: TextParameterWidget,
        SelectionParameter: SelectionParameterWidget,
        MultipleSelectionParameter: MultipleSelectionParameterWidget,
        BooleanParameter: BooleanParameterWidget,
        IntegerParameter: IntegerParameterWidget,
        FloatParameter: FloatParameterWidget,
        IntegerPairParameter: IntegerPairParameterWidget,
        FloatPairParameter: FloatPairParameterWidget,
        UnboundedIntegerParameter: UnboundedIntegerParameterWidget,
        UnboundedFloatParameter: UnboundedFloatParameterWidget,
    }

    widget_class = widget_map.get(type(parameter))
    if widget_class is None:
        raise ValueError(f"No widget implementation for parameter type: {type(parameter)}")

    return widget_class(parameter)
