from typing import List, Any, Tuple, Generic, TypeVar, Optional, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from copy import deepcopy
from warnings import warn

T = TypeVar("T")


# Keep original Parameter class and exceptions unchanged
class ParameterAddError(Exception):
    """
    Exception raised when there is an error creating a new parameter.

    Parameters
    ----------
    parameter_name : str
        Name of the parameter that failed to be created
    parameter_type : str
        Type of the parameter that failed to be created
    message : str, optional
        Additional error details
    """

    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(
            f"Failed to create {parameter_type} parameter '{parameter_name}'"
            + (f": {message}" if message else "")
        )


class ParameterUpdateError(Exception):
    """
    Exception raised when there is an error updating an existing parameter.

    Parameters
    ----------
    parameter_name : str
        Name of the parameter that failed to update
    parameter_type : str
        Type of the parameter that failed to update
    message : str, optional
        Additional error details
    """

    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(
            f"Failed to update {parameter_type} parameter '{parameter_name}'"
            + (f": {message}" if message else "")
        )


def get_parameter_attributes(param_class) -> List[str]:
    """
    Get all valid attributes for a parameter class.

    Parameters
    ----------
    param_class : class
        The parameter class to inspect

    Returns
    -------
    list of str
        Names of all valid attributes for the parameter class
    """
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
    """
    Base class for all parameter types. Parameters are the building blocks
    for creating interactive GUI elements.

    Each parameter has a name and a value, and ensures the value stays valid
    through validation rules.

    Parameters
    ----------
    name : str
        The name of the parameter, used as a label in the GUI
    value : T
        The current value of the parameter

    Notes
    -----
    This is an abstract base class - you should use one of the concrete parameter
    types like TextParameter, BooleanParameter, etc. instead of using this directly.
    """

    name: str
    value: T

    @abstractmethod
    def __init__(self, name: str, value: T):
        raise NotImplementedError("Need to define in subclass for proper IDE support")

    @property
    def value(self) -> T:
        """
        Get the current value of the parameter.

        Returns
        -------
        T
            The current value
        """
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """
        Set a new value for the parameter. The value will be validated before being set.

        Parameters
        ----------
        new_value : T
            The new value to set

        Raises
        ------
        ValueError
            If the new value is invalid for this parameter type
        """
        self._value = self._validate(new_value)

    @abstractmethod
    def _validate(self, new_value: Any) -> T:
        raise NotImplementedError

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Safely update multiple parameter attributes at once.

        Parameters
        ----------
        updates : dict
            Dictionary of attribute names and their new values

        Raises
        ------
        ParameterUpdateError
            If any of the updates are invalid

        Examples
        --------
        >>> param = FloatParameter("temperature", 20.0, min_value=0, max_value=100)
        >>> param.update({"value": 25.0, "max_value": 150})
        """
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
        """
        Internal update method that applies changes without safety copies.

        Validates attribute names but applies updates directly to instance.
        Called by public update() method inside a deepcopy context.

        Args:
            updates: Dict mapping attribute names to new values

        Raises:
            ValueError: If trying to update 'name' or invalid attributes
        """
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
        """
        Hook for validating complete parameter state after updates.

        Called at end of _unsafe_update(). Default implementation does nothing.
        Override in subclasses to add validation logic.
        """
        pass


@dataclass(init=False)
class TextParameter(Parameter[str]):
    """
    Parameter for text input.

    Creates a text box in the GUI that accepts any string input.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_text` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_text` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : str
        The initial text value

    Examples
    --------
    >>> name_param = TextParameter("username", "Alice")
    >>> name_param.value
    'Alice'
    >>> name_param.update({"value": "Bob"})
    >>> name_param.value
    'Bob'
    """

    def __init__(self, name: str, value: str):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> str:
        """
        Convert input to string.

        Args:
            new_value: Value to convert

        Returns:
            String representation of input value
        """
        return str(new_value)


@dataclass(init=False)
class BooleanParameter(Parameter[bool]):
    """
    Parameter for boolean values.

    Creates a checkbox in the GUI that can be toggled on/off.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_boolean` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_boolean` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : bool, optional
        The initial state (default is True)

    Examples
    --------
    >>> active = BooleanParameter("is_active", True)
    >>> active.value
    True
    >>> active.update({"value": False})
    >>> active.value
    False
    """

    def __init__(self, name: str, value: bool = True):
        self.name = name
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> bool:
        """
        Convert input to boolean.

        Args:
            new_value: Value to convert

        Returns:
            Boolean interpretation of input value using Python's bool() rules
        """
        return bool(new_value)


@dataclass(init=False)
class SelectionParameter(Parameter[Any]):
    """
    Parameter for single selection from a list of options.

    Creates a dropdown menu in the GUI where users can select one option.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_selection` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_selection` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Any
        The initially selected value (must be one of the options)
    options : list
        List of valid choices that can be selected

    Examples
    --------
    >>> color = SelectionParameter("color", "red", options=["red", "green", "blue"])
    >>> color.value
    'red'
    >>> color.update({"value": "blue"})
    >>> color.value
    'blue'
    >>> color.update({"value": "yellow"})  # This will raise an error
    """

    options: List[Any]

    def __init__(self, name: str, value: Any, options: List[Any]):
        self.name = name
        self.options = options
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> Any:
        """
        Validate that value is one of the allowed options.

        Args:
            new_value: Value to validate

        Returns:
            Input value if valid

        Raises:
            ValueError: If value is not in options list
        """
        if new_value not in self.options:
            raise ValueError(f"Value {new_value} not in options: {self.options}")
        return new_value

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures options is a list/tuple and current value is valid.
        Sets value to first option if current value becomes invalid.

        Raises:
            TypeError: If options is not a list or tuple
        """
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
    """
    Parameter for multiple selections from a list of options.

    Creates a set of checkboxes or multi-select dropdown in the GUI.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_multiple_selection` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_multiple_selection` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : list
        List of initially selected values (must all be from options)
    options : list
        List of valid choices that can be selected

    Examples
    --------
    >>> toppings = MultipleSelectionParameter("pizza_toppings",
    ...     value=["cheese", "mushrooms"],
    ...     options=["cheese", "mushrooms", "pepperoni", "olives"])
    >>> toppings.value
    ['cheese', 'mushrooms']
    >>> toppings.update({"value": ["cheese", "pepperoni"]})
    >>> toppings.value
    ['cheese', 'pepperoni']
    """

    options: List[Any]

    def __init__(self, name: str, value: List[Any], options: List[Any]):
        self.name = name
        self.options = options
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> List[Any]:
        """
        Validate list of selected values against options.

        Ensures value is a list/tuple and all elements are in options.
        Preserves order based on options list while removing duplicates.

        Args:
            new_value: List of selected values

        Returns:
            Validated list of unique values in options order

        Raises:
            TypeError: If value is not a list/tuple
            ValueError: If any value is not in options
        """
        if not isinstance(new_value, (list, tuple)):
            raise TypeError(f"Value must be a list or tuple")
        invalid = [val for val in new_value if val not in self.options]
        if invalid:
            raise ValueError(f"Values {invalid} not in options: {self.options}")
        # Keep only unique values while preserving order based on self.options
        return [x for x in self.options if x in new_value]

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
        # Keep only unique values while preserving order based on self.options
        seen = set()
        self.options = [x for x in self.options if not (x in seen or seen.add(x))]


@dataclass(init=False)
class IntegerParameter(Parameter[int]):
    """
    Parameter for bounded integer values.

    Creates a slider in the GUI for selecting whole numbers between bounds.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_integer` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : int
        Initial value (will be clamped to fit between min_value and max_value)
    min_value : int
        Minimum allowed value
    max_value : int
        Maximum allowed value

    Examples
    --------
    >>> age = IntegerParameter("age", value=25, min_value=0, max_value=120)
    >>> age.value
    25
    >>> age.update({"value": 150})  # Will be clamped to max_value
    >>> age.value
    120
    >>> age.update({"value": -10})  # Will be clamped to min_value
    >>> age.value
    0
    """

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
        """
        Validate and convert value to integer, optionally checking bounds.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to min/max bounds

        Returns:
            Validated integer value

        Raises:
            ValueError: If value cannot be converted to int
        """
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
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
    """
    Parameter for bounded decimal numbers.

    Creates a slider in the GUI for selecting numbers between bounds.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_float` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_float` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : float
        Initial value (will be clamped to fit between min_value and max_value)
    min_value : float
        Minimum allowed value
    max_value : float
        Maximum allowed value
    step : float, optional
        Size of each increment (default is 0.1)

    Examples
    --------
    >>> temp = FloatParameter("temperature", value=98.6,
    ...     min_value=95.0, max_value=105.0, step=0.1)
    >>> temp.value
    98.6
    >>> temp.update({"value": 98.67})  # Will be rounded to nearest step
    >>> temp.value
    98.7
    >>> temp.update({"value": 110.0})  # Will be clamped to max_value
    >>> temp.value
    105.0

    Notes
    -----
    The step parameter determines how finely you can adjust the value. For example:
    - step=0.1 allows values like 1.0, 1.1, 1.2, etc.
    - step=0.01 allows values like 1.00, 1.01, 1.02, etc.
    - step=5.0 allows values like 0.0, 5.0, 10.0, etc.
    """

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
        """
        Validate and convert value to float, optionally checking bounds.

        Rounds value to nearest step increment before range checking.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to min/max bounds

        Returns:
            Validated and potentially rounded float value

        Raises:
            ValueError: If value cannot be converted to float
        """
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
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
    """
    Parameter for a range of bounded integer values.

    Creates a range slider in the GUI for selecting a range of whole numbers.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer_range` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_integer_range` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : tuple[int, int]
        Initial (low, high) values
    min_value : int
        Minimum allowed value for both low and high
    max_value : int
        Maximum allowed value for both low and high

    Examples
    --------
    >>> age_range = IntegerRangeParameter("age_range",
    ...     value=(25, 35), min_value=18, max_value=100)
    >>> age_range.value
    (25, 35)
    >>> age_range.update({"value": (35, 25)})  # Values will be swapped
    >>> age_range.value
    (25, 35)
    >>> age_range.update({"value": (15, 40)})  # Low will be clamped
    >>> age_range.value
    (18, 40)
    """

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
        """
        Validate and convert a single numeric value.

        Used by _validate() to handle each number in the range tuple.
        Does not perform range checking.

        Args:
            new_value: Value to validate

        Returns:
            Converted numeric value

        Raises:
            ValueError: If value cannot be converted to required numeric type
        """
        try:
            return int(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to int")

    def _validate(self, new_value: Any) -> Tuple[int, int]:
        """
        Validate numeric value against parameter constraints.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to min/max bounds

        Returns:
            Validated and potentially clamped value

        Raises:
            ValueError: If value cannot be converted to required numeric type
        """
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
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
    """
    Parameter for a range of bounded decimal numbers.

    Creates a range slider in the GUI for selecting a range of numbers.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_float_range` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_float_range` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : tuple[float, float]
        Initial (low, high) values
    min_value : float
        Minimum allowed value for both low and high
    max_value : float
        Maximum allowed value for both low and high
    step : float, optional
        Size of each increment (default is 0.1)

    Examples
    --------
    >>> temp_range = FloatRangeParameter("temperature_range",
    ...     value=(98.6, 100.4), min_value=95.0, max_value=105.0, step=0.1)
    >>> temp_range.value
    (98.6, 100.4)
    >>> temp_range.update({"value": (98.67, 100.0)})  # Low will be rounded
    >>> temp_range.value
    (98.7, 100.0)
    >>> temp_range.update({"value": (101.0, 99.0)})  # Values will be swapped
    >>> temp_range.value
    (99.0, 101.0)

    Notes
    -----
    The step parameter determines how finely you can adjust the values. For example:
    - step=0.1 allows values like 1.0, 1.1, 1.2, etc.
    - step=0.01 allows values like 1.00, 1.01, 1.02, etc.
    - step=5.0 allows values like 0.0, 5.0, 10.0, etc.
    """

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
        """
        Validate and convert a single numeric value.

        Used by _validate() to handle each number in the range tuple.
        Does not perform range checking.

        Args:
            new_value: Value to validate

        Returns:
            Converted numeric value

        Raises:
            ValueError: If value cannot be converted to required numeric type
        """
        try:
            new_value = float(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to float")

        # Round to the nearest step
        new_value = round(new_value / self.step) * self.step
        return new_value

    def _validate(self, new_value: Any) -> Tuple[float, float]:
        """
        Validate numeric value against parameter constraints.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to min/max bounds

        Returns:
            Validated and potentially clamped value

        Raises:
            ValueError: If value cannot be converted to required numeric type
        """
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
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
    """
    Parameter for optionally bounded integer values.

    Creates a text input box in the GUI for entering whole numbers.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_integer` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_unbounded_integer` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : int
        Initial value
    min_value : int, optional
        Minimum allowed value (or None for no minimum)
    max_value : int, optional
        Maximum allowed value (or None for no maximum)

    Examples
    --------
    >>> count = UnboundedIntegerParameter("count", value=10, min_value=0)
    >>> count.value
    10
    >>> count.update({"value": -5})  # Will be clamped to min_value
    >>> count.value
    0
    >>> count.update({"value": 1000000})  # No maximum, so this is allowed
    >>> count.value
    1000000

    Notes
    -----
    Use this instead of IntegerParameter when you:
    - Don't know a reasonable maximum value
    - Only want to enforce a minimum or maximum, but not both
    - Need to allow very large numbers that would be impractical with a slider
    """

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
        """
        Validate and convert value to integer, optionally checking bounds.

        Handles None min/max values by skipping those bound checks.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to any defined min/max bounds

        Returns:
            Validated integer value

        Raises:
            ValueError: If value cannot be converted to int
        """
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
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
    """
    Parameter for optionally bounded decimal numbers.

    Creates a text input box in the GUI for entering numbers.
    See :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_float` and
    :meth:`~syd.interactive_viewer.InteractiveViewer.update_unbounded_float` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : float
        Initial value
    min_value : float, optional
        Minimum allowed value (or None for no minimum)
    max_value : float, optional
        Maximum allowed value (or None for no maximum)
    step : float, optional
        Size of each increment (default is None, meaning no rounding)

    Examples
    --------
    >>> price = UnboundedFloatParameter("price", value=19.99, min_value=0.0, step=0.01)
    >>> price.value
    19.99
    >>> price.update({"value": -5.0})  # Will be clamped to min_value
    >>> price.value
    0.0
    >>> price.update({"value": 19.987})  # Will be rounded to step
    >>> price.value
    19.99

    Notes
    -----
    Use this instead of FloatParameter when you:
    - Don't know a reasonable maximum value
    - Only want to enforce a minimum or maximum, but not both
    - Need to allow very large or precise numbers that would be impractical with a slider

    If step is provided, values will be rounded:
    - step=0.1 rounds to 1.0, 1.1, 1.2, etc.
    - step=0.01 rounds to 1.00, 1.01, 1.02, etc.
    - step=5.0 rounds to 0.0, 5.0, 10.0, etc.
    """

    min_value: Optional[float]
    max_value: Optional[float]
    step: float

    def __init__(
        self,
        name: str,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
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
        """
        Validate and convert value to float, optionally checking bounds.

        Handles None min/max values by skipping those bound checks.
        Only rounds to step if step is not None.

        Args:
            new_value: Value to validate
            compare_to_range: If True, clamps value to any defined min/max bounds

        Returns:
            Validated and potentially rounded float value

        Raises:
            ValueError: If value cannot be converted to float
        """
        try:
            new_value = float(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to float")

        # Round to the nearest step if step is defined
        if self.step is not None:
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
        """
        Validate complete parameter state after updates.

        Ensures min_value <= max_value, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            warn(f"Min value greater than max value, swapping")
            self.min_value, self.max_value = self.max_value, self.min_value
        self.value = self._validate(self.value)


class ButtonParameter(Parameter):
    """A parameter that represents a clickable button."""

    _is_button: bool = True

    def __init__(self, name: str, label: str, callback: Callable[[], None]):
        """
        Initialize a button parameter.

        Args:
            name: Internal name of the parameter
            label: Text to display on the button
            callback: Function to call when button is clicked
        """
        self.name = name
        self.label = label
        self.callback = callback
        self._value = None  # Buttons don't have a value in the traditional sense

    def update(self, updates: Dict[str, Any]) -> None:
        """Update the button's label and/or callback."""
        if "label" in updates:
            self.label = updates["label"]
        if "callback" in updates:
            self.callback = updates["callback"]

    @property
    def value(self) -> None:
        """Buttons don't have a value, always returns None."""
        return self._value

    @value.setter
    def value(self, _: Any) -> None:
        """Buttons don't store values."""
        pass

    def _validate_update(self) -> None:
        """Buttons don't need validation."""
        pass

    def _validate(self, new_value: Any) -> None:
        """Buttons don't need validation."""
        pass


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
    button = ButtonParameter
