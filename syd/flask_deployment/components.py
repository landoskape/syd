from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Union, Callable, Optional
from dataclasses import dataclass
from html import escape

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


@dataclass
class ComponentStyle:
    """Style configuration for components."""

    width: str = "auto"
    margin: str = "3px 0px"
    description_width: str = "initial"
    input_class: str = "form-control"
    label_class: str = "form-label"
    container_class: str = "mb-3"


class BaseComponent(Generic[T], ABC):
    """
    Abstract base class for all parameter components.

    This class defines the common interface and shared functionality
    for components that correspond to different parameter types.
    """

    _callbacks: List[Callable]
    _is_action: bool = False
    _value: Any
    _id: str

    def __init__(
        self,
        parameter: T,
        continuous: bool = False,
        style: Optional[ComponentStyle] = None,
    ):
        self._id = f"param_{parameter.name}"
        self._value = parameter.value
        self._callbacks = []
        self._continuous = continuous
        self._style = style or ComponentStyle()
        self._html = self._create_html(parameter)

    @abstractmethod
    def _create_html(self, parameter: T) -> str:
        """Create and return the appropriate HTML markup."""
        pass

    @property
    def html(self) -> str:
        """Get the HTML representation of the component."""
        return self._html

    @property
    def value(self) -> Any:
        """Get the current value of the component."""
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the value of the component."""
        self._value = new_value
        # In a real implementation, we'd use JavaScript to update the DOM
        # This would be handled by the Flask app's frontend code

    def matches_parameter(self, parameter: T) -> bool:
        """Check if the component matches the parameter."""
        return self.value == parameter.value

    def update_from_parameter(self, parameter: T) -> None:
        """Update the component from the parameter."""
        try:
            self.disable_callbacks()
            self.extra_updates_from_parameter(parameter)
            self.value = parameter.value
        finally:
            self.reenable_callbacks()

    def extra_updates_from_parameter(self, parameter: T) -> None:
        """Extra updates from the parameter."""
        pass

    def observe(self, callback: Callable) -> None:
        """Register a callback for value changes."""
        self._callbacks.append(callback)

    def unobserve(self, callback: Callable) -> None:
        """Unregister a callback."""
        self._callbacks.remove(callback)

    def reenable_callbacks(self) -> None:
        """Reenable all callbacks."""
        pass  # Handled by Flask routes and JavaScript

    def disable_callbacks(self) -> None:
        """Disable all callbacks."""
        pass  # Handled by Flask routes and JavaScript


class TextComponent(BaseComponent[TextParameter]):
    """Component for text parameters."""

    def _create_html(self, parameter: TextParameter) -> str:
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <input type="text" class="{self._style.input_class}" id="{self._id}" 
                   name="{parameter.name}" value="{escape(str(parameter.value))}"
                   style="width: {self._style.width}; margin: {self._style.margin};"
                   data-continuous="{str(self._continuous).lower()}">
        </div>
        """


class BooleanComponent(BaseComponent[BooleanParameter]):
    """Component for boolean parameters."""

    def _create_html(self, parameter: BooleanParameter) -> str:
        checked = "checked" if parameter.value else ""
        return f"""
        <div class="{self._style.container_class}">
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="{self._id}"
                       name="{parameter.name}" {checked}
                       style="margin: {self._style.margin};"
                       data-continuous="{str(self._continuous).lower()}">
                <label class="form-check-label" for="{self._id}">
                    {escape(parameter.name)}
                </label>
            </div>
        </div>
        """


class SelectionComponent(BaseComponent[SelectionParameter]):
    """Component for single selection parameters."""

    def _create_html(self, parameter: SelectionParameter) -> str:
        options_html = ""
        for option in parameter.options:
            selected = "selected" if option == parameter.value else ""
            options_html += f'<option value="{escape(str(option))}" {selected}>{escape(str(option))}</option>'

        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <select class="{self._style.input_class}" id="{self._id}" 
                    name="{parameter.name}"
                    style="width: {self._style.width}; margin: {self._style.margin};"
                    data-continuous="{str(self._continuous).lower()}">
                {options_html}
            </select>
        </div>
        """

    def matches_parameter(self, parameter: SelectionParameter) -> bool:
        """Check if the component matches the parameter."""
        return self.value == parameter.value and set(self._get_options()) == set(
            parameter.options
        )

    def _get_options(self) -> List[Any]:
        """Get current options from the HTML."""
        # In a real implementation, this would parse the HTML
        # For now, we'll just return an empty list
        return []

    def extra_updates_from_parameter(self, parameter: SelectionParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update the options in the DOM
        pass


class MultipleSelectionComponent(BaseComponent[MultipleSelectionParameter]):
    """Component for multiple selection parameters."""

    def _create_html(self, parameter: MultipleSelectionParameter) -> str:
        options_html = ""
        for option in parameter.options:
            selected = "selected" if option in parameter.value else ""
            options_html += f'<option value="{escape(str(option))}" {selected}>{escape(str(option))}</option>'

        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <select class="{self._style.input_class}" id="{self._id}" 
                    name="{parameter.name}" multiple
                    style="width: {self._style.width}; margin: {self._style.margin};"
                    data-continuous="{str(self._continuous).lower()}">
                {options_html}
            </select>
        </div>
        """

    def matches_parameter(self, parameter: MultipleSelectionParameter) -> bool:
        """Check if the component matches the parameter."""
        return set(self.value) == set(parameter.value) and set(
            self._get_options()
        ) == set(parameter.options)

    def _get_options(self) -> List[Any]:
        """Get current options from the HTML."""
        # In a real implementation, this would parse the HTML
        return []

    def extra_updates_from_parameter(
        self, parameter: MultipleSelectionParameter
    ) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update the options in the DOM
        pass


class IntegerComponent(BaseComponent[IntegerParameter]):
    """Component for integer parameters."""

    def _create_html(self, parameter: IntegerParameter) -> str:
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <input type="range" class="{self._style.input_class}" id="{self._id}"
                   name="{parameter.name}" value="{parameter.value}"
                   min="{parameter.min_value}" max="{parameter.max_value}"
                   style="width: {self._style.width}; margin: {self._style.margin};"
                   data-continuous="{str(self._continuous).lower()}">
            <output for="{self._id}">{parameter.value}</output>
        </div>
        """

    def matches_parameter(self, parameter: IntegerParameter) -> bool:
        """Check if the component matches the parameter."""
        return (
            self.value == parameter.value
            and self._get_min() == parameter.min_value
            and self._get_max() == parameter.max_value
        )

    def _get_min(self) -> int:
        """Get minimum value from the HTML."""
        return 0  # Placeholder

    def _get_max(self) -> int:
        """Get maximum value from the HTML."""
        return 100  # Placeholder

    def extra_updates_from_parameter(self, parameter: IntegerParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update min/max in the DOM
        pass


class FloatComponent(BaseComponent[FloatParameter]):
    """Component for float parameters."""

    def _create_html(self, parameter: FloatParameter) -> str:
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <input type="range" class="{self._style.input_class}" id="{self._id}"
                   name="{parameter.name}" value="{parameter.value}"
                   min="{parameter.min_value}" max="{parameter.max_value}" step="{parameter.step}"
                   style="width: {self._style.width}; margin: {self._style.margin};"
                   data-continuous="{str(self._continuous).lower()}">
            <output for="{self._id}">{parameter.value}</output>
        </div>
        """

    def matches_parameter(self, parameter: FloatParameter) -> bool:
        """Check if the component matches the parameter."""
        return (
            self.value == parameter.value
            and self._get_min() == parameter.min_value
            and self._get_max() == parameter.max_value
            and self._get_step() == parameter.step
        )

    def _get_min(self) -> float:
        """Get minimum value from the HTML."""
        return 0.0  # Placeholder

    def _get_max(self) -> float:
        """Get maximum value from the HTML."""
        return 1.0  # Placeholder

    def _get_step(self) -> float:
        """Get step value from the HTML."""
        return 0.1  # Placeholder

    def extra_updates_from_parameter(self, parameter: FloatParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update min/max/step in the DOM
        pass


class IntegerRangeComponent(BaseComponent[IntegerRangeParameter]):
    """Component for integer range parameters."""

    def _create_html(self, parameter: IntegerRangeParameter) -> str:
        low, high = parameter.value
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}_low" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <div class="d-flex align-items-center">
                <input type="range" class="{self._style.input_class}" id="{self._id}_low"
                       name="{parameter.name}_low" value="{low}"
                       min="{parameter.min_value}" max="{parameter.max_value}"
                       style="width: {self._style.width}; margin: {self._style.margin};"
                       data-continuous="{str(self._continuous).lower()}">
                <output for="{self._id}_low">{low}</output>
            </div>
            <div class="d-flex align-items-center">
                <input type="range" class="{self._style.input_class}" id="{self._id}_high"
                       name="{parameter.name}_high" value="{high}"
                       min="{parameter.min_value}" max="{parameter.max_value}"
                       style="width: {self._style.width}; margin: {self._style.margin};"
                       data-continuous="{str(self._continuous).lower()}">
                <output for="{self._id}_high">{high}</output>
            </div>
        </div>
        """

    def matches_parameter(self, parameter: IntegerRangeParameter) -> bool:
        """Check if the component matches the parameter."""
        return (
            self.value == parameter.value
            and self._get_min() == parameter.min_value
            and self._get_max() == parameter.max_value
        )

    def _get_min(self) -> int:
        """Get minimum value from the HTML."""
        return 0  # Placeholder

    def _get_max(self) -> int:
        """Get maximum value from the HTML."""
        return 100  # Placeholder

    def extra_updates_from_parameter(self, parameter: IntegerRangeParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update min/max in the DOM
        pass


class FloatRangeComponent(BaseComponent[FloatRangeParameter]):
    """Component for float range parameters."""

    def _create_html(self, parameter: FloatRangeParameter) -> str:
        low, high = parameter.value
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}_low" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <div class="d-flex align-items-center">
                <input type="range" class="{self._style.input_class}" id="{self._id}_low"
                       name="{parameter.name}_low" value="{low}"
                       min="{parameter.min_value}" max="{parameter.max_value}" step="{parameter.step}"
                       style="width: {self._style.width}; margin: {self._style.margin};"
                       data-continuous="{str(self._continuous).lower()}">
                <output for="{self._id}_low">{low}</output>
            </div>
            <div class="d-flex align-items-center">
                <input type="range" class="{self._style.input_class}" id="{self._id}_high"
                       name="{parameter.name}_high" value="{high}"
                       min="{parameter.min_value}" max="{parameter.max_value}" step="{parameter.step}"
                       style="width: {self._style.width}; margin: {self._style.margin};"
                       data-continuous="{str(self._continuous).lower()}">
                <output for="{self._id}_high">{high}</output>
            </div>
        </div>
        """

    def matches_parameter(self, parameter: FloatRangeParameter) -> bool:
        """Check if the component matches the parameter."""
        return (
            self.value == parameter.value
            and self._get_min() == parameter.min_value
            and self._get_max() == parameter.max_value
            and self._get_step() == parameter.step
        )

    def _get_min(self) -> float:
        """Get minimum value from the HTML."""
        return 0.0  # Placeholder

    def _get_max(self) -> float:
        """Get maximum value from the HTML."""
        return 1.0  # Placeholder

    def _get_step(self) -> float:
        """Get step value from the HTML."""
        return 0.1  # Placeholder

    def extra_updates_from_parameter(self, parameter: FloatRangeParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update min/max/step in the DOM
        pass


class UnboundedIntegerComponent(BaseComponent[UnboundedIntegerParameter]):
    """Component for unbounded integer parameters."""

    def _create_html(self, parameter: UnboundedIntegerParameter) -> str:
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <input type="number" class="{self._style.input_class}" id="{self._id}"
                   name="{parameter.name}" value="{parameter.value}"
                   style="width: {self._style.width}; margin: {self._style.margin};"
                   data-continuous="{str(self._continuous).lower()}">
        </div>
        """


class UnboundedFloatComponent(BaseComponent[UnboundedFloatParameter]):
    """Component for unbounded float parameters."""

    def _create_html(self, parameter: UnboundedFloatParameter) -> str:
        step = parameter.step if parameter.step is not None else "any"
        return f"""
        <div class="{self._style.container_class}">
            <label for="{self._id}" class="{self._style.label_class}">{escape(parameter.name)}</label>
            <input type="number" class="{self._style.input_class}" id="{self._id}"
                   name="{parameter.name}" value="{parameter.value}" step="{step}"
                   style="width: {self._style.width}; margin: {self._style.margin};"
                   data-continuous="{str(self._continuous).lower()}">
        </div>
        """

    def matches_parameter(self, parameter: UnboundedFloatParameter) -> bool:
        """Check if the component matches the parameter."""
        return self.value == parameter.value and self._get_step() == parameter.step

    def _get_step(self) -> Optional[float]:
        """Get step value from the HTML."""
        return None  # Placeholder

    def extra_updates_from_parameter(self, parameter: UnboundedFloatParameter) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update step in the DOM
        pass


class ButtonComponent(BaseComponent[ButtonAction]):
    """Component for button parameters."""

    _is_action: bool = True

    def _create_html(self, parameter: ButtonAction) -> str:
        return f"""
        <div class="{self._style.container_class}">
            <button type="button" class="btn btn-primary" id="{self._id}"
                    name="{parameter.name}"
                    style="width: {self._style.width}; margin: {self._style.margin};">
                {escape(parameter.label)}
            </button>
        </div>
        """

    def matches_parameter(self, parameter: ButtonAction) -> bool:
        """Check if the component matches the parameter."""
        return True  # Buttons don't have a value to match

    def extra_updates_from_parameter(self, parameter: ButtonAction) -> None:
        """Extra updates from the parameter."""
        # In a real implementation, this would update the button label in the DOM
        pass


def create_component(
    parameter: Union[Parameter[Any], ButtonAction],
    continuous: bool = False,
    style: Optional[ComponentStyle] = None,
) -> BaseComponent[Union[Parameter[Any], ButtonAction]]:
    """Create the appropriate component for a parameter."""
    component_map = {
        TextParameter: TextComponent,
        BooleanParameter: BooleanComponent,
        SelectionParameter: SelectionComponent,
        MultipleSelectionParameter: MultipleSelectionComponent,
        IntegerParameter: IntegerComponent,
        FloatParameter: FloatComponent,
        IntegerRangeParameter: IntegerRangeComponent,
        FloatRangeParameter: FloatRangeComponent,
        UnboundedIntegerParameter: UnboundedIntegerComponent,
        UnboundedFloatParameter: UnboundedFloatComponent,
        ButtonAction: ButtonComponent,
    }

    for param_type, component_class in component_map.items():
        if isinstance(parameter, param_type):
            return component_class(parameter, continuous, style)

    raise ValueError(f"No component available for parameter type: {type(parameter)}")
