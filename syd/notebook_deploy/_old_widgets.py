from typing import Any, Dict, Generic, List, Tuple, TypeVar, Protocol, runtime_checkable
from abc import ABC, abstractmethod
import ipywidgets as widgets
from dataclasses import dataclass

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


@runtime_checkable
class WidgetProtocol(Protocol):
    """Protocol defining the interface for parameter widgets."""

    @property
    def value(self) -> Any: ...

    @value.setter
    def value(self, new_value: Any) -> None: ...


class BaseParameterWidget(Generic[T], ABC):
    """Base class for parameter widgets."""

    def __init__(self, parameter: Parameter[T], continuous_update: bool = False):
        self.parameter = parameter
        self.continuous_update = continuous_update
        self._widget = self._create_widget()
        self._setup_widget()

    @abstractmethod
    def _create_widget(self) -> WidgetProtocol:
        """Create the specific widget for this parameter type."""
        pass

    def _setup_widget(self):
        """Configure common widget properties."""
        if isinstance(self._widget, widgets.Widget):
            self._widget.layout = widgets.Layout(width="95%")
            self._widget.style = {"description_width": "initial"}

    @property
    def widget(self) -> WidgetProtocol:
        return self._widget

    def get_value(self) -> T:
        """Get the current widget value."""
        return self._widget.value

    def set_value(self, value: T):
        """Set the widget value."""
        self._widget.value = value

    def observe(self, handler, names="value"):
        """Set up value change observation."""
        self._widget.observe(handler, names=names)

    def unobserve(self, handler, names="value"):
        """Remove value change observation."""
        self._widget.unobserve(handler, names=names)


class TextParameterWidget(BaseParameterWidget[str]):
    def _create_widget(self) -> widgets.Text:
        return widgets.Text(value=self.parameter.default, description=self.parameter.name)


class SelectionParameterWidget(BaseParameterWidget[Any]):
    def _create_widget(self) -> widgets.Dropdown:
        param = self.parameter
        assert isinstance(param, SingleSelectionParameter)
        return widgets.Dropdown(options=param.options, value=param.default if param.default else param.options[0], description=param.name)

    def update_options(self, new_options: List[Any]):
        """Update the available options in the dropdown."""
        current_value = self._widget.value
        self._widget.options = new_options
        if current_value in new_options:
            self._widget.value = current_value
        else:
            self._widget.value = new_options[0]


class MultipleSelectionParameterWidget(BaseParameterWidget[List[Any]]):
    def _create_widget(self) -> widgets.SelectMultiple:
        param = self.parameter
        assert isinstance(param, MultipleSelectionParameter)
        return widgets.SelectMultiple(options=param.options, value=param.default if param.default else [], description=param.name)

    def update_options(self, new_options: List[Any]):
        """Update the available options in the selection."""
        current_values = self._widget.value
        self._widget.options = new_options
        valid_values = [v for v in current_values if v in new_options]
        self._widget.value = valid_values


class BooleanParameterWidget(BaseParameterWidget[bool]):
    def _create_widget(self) -> widgets.Checkbox:
        param = self.parameter
        assert isinstance(param, BooleanParameter)
        return widgets.Checkbox(value=param.default, description=param.name)


class IntegerParameterWidget(BaseParameterWidget[int]):
    def _create_widget(self) -> widgets.IntSlider:
        param = self.parameter
        assert isinstance(param, IntegerParameter)
        return widgets.IntSlider(
            value=param.default if param.default is not None else param.min_value,
            min=param.min_value,
            max=param.max_value,
            description=param.name,
            continuous_update=self.continuous_update,
        )


class FloatParameterWidget(BaseParameterWidget[float]):
    def _create_widget(self) -> widgets.FloatSlider:
        param = self.parameter
        assert isinstance(param, FloatParameter)
        return widgets.FloatSlider(
            value=param.default if param.default is not None else param.min_value,
            min=param.min_value,
            max=param.max_value,
            step=param.step,
            description=param.name,
            continuous_update=self.continuous_update,
        )


@dataclass
class PairWidgetValue:
    """Helper class for pair widget values."""

    low: Any
    high: Any

    def as_tuple(self) -> Tuple[Any, Any]:
        return (self.low, self.high)


class BasePairParameterWidget(BaseParameterWidget[Tuple[T, T]], ABC):
    """Base class for pair parameter widgets."""

    @abstractmethod
    def _create_single_widget(self, value: T, description: str) -> WidgetProtocol:
        pass

    def _create_widget(self) -> widgets.VBox:
        param = self.parameter
        low_widget = self._create_single_widget(param.default[0], f"{param.name} (low)")
        high_widget = self._create_single_widget(param.default[1], f"{param.name} (high)")

        # Store references to child widgets
        self._low_widget = low_widget
        self._high_widget = high_widget

        return widgets.VBox([low_widget, high_widget])

    def get_value(self) -> Tuple[T, T]:
        """Get the current pair of values."""
        return (self._low_widget.value, self._high_widget.value)

    def set_value(self, value: Tuple[T, T]):
        """Set both values in the pair."""
        self._low_widget.value = value[0]
        self._high_widget.value = value[1]

    def observe(self, handler, names="value"):
        """Set up observation for both widgets."""
        self._low_widget.observe(handler, names=names)
        self._high_widget.observe(handler, names=names)

    def unobserve(self, handler, names="value"):
        """Remove observation from both widgets."""
        self._low_widget.unobserve(handler, names=names)
        self._high_widget.unobserve(handler, names=names)


class IntegerPairParameterWidget(BasePairParameterWidget[int]):
    def _create_single_widget(self, value: int, description: str) -> widgets.IntText:
        return widgets.IntText(value=value, description=description, layout=widgets.Layout(width="47%"))


class FloatPairParameterWidget(BasePairParameterWidget[float]):
    def _create_single_widget(self, value: float, description: str) -> widgets.FloatText:
        return widgets.FloatText(value=value, description=description, layout=widgets.Layout(width="47%"))


# Widget factory for creating the appropriate widget type
def create_parameter_widget(parameter: Parameter, continuous_update: bool = False) -> BaseParameterWidget:
    """Factory function to create the appropriate widget for a parameter."""
    widget_map = {
        TextParameter: TextParameterWidget,
        SingleSelectionParameter: SelectionParameterWidget,
        MultipleSelectionParameter: MultipleSelectionParameterWidget,
        BooleanParameter: BooleanParameterWidget,
        IntegerParameter: IntegerParameterWidget,
        FloatParameter: FloatParameterWidget,
        IntegerPairParameter: IntegerPairParameterWidget,
        FloatPairParameter: FloatPairParameterWidget,
    }

    widget_class = widget_map.get(type(parameter))
    if not widget_class:
        raise ValueError(f"No widget class found for parameter type: {type(parameter)}")

    return widget_class(parameter, continuous_update)
