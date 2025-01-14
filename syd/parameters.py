from typing import List, Any, Tuple, Generic, TypeVar, cast
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from warnings import warn

T = TypeVar("T")


@dataclass
class Parameter(Generic[T], ABC):
    """Abstract base class for parameters that should not be instantiated directly."""

    name: str

    @abstractmethod
    def __init__(self, name: str, default: T):
        raise NotImplementedError("Need to define in subclass for proper IDE support")

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T):
        self._value = self._validate(new_value)

    @abstractmethod
    def _validate(self, new_value: Any) -> T:
        raise NotImplementedError


@dataclass(init=False)
class TextParameter(Parameter[str]):
    def __init__(self, name: str, default: str):
        self.name = name
        self.default = default
        self._value = self._validate(default)

    def _validate(self, new_value: Any) -> str:
        return str(new_value)


@dataclass(init=False)
class SingleSelectionParameter(Parameter[Any]):
    options: List[Any]

    def __init__(self, name: str, options: List[Any], default: Any = None):
        self.name = name
        self.options = options
        self.default = default or options[0]
        self._value = self._validate(self.default)

    def _validate(self, new_value: Any) -> Any:
        if new_value not in self.options:
            raise ValueError(f"Value {new_value} not in options: {self.options}")
        return new_value


@dataclass(init=False)
class MultipleSelectionParameter(Parameter[List[Any]]):
    options: List[Any]

    def __init__(self, name: str, options: List[Any], default: List[Any] = None):
        self.name = name
        self.default = default or []
        self.options = options
        self._value = self._validate(self.default)

    def _validate(self, new_value: List[Any]) -> List[Any]:
        if not isinstance(new_value, (list, tuple)):
            raise TypeError(f"Expected list or tuple, got {type(new_value)}")
        if not all(val in self.options for val in new_value):
            invalid = [val for val in new_value if val not in self.options]
            raise ValueError(f"Values {invalid} not in options: {self.options}")
        return list(new_value)


@dataclass(init=False)
class BooleanParameter(Parameter[bool]):
    def __init__(self, name: str, default: bool = True):
        self.name = name
        self.default = default
        self._value = self._validate(default)

    def _validate(self, new_value: Any) -> bool:
        return bool(new_value)


@dataclass(init=False)
class NumericParameter(Parameter[T], ABC):
    min_value: T
    max_value: T

    def __init__(self, name: str, min_value: T = None, max_value: T = None, default: T = 0):
        self.name = name
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self._value = self._validate(default)

    @abstractmethod
    def _validate(self, new_value: Any) -> T:
        # Subclasses must implement this
        raise NotImplementedError


@dataclass(init=False)
class IntegerParameter(NumericParameter[int]):
    def __init__(self, name: str, min_value: int = None, max_value: int = None, default: int = 0):
        self.name = name
        try:
            self.min_value = int(min_value)
            self.max_value = int(max_value)
        except TypeError as e:
            raise TypeError(f"Cannot convert {min_value} and {max_value} to integer") from e
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"Minimum value {self.min_value} is greater than maximum value {self.max_value}")
        valid_default = self._validate(default)
        if valid_default != default:
            warn(f"Default value {default} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {valid_default}.")
        self.default = valid_default
        self._value = self._validate(self.default)

    def _validate(self, new_value: Any) -> int:
        try:
            value = int(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to integer")

        if self.min_value is not None:
            value = max(self.min_value, value)
        if self.max_value is not None:
            value = min(self.max_value, value)
        return value


@dataclass(init=False)
class FloatParameter(NumericParameter[float]):
    step: float

    def __init__(self, name: str, min_value: float = None, max_value: float = None, default: float = 0.0, step: float = 0.1):
        self.name = name
        self.default = default
        try:
            self.min_value = float(min_value)
            self.max_value = float(max_value)
        except TypeError as e:
            raise TypeError(f"Cannot convert {min_value} and {max_value} to float") from e
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"Minimum value {self.min_value} is greater than maximum value {self.max_value}")
        self.step = step
        valid_default = self._validate(default)
        if valid_default != default:
            warn(f"Default value {default} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {valid_default}.")
        self.default = valid_default
        self._value = self._validate(self.default)

    def _validate(self, new_value: Any) -> float:
        try:
            value = float(new_value)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to float")

        if self.min_value is not None:
            value = max(self.min_value, value)
        if self.max_value is not None:
            value = min(self.max_value, value)
        return value


@dataclass(init=False)
class PairParameter(Parameter[Tuple[T, T]], ABC):
    min_value: T
    max_value: T
    default: Tuple[T, T]

    @abstractmethod
    def __init__(self, name: str, default: Tuple[T, T], min_value: T = None, max_value: T = None):
        raise NotImplementedError("Need to define in subclass for proper IDE support")

    @abstractmethod
    def _validate_value(self, value: Any) -> T:
        raise NotImplementedError


@dataclass(init=False)
class IntegerPairParameter(PairParameter[int]):
    def __init__(self, name: str, default: Tuple[int, int], min_value: int = None, max_value: int = None):
        self.name = name
        try:
            self.min_value = int(min_value)
            self.max_value = int(max_value)
        except TypeError as e:
            raise TypeError(f"Cannot convert {min_value} and {max_value} to integer") from e
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"Minimum value {self.min_value} is greater than maximum value {self.max_value}")
        valid_default = self._validate(default)
        if valid_default != default:
            warn(f"Default value {default} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {valid_default}.")
        self.default = valid_default
        self._value = self._validate(self.default)

    def _validate(self, new_value: Tuple[Any, Any]) -> Tuple[int, int]:
        try:
            values = (int(new_value[0]), int(new_value[1]))
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to integer pair")

        if self.min_value is not None:
            values = (max(self.min_value, values[0]), max(self.min_value, values[1]))
        if self.max_value is not None:
            values = (min(self.max_value, values[0]), min(self.max_value, values[1]))
        return values


@dataclass(init=False)
class FloatPairParameter(PairParameter[float]):
    step: float

    def __init__(
        self,
        name: str,
        default: Tuple[float, float],
        min_value: float = None,
        max_value: float = None,
        step: float = 0.1,
    ):
        self.name = name
        try:
            self.min_value = float(min_value)
            self.max_value = float(max_value)
        except TypeError as e:
            raise TypeError(f"Cannot convert {min_value} and {max_value} to float") from e
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"Minimum value {self.min_value} is greater than maximum value {self.max_value}")
        valid_default = self._validate(default)
        if valid_default != default:
            warn(f"Default value {default} is not in the range [{self.min_value}, {self.max_value}]. Clamping to {valid_default}.")
        self.default = valid_default
        self.step = step
        self._value = self._validate(self.default)

    def _validate(self, new_value: Tuple[Any, Any]) -> Tuple[float, float]:
        try:
            values = (float(new_value[0]), float(new_value[1]))
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to float pair")

        if self.min_value is not None:
            values = (max(self.min_value, values[0]), max(self.min_value, values[1]))
        if self.max_value is not None:
            values = (min(self.max_value, values[0]), min(self.max_value, values[1]))
        return values


class ParameterType(Enum):
    text = TextParameter
    selection = SingleSelectionParameter
    multiple_selection = MultipleSelectionParameter
    boolean = BooleanParameter
    integer = IntegerParameter
    float = FloatParameter
    integer_pair = IntegerPairParameter
    float_pair = FloatPairParameter
