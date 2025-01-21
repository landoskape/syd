from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Union, Optional
from dataclasses import dataclass
from markupsafe import Markup

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


class BaseWebComponent(Generic[T], ABC):
    """
    Abstract base class for all web components.

    This class defines the interface for HTML/JS components that correspond
    to different parameter types in the web deployment.
    """

    def __init__(self, parameter: T, component_id: str):
        """
        Initialize the web component.

        Args:
            parameter: The parameter this component represents
            component_id: Unique ID for this component in the DOM
        """
        self.parameter = parameter
        self.component_id = component_id

    @abstractmethod
    def render_html(self) -> str:
        """
        Render the HTML for this component.

        Returns:
            str: HTML markup for the component
        """
        pass

    @abstractmethod
    def get_js_init(self) -> str:
        """
        Get JavaScript code needed to initialize this component.

        Returns:
            str: JavaScript code that sets up event listeners etc.
        """
        pass

    def get_js_update(self, value: Any) -> str:
        """
        Get JavaScript code needed to update this component's value.

        Args:
            value: New value to set

        Returns:
            str: JavaScript code that updates the component's value
        """
        # Default implementation for simple components
        return f"document.getElementById('{self.component_id}').value = {self._value_to_js(value)};"

    def _value_to_js(self, value: Any) -> str:
        """Convert a Python value to its JavaScript representation."""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (list, tuple)):
            return f"[{', '.join(self._value_to_js(v) for v in value)}]"
        else:
            raise ValueError(f"Cannot convert {type(value)} to JavaScript")


class TextComponent(BaseWebComponent[TextParameter]):
    """Component for text input parameters."""

    def render_html(self) -> str:
        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <input type="text" 
                       class="form-control" 
                       id="{self.component_id}" 
                       value="{self.parameter.value}">
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                updateParameter('{self.parameter.name}', e.target.value);
            }});
        """


class BooleanComponent(BaseWebComponent[BooleanParameter]):
    """Component for boolean parameters."""

    def render_html(self) -> str:
        checked = "checked" if self.parameter.value else ""
        return f"""
            <div class="form-check">
                <input type="checkbox" 
                       class="form-check-input" 
                       id="{self.component_id}" 
                       {checked}>
                <label class="form-check-label" 
                       for="{self.component_id}">
                    {self.parameter.name}
                </label>
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                updateParameter('{self.parameter.name}', e.target.checked);
            }});
        """

    def get_js_update(self, value: bool) -> str:
        return f"document.getElementById('{self.component_id}').checked = {str(value).lower()};"


class SelectionComponent(BaseWebComponent[SelectionParameter]):
    """Component for single selection parameters."""

    def render_html(self) -> str:
        options = []
        for opt in self.parameter.options:
            selected = "selected" if opt == self.parameter.value else ""
            options.append(f'<option value="{opt}" {selected}>{opt}</option>')

        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <select class="form-control" id="{self.component_id}">
                    {"".join(options)}
                </select>
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                updateParameter('{self.parameter.name}', e.target.value);
            }});
        """


class MultipleSelectionComponent(BaseWebComponent[MultipleSelectionParameter]):
    """Component for multiple selection parameters."""

    def render_html(self) -> str:
        options = []
        for opt in self.parameter.options:
            selected = "selected" if opt in self.parameter.value else ""
            options.append(f'<option value="{opt}" {selected}>{opt}</option>')

        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <select multiple class="form-control" id="{self.component_id}">
                    {"".join(options)}
                </select>
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                const selected = Array.from(e.target.selectedOptions).map(opt => opt.value);
                updateParameter('{self.parameter.name}', selected);
            }});
        """

    def get_js_update(self, values: List[str]) -> str:
        # More complex update for multi-select
        return f"""
            const sel = document.getElementById('{self.component_id}');
            Array.from(sel.options).forEach(opt => {{
                opt.selected = {self._value_to_js(values)}.includes(opt.value);
            }});
        """


class SliderMixin:
    """Shared functionality for slider components."""

    def _get_slider_js_init(self, component_id: str, param_name: str) -> str:
        return f"""
            noUiSlider.create(document.getElementById('{component_id}'), {{
                start: {self._value_to_js(self.parameter.value)},
                connect: true,
                range: {{
                    'min': {self.parameter.min_value},
                    'max': {self.parameter.max_value}
                }}
            }}).on('change', (values) => {{
                updateParameter('{param_name}', parseFloat(values[0]));
                const value = parseFloat(values[0]);
                // Update the display text
                document.getElementById('{component_id}_display').textContent = value.toFixed(2);
                debouncedUpdateParameter('{param_name}', value);
            }});
        """


class IntegerComponent(SliderMixin, BaseWebComponent[IntegerParameter]):
    """Component for integer parameters."""

    def render_html(self) -> str:
        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <div id="{self.component_id}" class="slider"></div>
                <span id="{self.component_id}_display" class="value-display">{self.parameter.value}</span>
            </div>
        """

    def get_js_init(self) -> str:
        return self._get_slider_js_init(self.component_id, self.parameter.name)


class FloatComponent(SliderMixin, BaseWebComponent[FloatParameter]):
    """Component for float parameters."""

    def render_html(self) -> str:
        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <div id="{self.component_id}" class="slider"></div>
                <span id="{self.component_id}_display" class="value-display">{self.parameter.value:.2f}</span>
            </div>
        """

    def get_js_init(self) -> str:
        return self._get_slider_js_init(self.component_id, self.parameter.name)


class RangeSliderMixin:
    """Shared functionality for range slider components."""

    def _get_range_slider_js_init(self, component_id: str, param_name: str) -> str:
        return f"""
            noUiSlider.create(document.getElementById('{component_id}'), {{
                start: {self._value_to_js(self.parameter.value)},
                connect: true,
                range: {{
                    'min': {self.parameter.min_value},
                    'max': {self.parameter.max_value}
                }}
            }}).on('change', (values) => {{
                updateParameter('{param_name}', [
                    parseFloat(values[0]), 
                    parseFloat(values[1])
                ]);
            }});
        """


class IntegerRangeComponent(RangeSliderMixin, BaseWebComponent[IntegerRangeParameter]):
    """Component for integer range parameters."""

    def render_html(self) -> str:
        low, high = self.parameter.value
        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <div id="{self.component_id}" class="range-slider"></div>
                <span class="value-display">{low} - {high}</span>
            </div>
        """

    def get_js_init(self) -> str:
        return self._get_range_slider_js_init(self.component_id, self.parameter.name)


class FloatRangeComponent(RangeSliderMixin, BaseWebComponent[FloatRangeParameter]):
    """Component for float range parameters."""

    def render_html(self) -> str:
        low, high = self.parameter.value
        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <div id="{self.component_id}" class="range-slider"></div>
                <span class="value-display">{low:.2f} - {high:.2f}</span>
            </div>
        """

    def get_js_init(self) -> str:
        return self._get_range_slider_js_init(self.component_id, self.parameter.name)


class UnboundedIntegerComponent(BaseWebComponent[UnboundedIntegerParameter]):
    """Component for unbounded integer parameters."""

    def render_html(self) -> str:
        min_attr = (
            f'min="{self.parameter.min_value}"'
            if self.parameter.min_value is not None
            else ""
        )
        max_attr = (
            f'max="{self.parameter.max_value}"'
            if self.parameter.max_value is not None
            else ""
        )

        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <input type="number" 
                       class="form-control" 
                       id="{self.component_id}" 
                       value="{self.parameter.value}"
                       {min_attr}
                       {max_attr}
                       step="1">
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                updateParameter('{self.parameter.name}', parseInt(e.target.value));
            }});
        """


class UnboundedFloatComponent(BaseWebComponent[UnboundedFloatParameter]):
    """Component for unbounded float parameters."""

    def render_html(self) -> str:
        min_attr = (
            f'min="{self.parameter.min_value}"'
            if self.parameter.min_value is not None
            else ""
        )
        max_attr = (
            f'max="{self.parameter.max_value}"'
            if self.parameter.max_value is not None
            else ""
        )
        step_attr = (
            f'step="{self.parameter.step}"' if self.parameter.step is not None else ""
        )

        return f"""
            <div class="form-group">
                <label for="{self.component_id}">{self.parameter.name}</label>
                <input type="number" 
                       class="form-control" 
                       id="{self.component_id}" 
                       value="{self.parameter.value}"
                       {min_attr}
                       {max_attr}
                       {step_attr}>
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('change', (e) => {{
                updateParameter('{self.parameter.name}', parseFloat(e.target.value));
            }});
        """


class ButtonComponent(BaseWebComponent[ButtonParameter]):
    """Component for button parameters."""

    def render_html(self) -> str:
        return f"""
            <div class="form-group">
                <button type="button" 
                        class="btn btn-primary" 
                        id="{self.component_id}">
                    {self.parameter.label}
                </button>
            </div>
        """

    def get_js_init(self) -> str:
        return f"""
            document.getElementById('{self.component_id}').addEventListener('click', () => {{
                buttonClick('{self.parameter.name}');
            }});
        """


def create_web_component(
    parameter: Parameter[Any], component_id: str
) -> BaseWebComponent[Parameter[Any]]:
    """Create and return the appropriate web component for the given parameter."""

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
        ButtonParameter: ButtonComponent,
    }

    component_class = component_map.get(type(parameter))
    if component_class is None:
        raise ValueError(
            f"No component implementation for parameter type: {type(parameter)}"
        )

    return component_class(parameter, component_id)


class WebComponentCollection:
    """
    Manages a collection of web components for a viewer's parameters.

    This class helps organize all the components needed for a viewer,
    handling their creation, initialization, and updates.
    """

    def __init__(self):
        self.components: Dict[str, BaseWebComponent] = {}

    def add_component(self, name: str, parameter: Parameter[Any]) -> None:
        """Add a new component for the given parameter."""
        component_id = f"param_{name}"
        self.components[name] = create_web_component(parameter, component_id)

    def get_all_html(self) -> str:
        """Get the combined HTML for all components."""
        return "\n".join(comp.render_html() for comp in self.components.values())

    def get_init_js(self) -> str:
        """Get the combined initialization JavaScript for all components."""
        return "\n".join(comp.get_js_init() for comp in self.components.values())

    def get_update_js(self, name: str, value: Any) -> str:
        """Get the JavaScript to update a specific component's value."""
        if name not in self.components:
            raise ValueError(f"No component found for parameter: {name}")
        return self.components[name].get_js_update(value)

    def get_required_css(self) -> List[str]:
        """Get list of CSS files required by the components."""
        return [
            "https://cdn.jsdelivr.net/npm/nouislider@14.6.3/distribute/nouislider.min.css",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
        ]

    def get_required_js(self) -> List[str]:
        """Get list of JavaScript files required by the components."""
        return [
            "https://cdn.jsdelivr.net/npm/nouislider@14.6.3/distribute/nouislider.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
        ]

    def get_custom_styles(self) -> str:
        """Get custom CSS styles needed for the components."""
        return """
            .slider, .range-slider {
                margin: 10px 0;
            }
            .value-display {
                display: block;
                text-align: center;
                margin-top: 5px;
                font-size: 0.9em;
                color: #666;
            }
            .form-group {
                margin-bottom: 1rem;
            }
        """
