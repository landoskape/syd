from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Union, Callable
from dash import dcc, html


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
C = TypeVar("C")


class BaseComponent(Generic[T, C], ABC):
    """
    Abstract base class for all parameter components.

    This class defines the common interface and shared functionality
    for components that correspond to different parameter types.
    """

    _component: C
    _callbacks: List[Dict[str, Union[Callable, Union[str, List[str]]]]]
    _is_action: bool = False
    _id: str

    def __init__(
        self,
        parameter: T,
        component_id: str,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ):
        self._id = component_id
        self._component = self._create_component(parameter, width, margin, label_width)
        self._callbacks = []

    @abstractmethod
    def _create_component(
        self,
        parameter: T,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> C:
        """Create and return the appropriate Plotly component."""
        pass

    @property
    def component(self) -> C:
        """Get the underlying Plotly component."""
        return self._component

    @property
    def id(self) -> str:
        """Get the component ID."""
        return self._id

    def matches_parameter(self, parameter: T) -> bool:
        """Check if the component matches the parameter."""
        return True  # Base implementation, override as needed

    def update_from_parameter(self, parameter: T) -> None:
        """Update the component from the parameter."""
        self.extra_updates_from_parameter(parameter)

    def extra_updates_from_parameter(self, parameter: T) -> None:
        """Extra updates from the parameter."""
        pass


class TextComponent(BaseComponent[TextParameter, Any]):
    """Component for text parameters."""

    def _create_component(
        self,
        parameter: TextParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Input(
                        id=self._id,
                        type="text",
                        value=parameter.value,
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class BooleanComponent(BaseComponent[BooleanParameter, Any]):
    """Component for boolean parameters."""

    def _create_component(
        self,
        parameter: BooleanParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Div(
                    dcc.Checklist(
                        id=self._id,
                        options=[{"label": parameter.name, "value": "checked"}],
                        value=["checked"] if parameter.value else [],
                    ),
                    style={"width": width, "margin": margin},
                )
            ]
        )


class SelectionComponent(BaseComponent[SelectionParameter, Any]):
    """Component for single selection parameters."""

    def _create_component(
        self,
        parameter: SelectionParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Dropdown(
                        id=self._id,
                        options=[
                            {"label": opt, "value": opt} for opt in parameter.options
                        ],
                        value=parameter.value,
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )

    def matches_parameter(self, parameter: SelectionParameter) -> bool:
        """Check if the component matches the parameter."""
        current_options = [
            opt["value"] for opt in self._component.children[1].children.options
        ]
        return current_options == parameter.options

    def extra_updates_from_parameter(self, parameter: SelectionParameter) -> None:
        """Extra updates from the parameter."""
        self._component.children[1].children.options = [
            {"label": opt, "value": opt} for opt in parameter.options
        ]


class MultipleSelectionComponent(BaseComponent[MultipleSelectionParameter, Any]):
    """Component for multiple selection parameters."""

    def _create_component(
        self,
        parameter: MultipleSelectionParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Dropdown(
                        id=self._id,
                        options=[
                            {"label": opt, "value": opt} for opt in parameter.options
                        ],
                        value=parameter.value,
                        multi=True,
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )

    def matches_parameter(self, parameter: MultipleSelectionParameter) -> bool:
        """Check if the component matches the parameter."""
        current_options = [
            opt["value"] for opt in self._component.children[1].children.options
        ]
        return current_options == parameter.options

    def extra_updates_from_parameter(
        self, parameter: MultipleSelectionParameter
    ) -> None:
        """Extra updates from the parameter."""
        self._component.children[1].children.options = [
            {"label": opt, "value": opt} for opt in parameter.options
        ]


class SliderComponent(BaseComponent[Union[IntegerParameter, FloatParameter], Any]):
    """Base component for numeric sliders."""

    def _create_component(
        self,
        parameter: Union[IntegerParameter, FloatParameter],
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                dcc.Slider(
                    id=self._id,
                    min=parameter.min_value,
                    max=parameter.max_value,
                    value=parameter.value,
                    step=getattr(parameter, "step", 1),
                    marks={
                        i: str(i)
                        for i in range(parameter.min_value, parameter.max_value + 1)
                    },
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class IntegerComponent(BaseComponent[IntegerParameter, Any]):
    """Component for integer parameters."""

    def _create_component(
        self,
        parameter: IntegerParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Slider(
                        id=self._id,
                        min=parameter.min_value,
                        max=parameter.max_value,
                        value=parameter.value,
                        step=1,
                        marks={
                            i: str(i)
                            for i in range(parameter.min_value, parameter.max_value + 1)
                        },
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class FloatComponent(BaseComponent[FloatParameter, Any]):
    """Component for float parameters."""

    def _create_component(
        self,
        parameter: FloatParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Slider(
                        id=self._id,
                        min=parameter.min_value,
                        max=parameter.max_value,
                        value=parameter.value,
                        step=parameter.step,
                        marks={
                            i: str(i)
                            for i in range(
                                int(parameter.min_value), int(parameter.max_value) + 1
                            )
                        },
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class RangeSliderComponent(
    BaseComponent[Union[IntegerRangeParameter, FloatRangeParameter], Any]
):
    """Base component for range sliders."""

    def _create_component(
        self,
        parameter: Union[IntegerRangeParameter, FloatRangeParameter],
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                dcc.RangeSlider(
                    id=self._id,
                    min=parameter.min_value,
                    max=parameter.max_value,
                    value=parameter.value,
                    step=getattr(parameter, "step", 1),
                    marks={
                        i: str(i)
                        for i in range(parameter.min_value, parameter.max_value + 1)
                    },
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class IntegerRangeComponent(BaseComponent[IntegerRangeParameter, Any]):
    """Component for integer range parameters."""

    def _create_component(
        self,
        parameter: IntegerRangeParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.RangeSlider(
                        id=self._id,
                        min=parameter.min_value,
                        max=parameter.max_value,
                        value=parameter.value,
                        step=1,
                        marks={
                            i: str(i)
                            for i in range(parameter.min_value, parameter.max_value + 1)
                        },
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class FloatRangeComponent(BaseComponent[FloatRangeParameter, Any]):
    """Component for float range parameters."""

    def _create_component(
        self,
        parameter: FloatRangeParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.RangeSlider(
                        id=self._id,
                        min=parameter.min_value,
                        max=parameter.max_value,
                        value=parameter.value,
                        step=parameter.step,
                        marks={
                            i: str(i)
                            for i in range(
                                int(parameter.min_value), int(parameter.max_value) + 1
                            )
                        },
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class UnboundedIntegerComponent(BaseComponent[UnboundedIntegerParameter, Any]):
    """Component for unbounded integer parameters."""

    def _create_component(
        self,
        parameter: UnboundedIntegerParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Input(
                        id=self._id,
                        type="number",
                        value=parameter.value,
                        step=1,
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class UnboundedFloatComponent(BaseComponent[UnboundedFloatParameter, Any]):
    """Component for unbounded float parameters."""

    def _create_component(
        self,
        parameter: UnboundedFloatParameter,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            [
                html.Label(parameter.name, style={"width": label_width}),
                html.Div(
                    dcc.Input(
                        id=self._id,
                        type="number",
                        value=parameter.value,
                        step=parameter.step,
                    ),
                    style={"width": width, "margin": margin},
                ),
            ]
        )


class ButtonComponent(BaseComponent[ButtonAction, Any]):
    """Component for button actions."""

    _is_action: bool = True

    def _create_component(
        self,
        parameter: ButtonAction,
        width: str = "auto",
        margin: str = "3px 0px",
        label_width: str = "initial",
    ) -> Any:
        return html.Div(
            html.Button(
                parameter.label,
                id=self._id,
            ),
            style={"width": width, "margin": margin},
        )


def create_component(
    parameter: Union[Parameter[Any], ButtonAction],
    component_id: str,
    width: str = "auto",
    margin: str = "3px 0px",
    label_width: str = "initial",
) -> BaseComponent[Union[Parameter[Any], ButtonAction], Any]:
    """Create and return the appropriate component for the given parameter.

    Args:
        parameter: The parameter to create a component for
        component_id: Unique ID for the component
        width: Width of the component
        margin: Margin of the component
        label_width: Width of the label
    """
    component_map = {
        TextParameter: TextComponent,
        SelectionParameter: SelectionComponent,
        MultipleSelectionParameter: MultipleSelectionComponent,
        BooleanParameter: BooleanComponent,
        IntegerParameter: IntegerComponent,
        FloatParameter: FloatComponent,
        IntegerRangeParameter: IntegerRangeComponent,
        FloatRangeParameter: FloatRangeComponent,
        UnboundedIntegerParameter: UnboundedIntegerComponent,
        UnboundedFloatParameter: UnboundedFloatComponent,
        ButtonAction: ButtonComponent,
    }

    # Try direct type lookup first
    component_class = component_map.get(type(parameter))

    # If that fails, try matching by class name
    if component_class is None:
        param_type_name = type(parameter).__name__
        for key_class, value_class in component_map.items():
            if key_class.__name__ == param_type_name:
                component_class = value_class
                break

    if component_class is None:
        raise ValueError(
            f"No component implementation for parameter type: {type(parameter)}\n"
            f"Parameter type name: {type(parameter).__name__}\n"
            f"Available types: {[k.__name__ for k in component_map.keys()]}"
        )

    return component_class(
        parameter,
        component_id,
        width=width,
        margin=margin,
        label_width=label_width,
    )
