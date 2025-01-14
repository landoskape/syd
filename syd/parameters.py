from typing import List, Any, Tuple, Generic, TypeVar, Union, cast
from dataclasses import dataclass
from enum import Enum

T = TypeVar("T")


@dataclass
class Parameter(Generic[T]):
    """Abstract base class for parameters that should not be instantiated directly."""

    def __new__(cls, *args, **kwargs):
        if cls is Parameter:
            raise TypeError("Cannot instantiate abstract Parameter class directly")
        return super().__new__(cls)

    name: str
    default: T

    def __post_init__(self):
        self._value = self.default

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T):
        self._value = self._validate(new_value)

    def _validate(self, new_value: Any) -> T:
        return new_value


@dataclass
class TextParameter(Parameter[str]):
    default: str = ""

    def _validate(self, new_value: Any) -> str:
        return str(new_value)


@dataclass(init=False)
class SingleSelectionParameter(Parameter[Any]):
    options: List[Any]

    def __init__(self, name: str, options: List[Any], default: Any = None):
        if default is None and options:
            default = options[0]
        super().__init__(name=name, default=default)
        self.options = options

    def _validate(self, new_value: Any) -> Any:
        if new_value not in self.options:
            raise ValueError(f"Value {new_value} not in options: {self.options}")
        return new_value


@dataclass(init=False)
class MultipleSelectionParameter(Parameter[List[Any]]):
    options: List[Any]

    def __init__(self, name: str, options: List[Any], default: List[Any] = None):
        super().__init__(name=name, default=default or [])
        self.options = options

    def _validate(self, new_value: List[Any]) -> List[Any]:
        if not isinstance(new_value, (list, tuple)):
            raise TypeError(f"Expected list or tuple, got {type(new_value)}")
        if not all(val in self.options for val in new_value):
            invalid = [val for val in new_value if val not in self.options]
            raise ValueError(f"Values {invalid} not in options: {self.options}")
        return list(new_value)


@dataclass
class BooleanParameter(Parameter[bool]):
    default: bool = False

    def _validate(self, new_value: Any) -> bool:
        return bool(new_value)


@dataclass
class NumericParameter(Parameter[T]):
    min_value: T = None
    max_value: T = None

    @property
    def value(self) -> T:
        return super().value

    @value.setter
    def value(self, new_value: T):
        self._value = self._validate(new_value)

    def _validate(self, new_value: Any) -> T:
        # Subclasses must implement this
        raise NotImplementedError


@dataclass
class IntegerParameter(NumericParameter[int]):
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


@dataclass
class FloatParameter(NumericParameter[float]):
    step: float = 0.1

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


@dataclass
class PairParameter(Parameter[Tuple[T, T]]):
    min_value: T = None
    max_value: T = None
    default_low: T = None
    default_high: T = None

    def __post_init__(self):
        self._value = (self.default_low, self.default_high)

    def _validate(self, new_value: Tuple[Any, Any]) -> Tuple[T, T]:
        if not isinstance(new_value, (tuple, list)) or len(new_value) != 2:
            raise TypeError(f"Expected tuple of length 2, got {new_value}")
        # Subclasses must implement actual validation
        return cast(Tuple[T, T], tuple(new_value))


@dataclass
class IntegerPairParameter(PairParameter[int]):
    def _validate(self, new_value: Tuple[Any, Any]) -> Tuple[int, int]:
        validated = super()._validate(new_value)
        try:
            values = (int(validated[0]), int(validated[1]))
        except (TypeError, ValueError):
            raise TypeError(f"Cannot convert {new_value} to integer pair")

        if self.min_value is not None:
            values = (max(self.min_value, values[0]), max(self.min_value, values[1]))
        if self.max_value is not None:
            values = (min(self.max_value, values[0]), min(self.max_value, values[1]))
        return values


@dataclass
class FloatPairParameter(PairParameter[float]):
    step: float = 0.1

    def _validate(self, new_value: Tuple[Any, Any]) -> Tuple[float, float]:
        validated = super()._validate(new_value)
        try:
            values = (float(validated[0]), float(validated[1]))
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
