from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
from dataclasses import dataclass
import ipywidgets as widgets
from traitlets import Any as TraitAny
from traitlets import Bool, Float, Int, List as TraitList, Unicode

from ..parameters import (
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

T = TypeVar("T")
W = TypeVar("W", bound=widgets.Widget)


class BaseParameterWidget(Generic[T, W], ABC):
    """
    Abstract base class for all parameter widgets.

    This class defines the common interface and shared functionality
    for widgets that correspond to different parameter types.
    """

    _widget: W

    def __init__(self, parameter: Parameter[T]):
        self.parameter = parameter
        self._widget = self._create_widget()
        self._updating = False  # Flag to prevent circular updates
        self._setup_observers()

    @abstractmethod
    def _create_widget(self) -> W:
        """Create and return the appropriate ipywidget."""
        pass

    def _setup_observers(self) -> None:
        """Set up two-way binding between parameter and widget."""
        # Observe widget changes
        self._widget.observe(self._handle_widget_change, names=["value"])

    def _handle_widget_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the widget value."""
        if self._updating:
            return

        try:
            self._updating = True
            new_value = change["new"]
            self.parameter.value = new_value
        finally:
            self._updating = False

    def update_from_parameter(self) -> None:
        """Update widget state to match parameter."""
        if self._updating:
            return

        try:
            self._updating = True
            self._widget.value = self.parameter.value
        finally:
            self._updating = False

    @property
    def widget(self) -> W:
        """Get the underlying ipywidget."""
        return self._widget


class TextParameterWidget(BaseParameterWidget[str, widgets.Text]):
    """Widget for text parameters."""

    def _create_widget(self) -> widgets.Text:
        return widgets.Text(value=self.parameter.value, description=self.parameter.name, continuous_update=False)


class SingleSelectionParameterWidget(BaseParameterWidget[Any, widgets.Dropdown]):
    """Widget for single selection parameters."""

    def _create_widget(self) -> widgets.Dropdown:
        param = self.parameter
        assert isinstance(param, SingleSelectionParameter)

        return widgets.Dropdown(value=param.value, options=param.options, description=param.name)

    def update_options(self, new_options: List[Any]) -> None:
        """Update the available options in the dropdown."""
        if self._updating:
            return

        try:
            self._updating = True
            current_value = self._widget.value
            self._widget.options = new_options

            # Try to maintain current value if it's still valid
            if current_value in new_options:
                self._widget.value = current_value
            else:
                self._widget.value = new_options[0]
        finally:
            self._updating = False


class MultipleSelectionParameterWidget(BaseParameterWidget[List[Any], widgets.SelectMultiple]):
    """Widget for multiple selection parameters."""

    def _create_widget(self) -> widgets.SelectMultiple:
        param = self.parameter
        assert isinstance(param, MultipleSelectionParameter)

        return widgets.SelectMultiple(value=param.value, options=param.options, description=param.name, rows=min(len(param.options), 5))

    def update_options(self, new_options: List[Any]) -> None:
        """Update the available options in the selection widget."""
        if self._updating:
            return

        try:
            self._updating = True
            current_values = set(self._widget.value)
            self._widget.options = new_options

            # Maintain valid current selections
            new_values = [v for v in current_values if v in new_options]
            self._widget.value = new_values
        finally:
            self._updating = False


class BooleanParameterWidget(BaseParameterWidget[bool, widgets.Checkbox]):
    """Widget for boolean parameters."""

    def _create_widget(self) -> widgets.Checkbox:
        return widgets.Checkbox(value=self.parameter.value, description=self.parameter.name)


class NumericParameterWidget(BaseParameterWidget[Union[int, float], Any], ABC):
    """Base class for numeric parameter widgets."""

    @abstractmethod
    def update_bounds(self, min_value: Union[int, float], max_value: Union[int, float]) -> None:
        """Update the minimum and maximum allowed values."""
        pass


class IntegerParameterWidget(NumericParameterWidget[int, widgets.IntSlider]):
    """Widget for integer parameters."""

    def _create_widget(self) -> widgets.IntSlider:
        param = self.parameter
        assert isinstance(param, IntegerParameter)

        return widgets.IntSlider(value=param.value, min=param.min_value, max=param.max_value, description=param.name, continuous_update=False)

    def update_bounds(self, min_value: int, max_value: int) -> None:
        """Update slider bounds while preserving value if possible."""
        if self._updating:
            return

        try:
            self._updating = True
            current_value = self._widget.value
            self._widget.min = min_value
            self._widget.max = max_value

            # Clamp current value to new bounds
            self._widget.value = max(min_value, min(max_value, current_value))
        finally:
            self._updating = False


class FloatParameterWidget(NumericParameterWidget[float, widgets.FloatSlider]):
    """Widget for float parameters."""

    def _create_widget(self) -> widgets.FloatSlider:
        param = self.parameter
        assert isinstance(param, FloatParameter)

        return widgets.FloatSlider(
            value=param.value, min=param.min_value, max=param.max_value, step=param.step, description=param.name, continuous_update=False
        )

    def update_bounds(self, min_value: float, max_value: float) -> None:
        """Update slider bounds while preserving value if possible."""
        if self._updating:
            return

        try:
            self._updating = True
            current_value = self._widget.value
            self._widget.min = min_value
            self._widget.max = max_value

            # Clamp current value to new bounds
            self._widget.value = max(min_value, min(max_value, current_value))
        finally:
            self._updating = False


class IntegerPairParameterWidget(BaseParameterWidget[tuple[int, int], widgets.HBox]):
    """Widget for integer pair parameters."""

    def _create_widget(self) -> widgets.HBox:
        param = self.parameter
        assert isinstance(param, IntegerPairParameter)

        self._low_slider = widgets.IntSlider(
            value=param.value[0], min=param.min_value, max=param.value[1], description=f"{param.name} (min)", continuous_update=False
        )

        self._high_slider = widgets.IntSlider(
            value=param.value[1], min=param.value[0], max=param.max_value, description=f"{param.name} (max)", continuous_update=False
        )

        # Link the sliders to maintain min <= max
        self._low_slider.observe(self._update_high_min, names=["value"])
        self._high_slider.observe(self._update_low_max, names=["value"])

        return widgets.HBox([self._low_slider, self._high_slider])

    def _update_high_min(self, change: Dict[str, Any]) -> None:
        """Update high slider's minimum when low slider changes."""
        self._high_slider.min = change["new"]

    def _update_low_max(self, change: Dict[str, Any]) -> None:
        """Update low slider's maximum when high slider changes."""
        self._low_slider.max = change["new"]

    def _handle_widget_change(self, change: Dict[str, Any]) -> None:
        """Override to handle changes from either slider."""
        if self._updating:
            return

        try:
            self._updating = True
            new_value = (self._low_slider.value, self._high_slider.value)
            self.parameter.value = new_value
        finally:
            self._updating = False


class FloatPairParameterWidget(BaseParameterWidget[tuple[float, float], widgets.HBox]):
    """Widget for float pair parameters."""

    def _create_widget(self) -> widgets.HBox:
        param = self.parameter
        assert isinstance(param, FloatPairParameter)

        self._low_slider = widgets.FloatSlider(
            value=param.value[0], min=param.min_value, max=param.value[1], step=param.step, description=f"{param.name} (min)", continuous_update=False
        )

        self._high_slider = widgets.FloatSlider(
            value=param.value[1], min=param.value[0], max=param.max_value, step=param.step, description=f"{param.name} (max)", continuous_update=False
        )

        # Link the sliders to maintain min <= max
        self._low_slider.observe(self._update_high_min, names=["value"])
        self._high_slider.observe(self._update_low_max, names=["value"])

        return widgets.HBox([self._low_slider, self._high_slider])

    def _update_high_min(self, change: Dict[str, Any]) -> None:
        """Update high slider's minimum when low slider changes."""
        self._high_slider.min = change["new"]

    def _update_low_max(self, change: Dict[str, Any]) -> None:
        """Update low slider's maximum when high slider changes."""
        self._low_slider.max = change["new"]

    def _handle_widget_change(self, change: Dict[str, Any]) -> None:
        """Override to handle changes from either slider."""
        if self._updating:
            return

        try:
            self._updating = True
            new_value = (self._low_slider.value, self._high_slider.value)
            self.parameter.value = new_value
        finally:
            self._updating = False


# Factory function to create the appropriate widget for a parameter
def create_parameter_widget(parameter: Parameter[Any]) -> BaseParameterWidget[Any, Any]:
    """Create and return the appropriate widget for the given parameter."""
    widget_map = {
        TextParameter: TextParameterWidget,
        SingleSelectionParameter: SingleSelectionParameterWidget,
        MultipleSelectionParameter: MultipleSelectionParameterWidget,
        BooleanParameter: BooleanParameterWidget,
        IntegerParameter: IntegerParameterWidget,
        FloatParameter: FloatParameterWidget,
        IntegerPairParameter: IntegerPairParameterWidget,
        FloatPairParameter: FloatPairParameterWidget,
    }

    widget_class = widget_map.get(type(parameter))
    if widget_class is None:
        raise ValueError(f"No widget implementation for parameter type: {type(parameter)}")

    return widget_class(parameter)
