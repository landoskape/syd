from typing import List, Any, Tuple, Generic, TypeVar, Optional, Dict, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from copy import copy, deepcopy
from warnings import warn

T = TypeVar("T")


class ParameterAddError(Exception):
    """Raised when parameter creation fails due to invalid arguments or state."""

    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(f"Failed to create {parameter_type} parameter '{parameter_name}'" + (f": {message}" if message else ""))


class ParameterUpdateError(Exception):
    """Raised when parameter update fails due to invalid arguments or state."""

    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(f"Failed to update {parameter_type} parameter '{parameter_name}'" + (f": {message}" if message else ""))


def get_parameter_attributes(param_class) -> List[str]:
    """Get all attributes for a parameter class."""
    attributes = []

    # Walk through class hierarchy in reverse (most specific to most general)
    for cls in reversed(param_class.__mro__):
        if hasattr(cls, "__annotations__"):
            # Only add annotations that haven't been specified by a more specific class
            for name in cls.__annotations__:
                if not name.startswith("_"):
                    attributes.append(name)

    return attributes


@dataclass
class Parameter(Generic[T], ABC):
    """Abstract base class for parameters that should not be instantiated directly."""

    name: str
    value: T

    @abstractmethod
    def __init__(self, name: str, value: T):
        raise NotImplementedError("Need to define in subclass for proper IDE support")

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        self._value = self._validate(new_value)

    @abstractmethod
    def _validate(self, new_value: Any) -> T:
        raise NotImplementedError

    def update(self, updates: Dict[str, Any]) -> None:
        """Update parameter attributes while respecting validation rules.

        Updates are performed atomically - either all updates succeed or none do.
        The parameter state remains unchanged if any validation fails.

        Args:
            updates: Dictionary of attributes to update

        Raises:
            ValueError: If attempting to update 'name' or an invalid attribute
            ParameterUpdateError: If any validation fails during the update
        """
        # Make a copy of self
        param_copy = deepcopy(self)

        try:
            # Apply updates to copy using private method
            param_copy._unsafe_update(updates)

            # If we get here, updates and validation succeeded on the copy
            # Now transfer all non-private attributes using proper setters
            for key, value in vars(param_copy).items():
                if not key.startswith("_"):
                    setattr(self, key, value)

            # Handle value separately using property setter
            self.value = param_copy.value

        except Exception as e:
            # Re-raise as ParameterUpdateError with context
            if isinstance(e, ValueError):
                raise ParameterUpdateError(self.name, type(self).__name__, str(e)) from e
            else:
                raise ParameterUpdateError(self.name, type(self).__name__, f"Update failed: {str(e)}") from e

    def _unsafe_update(self, updates: Dict[str, Any]) -> None:
        """Internal method to apply updates without safety mechanisms.

        This method performs the actual update logic but without the safety of doing it
        on a copy first. It should only be called from the safe update() method. This
        method will leave self in an inconsistent state if it fails.

        Args:
            updates: Dictionary of attributes to update

        Raises:
            ValueError: If attempting to update 'name' or an invalid attribute
        """
        # Validate the updates first
        valid_attributes = get_parameter_attributes(type(self))

        for key, new_value in updates.items():
            if key == "name":
                raise ValueError(f"Cannot update parameter name")
            elif key not in valid_attributes:
                raise ValueError(f"Update failed, {key} is not a valid attribute for {self.name}")

        # Apply non-value updates first
        for key, new_value in updates.items():
            if key != "value":
                setattr(self, key, new_value)

        # Update value last to avoid validation errors in case
        # the user changed options/bounds/etc
        if "value" in updates:
            self.value = updates["value"]

        # Final validation of the complete state
        self._validate_update()

    def _validate_update(self) -> None:
        """Optional method to validate the update after all attributes have been set."""
        pass


@dataclass(init=False)
class TextParameter(Parameter[str]):
    def __init__(self, name: str, value: str):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> str:
        return str(new_value)


@dataclass(init=False)
class SelectionParameter(Parameter[Any]):
    options: List[Any]

    def __init__(self, name: str, value: Any, options: List[Any]):
        self.name = name
        self.options = options
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> Any:
        if new_value not in self.options:
            raise ValueError(f"Value {new_value} not in options: {self.options}")
        return new_value

    def _validate_update(self) -> None:
        if not isinstance(self.options, (list, tuple)):
            raise TypeError(f"Options for parameter {self.name} are not a list or tuple: {self.options}")
        if self.value not in self.options:
            warn(f"Value {self.value} not in options: {self.options}, setting to first option")
            self.value = self.options[0]


@dataclass(init=False)
class MultipleSelectionParameter(Parameter[List[Any]]):
    options: List[Any]

    def __init__(self, name: str, value: List[Any], options: List[Any]):
        self.name = name
        self.options = options
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> List[Any]:
        if not isinstance(new_value, (list, tuple)):
            raise TypeError(f"Expected list or tuple, got {type(new_value)}")
        if not all(val in self.options for val in new_value):
            invalid = [val for val in new_value if val not in self.options]
            raise ValueError(f"Values {invalid} not in options: {self.options}")
        return list(new_value)

    def _validate_update(self) -> None:
        if not isinstance(self.value, (list, tuple)):
            warn(f"For parameter {self.name}, value {self.value} is not a list or tuple. Setting to empty list.")
            self.value = []
        if not all(val in self.options for val in self.value):
            invalid = [val for val in self.value if val not in self.options]
            warn(f"For parameter {self.name}, value {self.value} contains invalid options: {invalid}. Setting to empty list.")
            self.value = []


@dataclass(init=False)
class BooleanParameter(Parameter[bool]):
    def __init__(self, name: str, value: bool = True):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> bool:
        return bool(new_value)


@dataclass(init=False)
class NumericParameter(Parameter[T], ABC):
    min_value: T
    max_value: T
    _param_type: type = None  # Will be overridden by subclasses

    def _validate_update(self) -> None:
        self.min_value = self._validate(self.min_value, compare_to_range=False)
        self.max_value = self._validate(self.max_value, compare_to_range=False)
        self.value = self._validate(self.value)
        if self.min_value > self.max_value:
            warn(f"For parameter {self.name}, minimum value {self.min_value} is greater than maximum value {self.max_value}. Switching values.")
            self.min_value, self.max_value = self.max_value, self.min_value

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> T:
        try:
            value = self._param_type(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to {self._param_type.__name__}")

        if compare_to_range:
            old_value = copy(value)
            value = max(self.min_value, value)
            value = min(self.max_value, value)
            if value != old_value:
                warn(f"For parameter {self.name}, value {old_value} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {value}.")

        return value


@dataclass(init=False)
class IntegerParameter(NumericParameter[int]):
    _param_type: type = int

    def __init__(self, name: str, value: int, min_value: int, max_value: int):
        self.name = name
        self.min_value = self._validate(min_value, compare_to_range=False)
        self.max_value = self._validate(max_value, compare_to_range=False)
        self._value = self._validate(value)


@dataclass(init=False)
class FloatParameter(NumericParameter[float]):
    step: float
    _param_type: type = float

    def __init__(self, name: str, value: float, min_value: float, max_value: float, step: float = 0.1):
        self.name = name
        self.min_value = self._validate(min_value, compare_to_range=False)
        self.max_value = self._validate(max_value, compare_to_range=False)
        self.step = step
        self._value = self._validate(value)

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> T:
        try:
            value = self._param_type(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to {self._param_type.__name__}")

        if compare_to_range:
            old_value = copy(value)
            value = max(self.min_value, value)
            value = min(self.max_value, value)
            if value != old_value:
                warn(f"For parameter {self.name}, value {old_value} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {value}.")
            old_value = copy(value)
            value = round(value / self.step) * self.step
            if value != old_value:
                warn(f"For parameter {self.name}, value {old_value} is not a multiple of {self.step}. Rounding to {value}.")

        return value


@dataclass(init=False)
class PairParameter(Parameter[Tuple[T, T]], ABC):
    min_value: T
    max_value: T
    _param_type: type = None  # Will be overridden by subclasses

    def _validate_update(self) -> None:
        self.min_value, self.max_value = self._validate((self.min_value, self.max_value), compare_to_range=False)
        self.value = self._validate(self.value)
        if self.min_value > self.max_value:
            warn(f"For parameter {self.name}, minimum value {self.min_value} is greater than maximum value {self.max_value}. Switching values.")
            self.min_value, self.max_value = self.max_value, self.min_value

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> Tuple[int, int]:
        if not isinstance(new_value, (list, tuple)):
            raise TypeError(f"Expected list or tuple, got {type(new_value)}")
        try:
            values = (self._param_type(new_value[0]), self._param_type(new_value[1]))
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to {self._param_type.__name__} pair")

        if compare_to_range:
            if values[0] > values[1]:
                warn(f"For parameter {self.name}, values were not sorted. Swapping {values[0]} and {values[1]}.")
                values = (values[1], values[0])
            old_values = copy(values)
            values = (max(self.min_value, values[0]), max(self.min_value, values[1]))
            values = (min(self.max_value, values[0]), min(self.max_value, values[1]))
            if values != old_values:
                warn(
                    f"For parameter {self.name}, values {old_values} are not in the range [{self.min_value}, {self.max_value}]. Clamping to {values}."
                )
        return values


@dataclass(init=False)
class IntegerPairParameter(PairParameter[int]):
    _param_type: type = int

    def __init__(self, name: str, value: Tuple[int, int], min_value: int, max_value: int):
        self.name = name
        self.min_value, self.max_value = self._validate((min_value, max_value), compare_to_range=False)
        self._value = self._validate(value)


@dataclass(init=False)
class FloatPairParameter(PairParameter[float]):
    step: float
    _param_type: type = float

    def __init__(
        self,
        name: str,
        value: Tuple[float, float],
        min_value: float = None,
        max_value: float = None,
        step: float = 0.1,
    ):
        self.name = name
        self.min_value, self.max_value = self._validate((min_value, max_value), compare_to_range=False)
        self._value = self._validate(value)
        self.step = step


@dataclass(init=False)
class UnboundedNumericParameter(Parameter[T], ABC):
    min_value: Optional[T]
    max_value: Optional[T]
    _param_type: type = None  # Will be overridden by subclasses

    def _validate_update(self) -> None:
        if self.min_value is not None:
            self.min_value = self._validate(self.min_value, compare_to_range=False)
        if self.max_value is not None:
            self.max_value = self._validate(self.max_value, compare_to_range=False)
        self.value = self._validate(self.value)
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            warn(f"For parameter {self.name}, minimum value {self.min_value} is greater than maximum value {self.max_value}. Switching values.")
            self.min_value, self.max_value = self.max_value, self.min_value

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> T:
        try:
            value = self._param_type(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to {self._param_type.__name__}")

        if compare_to_range:
            old_value = copy(value)
            if self.min_value is not None:
                value = max(self.min_value, value)
            if self.max_value is not None:
                value = min(self.max_value, value)
            if value != old_value:
                warn(f"For parameter {self.name}, value {old_value} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {value}.")

        return value


@dataclass(init=False)
class UnboundedIntegerParameter(UnboundedNumericParameter[int]):
    _param_type: type = int

    def __init__(
        self,
        name: str,
        value: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        super().__init__(name, value, min_value, max_value)


@dataclass(init=False)
class UnboundedFloatParameter(UnboundedNumericParameter[float]):
    step: Optional[float]  # None means no step constraint
    _param_type: type = float

    def __init__(
        self,
        name: str,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
    ):
        super().__init__(name, value, min_value, max_value)
        self.step = step

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> T:
        try:
            value = self._param_type(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to {self._param_type.__name__}")

        if self.step is not None:
            value = round(value / self.step) * self.step

        if compare_to_range:
            old_value = copy(value)
            if self.min_value is not None:
                value = max(self.min_value, value)
            if self.max_value is not None:
                value = min(self.max_value, value)
            if value != old_value:
                warn(f"For parameter {self.name}, value {old_value} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {value}.")

        return value


class ParameterType(Enum):
    text = TextParameter
    selection = SelectionParameter
    multiple_selection = MultipleSelectionParameter
    boolean = BooleanParameter
    integer = IntegerParameter
    float = FloatParameter
    integer_pair = IntegerPairParameter
    float_pair = FloatPairParameter
    unbounded_integer = UnboundedIntegerParameter
    unbounded_float = UnboundedFloatParameter
