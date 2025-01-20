from typing import List, Any, Tuple, Generic, TypeVar, Optional, Dict, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from copy import deepcopy
from warnings import warn

T = TypeVar("T")


# Keep original Parameter class and exceptions unchanged
class ParameterAddError(Exception):
    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(
            f"Failed to create {parameter_type} parameter '{parameter_name}'"
            + (f": {message}" if message else "")
        )


class ParameterUpdateError(Exception):
    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(
            f"Failed to update {parameter_type} parameter '{parameter_name}'"
            + (f": {message}" if message else "")
        )


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
    """Base parameter class with safe update functionality."""

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
        """Update parameter attributes while respecting validation rules."""
        param_copy = deepcopy(self)

        try:
            param_copy._unsafe_update(updates)

            for key, value in vars(param_copy).items():
                if not key.startswith("_"):
                    setattr(self, key, value)
            self.value = param_copy.value

        except Exception as e:
            if isinstance(e, ValueError):
                raise ParameterUpdateError(
                    self.name, type(self).__name__, str(e)
                ) from e
            else:
                raise ParameterUpdateError(
                    self.name, type(self).__name__, f"Update failed: {str(e)}"
                ) from e

    def _unsafe_update(self, updates: Dict[str, Any]) -> None:
        """Internal method to apply updates without safety mechanisms."""
        valid_attributes = get_parameter_attributes(type(self))

        for key, new_value in updates.items():
            if key == "name":
                raise ValueError("Cannot update parameter name")
            elif key not in valid_attributes:
                raise ValueError(f"Update failed, {key} is not a valid attribute")

        for key, new_value in updates.items():
            if key != "value":
                setattr(self, key, new_value)

        if "value" in updates:
            self.value = updates["value"]

        self._validate_update()

    def _validate_update(self) -> None:
        """Optional method to validate the complete state after an update."""
        pass


@dataclass(init=False)
class TextParameter(Parameter[str]):
    def __init__(self, name: str, value: str):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> str:
        return str(new_value)


@dataclass(init=False)
class BooleanParameter(Parameter[bool]):
    def __init__(self, name: str, value: bool = True):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> bool:
        return bool(new_value)


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
            raise TypeError(
                f"Options for parameter {self.name} are not a list or tuple: {self.options}"
            )
        if self.value not in self.options:
            warn(
                f"Value {self.value} not in options: {self.options}, setting to first option"
            )
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
            raise TypeError(f"Value must be a list or tuple")
        invalid = [val for val in new_value if val not in self.options]
        if invalid:
            raise ValueError(f"Values {invalid} not in options: {self.options}")
        return list(new_value)

    def _validate_update(self) -> None:
        if not isinstance(self.options, (list, tuple)):
            raise TypeError(
                f"Options for parameter {self.name} are not a list or tuple: {self.options}"
            )
        if not isinstance(self.value, (list, tuple)):
            warn(
                f"For parameter {self.name}, value {self.value} is not a list or tuple. Setting to empty list."
            )
            self.value = []
        if not all(val in self.options for val in self.value):
            invalid = [val for val in self.value if val not in self.options]
            warn(
                f"For parameter {self.name}, value {self.value} contains invalid options: {invalid}. Setting to empty list."
            )
            self.value = []


@dataclass(init=False)
class IntegerParameter(Parameter[int]):
    min_value: int
    max_value: int

    def __init__(
        self,
        name: str,
        value: int,
        min_value: int,
        max_value: int,
    ):
        self.name = name
        self.min_value = self._validate(min_value, compare_to_range=False)
        self.max_value = self._validate(max_value, compare_to_range=False)
        self._value = self._validate(value)

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> int:
        try:
            new_value = int(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to int")

        if compare_to_range:
            if new_value < self.min_value:
                warn(f"Value {new_value} below minimum {self.min_value}, clamping")
                new_value = self.min_value
            if new_value > self.max_value:
                warn(f"Value {new_value} above maximum {self.max_value}, clamping")
                new_value = self.max_value
        return int(new_value)

    def _validate_update(self) -> None:
        if self.min_value is None or self.max_value is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "IntegerParameter must have both min_value and max_value bounds",
            )
        if self.min_value > self.max_value:
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


@dataclass(init=False)
class FloatParameter(Parameter[float]):
    min_value: float
    max_value: float
    step: float

    def __init__(
        self,
        name: str,
        value: float,
        min_value: float,
        max_value: float,
        step: float = 0.1,
    ):
        self.name = name
        self.step = step
        self.min_value = self._validate(min_value, compare_to_range=False)
        self.max_value = self._validate(max_value, compare_to_range=False)
        self._value = self._validate(value)

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> float:
        try:
            new_value = float(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to float")

        # Round to the nearest step
        new_value = round(new_value / self.step) * self.step

        if compare_to_range:
            if new_value < self.min_value:
                warn(f"Value {new_value} below minimum {self.min_value}, clamping")
                new_value = self.min_value
            if new_value > self.max_value:
                warn(f"Value {new_value} above maximum {self.max_value}, clamping")
                new_value = self.max_value

        return float(new_value)

    def _validate_update(self) -> None:
        if self.min_value is None or self.max_value is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "FloatParameter must have both min_value and max_value bounds",
            )
        if self.min_value > self.max_value:
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


@dataclass(init=False)
class IntegerRangeParameter(Parameter[Tuple[int, int]]):
    min_value: int
    max_value: int

    def __init__(
        self,
        name: str,
        value: Tuple[int, int],
        min_value: int,
        max_value: int,
    ):
        self.name = name
        self.min_value = self._validate_single(min_value)
        self.max_value = self._validate_single(max_value)
        self._value = self._validate(value)

    def _validate_single(self, new_value: Any) -> int:
        """Validate a single number value."""
        try:
            return int(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to int")

    def _validate(self, new_value: Any) -> Tuple[int, int]:
        if not isinstance(new_value, (tuple, list)) or len(new_value) != 2:
            raise ValueError("Value must be a tuple of (low, high)")

        low = self._validate_single(new_value[0])
        high = self._validate_single(new_value[1])

        if low > high:
            warn(f"Low value {low} greater than high value {high}, swapping")
            low, high = high, low

        if low < self.min_value:
            warn(f"Low value {low} below minimum {self.min_value}, clamping")
            low = self.min_value
        if high > self.max_value:
            warn(f"High value {high} above maximum {self.max_value}, clamping")
            high = self.max_value

        return (low, high)

    def _validate_update(self) -> None:
        if self.min_value is None or self.max_value is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "IntegerRangeParameter must have both min_value and max_value bounds",
            )
        if self.min_value > self.max_value:
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


@dataclass(init=False)
class FloatRangeParameter(Parameter[Tuple[float, float]]):
    min_value: float
    max_value: float
    step: float

    def __init__(
        self,
        name: str,
        value: Tuple[float, float],
        min_value: float,
        max_value: float,
        step: float = 0.1,
    ):
        self.name = name
        self.step = step
        self.min_value = self._validate_single(min_value)
        self.max_value = self._validate_single(max_value)
        self._value = self._validate(value)

    def _validate_single(self, new_value: Any) -> float:
        """Validate a single number value."""
        try:
            new_value = float(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to float")

        # Round to the nearest step
        new_value = round(new_value / self.step) * self.step
        return new_value

    def _validate(self, new_value: Any) -> Tuple[float, float]:
        if not isinstance(new_value, (tuple, list)) or len(new_value) != 2:
            raise ValueError("Value must be a tuple of (low, high)")

        low = self._validate_single(new_value[0])
        high = self._validate_single(new_value[1])

        if low > high:
            warn(f"Low value {low} greater than high value {high}, swapping")
            low, high = high, low

        if low < self.min_value:
            warn(f"Low value {low} below minimum {self.min_value}, clamping")
            low = self.min_value
        if high > self.max_value:
            warn(f"High value {high} above maximum {self.max_value}, clamping")
            high = self.max_value

        return (low, high)

    def _validate_update(self) -> None:
        if self.min_value is None or self.max_value is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "FloatRangeParameter must have both min_value and max_value bounds",
            )
        if self.min_value > self.max_value:
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


@dataclass(init=False)
class UnboundedIntegerParameter(Parameter[int]):
    min_value: Optional[int]
    max_value: Optional[int]

    def __init__(
        self,
        name: str,
        value: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        self.name = name
        self.min_value = (
            self._validate(min_value, compare_to_range=False)
            if min_value is not None
            else None
        )
        self.max_value = (
            self._validate(max_value, compare_to_range=False)
            if max_value is not None
            else None
        )
        self._value = self._validate(value)

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> int:
        try:
            new_value = int(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to int")

        if compare_to_range:
            if self.min_value is not None and new_value < self.min_value:
                warn(f"Value {new_value} below minimum {self.min_value}, clamping")
                new_value = self.min_value
            if self.max_value is not None and new_value > self.max_value:
                warn(f"Value {new_value} above maximum {self.max_value}, clamping")
                new_value = self.max_value
        return int(new_value)

    def _validate_update(self) -> None:
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


@dataclass(init=False)
class UnboundedFloatParameter(Parameter[float]):
    min_value: Optional[float]
    max_value: Optional[float]
    step: float

    def __init__(
        self,
        name: str,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: float = 0.1,
    ):
        self.name = name
        self.step = step
        self.min_value = (
            self._validate(min_value, compare_to_range=False)
            if min_value is not None
            else None
        )
        self.max_value = (
            self._validate(max_value, compare_to_range=False)
            if max_value is not None
            else None
        )
        self._value = self._validate(value)

    def _validate(self, new_value: Any, compare_to_range: bool = True) -> float:
        try:
            new_value = float(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to float")

        # Round to the nearest step
        new_value = round(new_value / self.step) * self.step

        if compare_to_range:
            if self.min_value is not None and new_value < self.min_value:
                warn(f"Value {new_value} below minimum {self.min_value}, clamping")
                new_value = self.min_value
            if self.max_value is not None and new_value > self.max_value:
                warn(f"Value {new_value} above maximum {self.max_value}, clamping")
                new_value = self.max_value

        return float(new_value)

    def _validate_update(self) -> None:
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


class ParameterType(Enum):
    """Registry of all available parameter types."""

    text = TextParameter
    boolean = BooleanParameter
    selection = SelectionParameter
    multiple_selection = MultipleSelectionParameter
    integer = IntegerParameter
    float = FloatParameter
    integer_range = IntegerRangeParameter
    float_range = FloatRangeParameter
    unbounded_integer = UnboundedIntegerParameter
    unbounded_float = UnboundedFloatParameter
