from typing import Any, Optional, Protocol, Dict
from abc import ABC, abstractmethod
import warnings
from functools import wraps
from contextlib import contextmanager
from time import time
import matplotlib.pyplot as plt

from .parameters import ParameterUpdateWarning, Parameter
from .viewer import Viewer


class ComponentProtocol(Protocol):
    """Protocol for all components."""

    # Components must be associated with a value
    @property
    def value(self) -> Any: ...

    # Components must define whether they are actions
    @property
    def is_action(self) -> bool: ...

    # Components must be able to check if they match a parameter
    def matches_parameter(self, parameter: Parameter) -> bool: ...

    # Components must be able to update their properties from a parameter
    def update_from_parameter(self, parameter: Parameter) -> None: ...


@contextmanager
def _plot_context():
    plt.ioff()
    try:
        yield
    finally:
        plt.ion()


def debounce(wait_time):
    """
    Decorator to prevent a function from being called more than once every wait_time seconds.
    """

    def decorator(fn):
        last_called = [0.0]  # Using list to maintain state in closure

        @wraps(fn)
        def debounced(*args, **kwargs):
            current_time = time()
            if current_time - last_called[0] >= wait_time:
                fn(*args, **kwargs)
                last_called[0] = current_time

        return debounced

    return decorator


class Deployer(ABC):
    """Base class for all deployers.

    Handles central logic for deployment of a syd viewer in any environment.
    """

    def __init__(self, viewer: Viewer, suppress_warnings: bool = False):
        self.viewer = viewer
        self.components: Dict[str, ComponentProtocol] = {}
        self.suppress_warnings = suppress_warnings
        self._updating = False  # Flag to check circular updates

    @abstractmethod
    def display_new_plot(self, figure: Any) -> None:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def build_components(self) -> None:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def build_layout(self) -> None:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def display(self) -> None:
        raise NotImplementedError("Subclasses must implement this method.")

    def deploy(self) -> None:
        """Deploy the viewer.

        Deployment takes three steps which are unique to each deployment environment.
        1. Build the components.
        2. Build the layout.
        3. Set the callbacks for the components (the components need to have populated the components dictionary!)
        3. Display the full layout.
        """
        self.build_components()
        self.build_layout()
        self.display()
        self.update_plot()

    @debounce(0.1)
    def handle_component_engagement(self, name: str) -> None:
        """Handle engagement with an interactive component."""
        if self._updating:
            print(
                "Already updating -- there's a circular dependency!"
                "This is probably caused by failing to disable callbacks for a parameter."
                "It's a bug --- tell the developer on github issues please."
            )
            return

        try:
            self._updating = True

            # Optionally suppress warnings during parameter updates
            with warnings.catch_warnings():
                if self.suppress_warnings:
                    warnings.filterwarnings("ignore", category=ParameterUpdateWarning)

                # Get the component
                component = self.components[name]
                if component.is_action:
                    # If the component is an action, call the callback
                    parameter = self.viewer.parameters[name]
                    parameter.callback(self.viewer.state)
                else:
                    # Otherwise, update the parameter value
                    self.viewer.set_parameter_value(name, component.value)

                # Update any components that changed due to dependencies
                self.sync_components_with_state()

                # Update the plot
                self.update_plot()

        finally:
            self._updating = False

    def sync_components_with_state(self, exclude: Optional[str] = None) -> None:
        """Sync component values with viewer state."""
        for name, parameter in self.viewer.parameters.items():
            if name == exclude:
                continue

            component = self.components[name]
            if not component.matches_parameter(parameter):
                component.update_from_parameter(parameter)

    def update_plot(self) -> None:
        """Update the plot with current state."""
        state = self.viewer.state

        with _plot_context():
            figure = self.viewer.plot(state)

        # Update components if plot function updated a parameter
        self.sync_components_with_state()

        # Display the new plot (each deployer will have a different way of doing this)
        self.display_new_plot(figure)
