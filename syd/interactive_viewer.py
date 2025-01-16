from typing import List, Any, Callable, Dict, Tuple, Union
from functools import wraps
from contextlib import contextmanager
from abc import ABC, abstractmethod
from matplotlib.figure import Figure

from .parameters import ParameterType, Parameter


def validate_parameter_operation(operation: str, parameter_type: ParameterType) -> Callable:
    """
    Decorator that validates parameter operations for the InteractiveViewer class.

    This decorator ensures that:
    1. The operation type matches the method name (add/update)
    2. The parameter type matches the method's intended parameter type
    3. Parameters can only be added when the app is not deployed
    4. Parameters can only be updated when the app is deployed
    5. For updates, validates that the parameter exists and is of the correct type

    Args:
        operation (str): The type of operation to validate. Must be either 'add' or 'update'.
        parameter_type (ParameterType): The expected parameter type from the ParameterType enum.

    Returns:
        Callable: A decorated function that includes parameter validation.

    Raises:
        ValueError: If the operation type doesn't match the method name or if updating a non-existent parameter
        TypeError: If updating a parameter with an incorrect type
        RuntimeError: If adding parameters while deployed or updating while not deployed

    Example:
        @validate_parameter_operation('add', ParameterType.text)
        def add_text(self, name: str, default: str = "") -> None:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: "InteractiveViewer", name: str, *args, **kwargs):
            # Validate operation matches method name (add/update)
            if not func.__name__.startswith(operation):
                raise ValueError(f"Invalid operation type specified ({operation}) for method {func.__name__}")

            # Validate deployment state
            if operation == "add" and self._app_deployed:
                raise RuntimeError("The app is currently deployed, cannot add a new parameter right now.")

            # For updates, validate parameter existence and type
            if operation == "update":
                if name not in self.parameters:
                    raise ValueError(f"Parameter called {name} not found - you can only update registered parameters!")
                if type(self.parameters[name]) != parameter_type.value:
                    msg = f"Parameter called {name} was found but is registered as a different parameter type ({type(self.parameters[name])})"
                    raise TypeError(msg)

            return func(self, name, *args, **kwargs)

        return wrapper

    return decorator


class InteractiveViewer(ABC):
    parameters: Dict[str, Parameter]
    callbacks: Dict[str, List[Callable]]
    state: Dict[str, Any]
    _app_deployed: bool
    _in_callbacks: bool

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.parameters = {}
        instance.callbacks = {}
        instance.state = {}
        instance._app_deployed = False
        instance._in_callbacks = False
        return instance

    def get_state(self) -> Dict[str, Any]:
        return {name: param.value for name, param in self.parameters.items()}

    @abstractmethod
    def plot(self, **kwargs) -> Figure:
        raise NotImplementedError("Subclasses must implement the plot method")

    @contextmanager
    def deploy_app(self):
        """Internal context manager to control app deployment state"""
        self._app_deployed = True
        try:
            yield
        finally:
            self._app_deployed = False

    def perform_callbacks(self, name: str) -> bool:
        """Perform callbacks for all parameters that have changed"""
        if self._in_callbacks:
            return
        try:
            self._in_callbacks = True
            if name in self.callbacks:
                state = self.get_state()
                for callback in self.callbacks[name]:
                    callback(state)
        finally:
            self._in_callbacks = False

    def on_change(self, parameter_name: Union[str, List[str]], callback: Callable):
        """Register a function to be called when a parameter changes."""
        if isinstance(parameter_name, str):
            parameter_name = [parameter_name]

        for param_name in parameter_name:
            if param_name not in self.parameters:
                raise ValueError(f"Parameter '{param_name}' is not registered!")
            if param_name not in self.callbacks:
                self.callbacks[param_name] = []
            self.callbacks[param_name].append(callback)

    def set_parameter_value(self, name: str, value: Any) -> None:
        """Set a parameter value and trigger dependency updates"""
        if name not in self.parameters:
            raise ValueError(f"Parameter {name} not found")

        # Update the parameter value
        self.parameters[name].value = value

        # Perform callbacks
        self.perform_callbacks(name)

    # -------------------- parameter registration methods --------------------
    @validate_parameter_operation("add", ParameterType.text)
    def add_text(self, name: str, default: str = "") -> None:
        self.parameters[name] = ParameterType.text.value(name, default)

    @validate_parameter_operation("add", ParameterType.selection)
    def add_selection(self, name: str, options: List[Any], default: Any = None) -> None:
        self.parameters[name] = ParameterType.selection.value(name, options, default)

    @validate_parameter_operation("add", ParameterType.multiple_selection)
    def add_multiple_selection(self, name: str, options: List[Any], default: List[Any] = None) -> None:
        self.parameters[name] = ParameterType.multiple_selection.value(name, options, default)

    @validate_parameter_operation("add", ParameterType.boolean)
    def add_boolean(self, name: str, default: bool = True) -> None:
        self.parameters[name] = ParameterType.boolean.value(name, default)

    @validate_parameter_operation("add", ParameterType.integer)
    def add_integer(self, name: str, min_value: int = None, max_value: int = None, default: int = 0) -> None:
        self.parameters[name] = ParameterType.integer.value(name, min_value, max_value, default)

    @validate_parameter_operation("add", ParameterType.float)
    def add_float(self, name: str, min_value: float = None, max_value: float = None, default: float = 0.0, step: float = 0.1) -> None:
        self.parameters[name] = ParameterType.float.value(name, min_value, max_value, default, step)

    @validate_parameter_operation("add", ParameterType.integer_pair)
    def add_integer_pair(
        self,
        name: str,
        default: Tuple[int, int],
        min_value: int = None,
        max_value: int = None,
    ) -> None:
        self.parameters[name] = ParameterType.integer_pair.value(name, default, min_value, max_value)

    @validate_parameter_operation("add", ParameterType.float_pair)
    def add_float_pair(
        self,
        name: str,
        default: Tuple[float, float],
        min_value: float = None,
        max_value: float = None,
        step: float = 0.1,
    ) -> None:
        self.parameters[name] = ParameterType.float_pair.value(name, default, min_value, max_value, step)

    # -------------------- parameter update methods --------------------
    @validate_parameter_operation("update", ParameterType.text)
    def update_text(self, name: str, default: str = "") -> None:
        self.parameters[name] = ParameterType.text.value(name, default)

    @validate_parameter_operation("update", ParameterType.selection)
    def update_selection(self, name: str, options: List[Any], default: Any = None) -> None:
        self.parameters[name] = ParameterType.selection.value(name, options, default)

    @validate_parameter_operation("update", ParameterType.multiple_selection)
    def update_multiple_selection(self, name: str, options: List[Any], default: List[Any] = None) -> None:
        self.parameters[name] = ParameterType.multiple_selection.value(name, options, default)

    @validate_parameter_operation("update", ParameterType.boolean)
    def update_boolean(self, name: str, default: bool = True) -> None:
        self.parameters[name] = ParameterType.boolean.value(name, default)

    @validate_parameter_operation("update", ParameterType.integer)
    def update_integer(self, name: str, min_value: int = None, max_value: int = None, default: int = 0) -> None:
        self.parameters[name] = ParameterType.integer.value(name, min_value, max_value, default)

    @validate_parameter_operation("update", ParameterType.float)
    def update_float(self, name: str, min_value: float = None, max_value: float = None, default: float = 0.0, step: float = 0.1) -> None:
        self.parameters[name] = ParameterType.float.value(name, min_value, max_value, default, step)

    @validate_parameter_operation("update", ParameterType.integer_pair)
    def update_integer_pair(
        self,
        name: str,
        default: Tuple[int, int],
        min_value: int = None,
        max_value: int = None,
    ) -> None:
        self.parameters[name] = ParameterType.integer_pair.value(name, default, min_value, max_value)

    @validate_parameter_operation("update", ParameterType.float_pair)
    def update_float_pair(
        self,
        name: str,
        default: Tuple[float, float],
        min_value: float = None,
        max_value: float = None,
        step: float = 0.1,
    ) -> None:
        self.parameters[name] = ParameterType.float_pair.value(name, default, min_value, max_value, step)
