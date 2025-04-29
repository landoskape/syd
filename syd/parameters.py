from typing import List, Any, Tuple, Generic, TypeVar, Optional, Dict, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
from copy import deepcopy

from .support import (
    NoInitialValue,
    ParameterMeta,
    ParameterUpdateError,
    get_parameter_attributes,
    warn_parameter_update,
)

T = TypeVar("T")


@dataclass
class Parameter(Generic[T], ABC, metaclass=ParameterMeta):
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
    _is_action: bool = False

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
        >>> param = FloatParameter("temperature", 20.0, min=0, max=100)
        >>> param.update({"value": 25.0, "max": 150})
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
    See :meth:`~syd.viewer.Viewer.add_text` and
    :meth:`~syd.viewer.Viewer.update_text` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[str, NoInitialValue]
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

    def __init__(self, name: str, value: Union[str, NoInitialValue]):
        self.name = name
        if isinstance(value, NoInitialValue):
            value = ""
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
    See :meth:`~syd.viewer.Viewer.add_boolean` and
    :meth:`~syd.viewer.Viewer.update_boolean` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[bool, NoInitialValue]
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

    def __init__(self, name: str, value: Union[bool, NoInitialValue]):
        self.name = name
        if isinstance(value, NoInitialValue):
            value = True
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
    See :meth:`~syd.viewer.Viewer.add_selection` and
    :meth:`~syd.viewer.Viewer.update_selection` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[Any, NoInitialValue]
        The initially selected value (must be one of the options)
    options : sequence
        List, tuple, or 1D numpy array of valid choices that can be selected

    Examples
    --------
    >>> color = SelectionParameter("color", "red", options=["red", "green", "blue"])
    >>> color.value
    'red'
    >>> color.update({"value": "blue"})
    >>> color.value
    'blue'
    >>> color.update({"value": "yellow"})  # This will raise an error
    >>> # With numpy array
    >>> import numpy as np
    >>> numbers = SelectionParameter("number", 1, options=np.array([1, 2, 3]))
    >>> numbers.value
    1
    """

    options: List[Any]

    def __init__(
        self, name: str, value: Union[Any, NoInitialValue], options: Union[List, Tuple]
    ):
        self.name = name
        self.options = self._validate_options(options)
        if isinstance(value, NoInitialValue):
            value = self.options[0]
        self._value = self._validate(value)

    def _validate_options(self, options: Any) -> List[Any]:
        """
        Validate options and convert to list if necessary.

        Parameters
        ----------
        options : list or tuple
            The options to validate

        Returns
        -------
        list
            Validated list of options

        Raises
        ------
        TypeError
            If options is not a list or tuple
        ValueError
            If any option is not hashable
        """
        if not isinstance(options, (list, tuple)):
            raise TypeError(
                f"Options for parameter {self.name} must be a list or tuple"
            )

        if not options:
            raise ValueError(f"Options for parameter {self.name} must not be empty")

        # Verify all options are hashable (needed for comparison)
        try:
            for opt in options:
                hash(opt)
        except TypeError as e:
            raise ValueError(
                f"All options for parameter {self.name} must be hashable: {str(e)}"
            )
        return list(options)

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
        # Direct check for non-float values or when new_value is exactly in options
        if new_value in self.options:
            return new_value

        # Special handling for numeric values to account for type mismatches
        if isinstance(new_value, (int, float)):
            for option in self.options:
                # For numeric options, compare as floats
                if (
                    isinstance(option, (int, float))
                    and abs(float(new_value) - float(option)) < 1e-10
                ):
                    return option
                # Also try string conversion for numeric strings
                elif isinstance(option, str):
                    try:
                        if abs(float(new_value) - float(option)) < 1e-10:
                            return option
                    except ValueError:
                        pass

        # Handle string conversion - when new_value is a string but options might be numeric
        if isinstance(new_value, str):
            try:
                # Try to convert to float if possible
                float_value = float(new_value)
                for option in self.options:
                    if (
                        isinstance(option, (int, float))
                        and abs(float_value - float(option)) < 1e-10
                    ):
                        return option
            except ValueError:
                pass

        raise ValueError(f"Value {new_value} not in options: {self.options}")

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures options is a list/tuple and current value is valid.
        Sets value to first option if current value becomes invalid.

        Raises:
            TypeError: If options is not a list or tuple
        """
        self.options = self._validate_options(self.options)

        # Check if value is directly in options
        if self.value in self.options:
            return

        # For numeric values, try flexible comparison
        value_found = False
        if isinstance(self.value, (int, float)):
            for option in self.options:
                if (
                    isinstance(option, (int, float))
                    and abs(float(self.value) - float(option)) < 1e-10
                ):
                    # Don't update self.value here as we want to keep the original type if possible
                    value_found = True
                    break
                elif isinstance(option, str):
                    try:
                        if abs(float(self.value) - float(option)) < 1e-10:
                            value_found = True
                            break
                    except ValueError:
                        pass

        # For string values that might be numeric
        if not value_found and isinstance(self.value, str):
            try:
                float_value = float(self.value)
                for option in self.options:
                    if (
                        isinstance(option, (int, float))
                        and abs(float_value - float(option)) < 1e-10
                    ):
                        value_found = True
                        break
            except ValueError:
                pass

        # If value is not found after all checks, reset to first option
        if not value_found:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Value {self.value} not in options, setting to first option ({self.options[0]})",
            )
            self.value = self.options[0]


@dataclass(init=False)
class MultipleSelectionParameter(Parameter[List[Any]]):
    """
    Parameter for multiple selections from a list of options.

    Creates a set of checkboxes or multi-select dropdown in the GUI.
    See :meth:`~syd.viewer.Viewer.add_multiple_selection` and
    :meth:`~syd.viewer.Viewer.update_multiple_selection` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[List[Any], NoInitialValue]
        List of initially selected values (must all be from options, can be empty)
    options : sequence
        List, tuple, or 1D numpy array of valid choices that can be selected

    Examples
    --------
    >>> toppings = MultipleSelectionParameter("pizza_toppings",
    ...     value=["cheese", "mushrooms"],
    ...     options=["cheese", "mushrooms", "pepperoni", "olives"])
    >>> toppings.value
    ['cheese', 'mushrooms']
    >>> # With numpy array
    >>> import numpy as np
    >>> numbers = MultipleSelectionParameter("numbers",
    ...     value=[1, 3],
    ...     options=np.array([1, 2, 3, 4]))
    >>> numbers.value
    [1, 3]
    """

    options: List[Any]

    def __init__(
        self,
        name: str,
        value: Union[List[Any], NoInitialValue],
        options: Union[List, Tuple],
    ):
        self.name = name
        self.options = self._validate_options(options)
        if isinstance(value, NoInitialValue):
            value = []
        self._value = self._validate(value)

    def _validate_options(self, options: Any) -> List[Any]:
        """
        Validate options and convert to list if necessary.

        Parameters
        ----------
        options : list or tuple
            The options to validate

        Returns
        -------
        list
            Validated list of options

        Raises
        ------
        TypeError
            If options is not a list or tuple
        ValueError
            If any option is not hashable
        """
        if not isinstance(options, (list, tuple)):
            raise TypeError(
                f"Options for parameter {self.name} must be a list or tuple, received {type(options)}"
            )

        if not options:
            raise ValueError(f"Options for parameter {self.name} must not be empty")

        # Verify all options are hashable (needed for comparison)
        try:
            for opt in options:
                hash(opt)
        except TypeError as e:
            raise ValueError(
                f"All options for parameter {self.name} must be hashable: {str(e)}"
            )
        return list(options)

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
        self.options = self._validate_options(self.options)
        if not isinstance(self.value, (list, tuple)):
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"For parameter {self.name}, value {self.value} is not a list or tuple. Setting to empty list.",
            )
            self.value = []
        if not all(val in self.options for val in self.value):
            invalid = [val for val in self.value if val not in self.options]
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"For parameter {self.name}, value {self.value} contains invalid selections: {invalid}. Setting to empty list.",
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
    See :meth:`~syd.viewer.Viewer.add_integer` and
    :meth:`~syd.viewer.Viewer.update_integer` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[int, NoInitialValue]
        Initial value (will be clamped to fit between min and max)
    min : int
        Minimum allowed value
    max : int
        Maximum allowed value

    Examples
    --------
    >>> age = IntegerParameter("age", value=25, min=0, max=120)
    >>> age.value
    25
    >>> age.update({"value": 150})  # Will be clamped to max
    >>> age.value
    120
    >>> age.update({"value": -10})  # Will be clamped to min
    >>> age.value
    0
    """

    min: int
    max: int

    def __init__(
        self,
        name: str,
        value: Union[int, NoInitialValue],
        min: int,
        max: int,
    ):
        self.name = name
        self.min = self._validate(min, compare_to_range=False)
        self.max = self._validate(max, compare_to_range=False)
        if isinstance(value, NoInitialValue):
            value = self.min
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
            if new_value < self.min:
                warn_parameter_update(
                    self.name,
                    type(self).__name__,
                    f"Value {new_value} below minimum {self.min}, clamping",
                )
                new_value = self.min
            if new_value > self.max:
                warn_parameter_update(
                    self.name,
                    type(self).__name__,
                    f"Value {new_value} above maximum {self.max}, clamping",
                )
                new_value = self.max
        return int(new_value)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures min <= max, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        if self.min is None or self.max is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "IntegerParameter must have both min and max bounds",
            )
        if self.min > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Min value greater than max value, swapping",
            )
            self.min, self.max = self.max, self.min
        self.value = self._validate(self.value)


@dataclass(init=False)
class FloatParameter(Parameter[float]):
    """
    Parameter for bounded decimal numbers.

    Creates a slider in the GUI for selecting numbers between bounds.
    See :meth:`~syd.viewer.Viewer.add_float` and
    :meth:`~syd.viewer.Viewer.update_float` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[float, NoInitialValue]
        Initial value (will be clamped to fit between min and max)
    min : float
        Minimum allowed value
    max : float
        Maximum allowed value
    step : float, optional
        Size of each increment (default is 0.001)

    Examples
    --------
    >>> temp = FloatParameter("temperature", value=98.6,
    ...     min=95.0, max=105.0, step=0.1)
    >>> temp.value
    98.6
    >>> temp.update({"value": 98.67})  # Will be rounded to nearest step
    >>> temp.value
    98.7
    >>> temp.update({"value": 110.0})  # Will be clamped to max
    >>> temp.value
    105.0

    Notes
    -----
    The step parameter determines how finely you can adjust the value. For example:
    - step=0.1 allows values like 1.0, 1.1, 1.2, etc.
    - step=0.01 allows values like 1.00, 1.01, 1.02, etc.
    - step=5.0 allows values like 0.0, 5.0, 10.0, etc.
    """

    min: float
    max: float
    step: float

    def __init__(
        self,
        name: str,
        value: Union[float, NoInitialValue],
        min: float,
        max: float,
        step: float = 0.001,
    ):
        self.name = name
        self.step = step
        self.min = self._validate(min, compare_to_range=False)
        self.max = self._validate(max, compare_to_range=False)
        if isinstance(value, NoInitialValue):
            value = self.min
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
            if new_value < self.min:
                warn_parameter_update(
                    self.name,
                    type(self).__name__,
                    f"Value {new_value} below minimum {self.min}, clamping",
                )
                new_value = self.min
            if new_value > self.max:
                warn_parameter_update(
                    self.name,
                    type(self).__name__,
                    f"Value {new_value} above maximum {self.max}, clamping",
                )
                new_value = self.max

        return float(new_value)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures min <= max, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        if self.min is None or self.max is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "FloatParameter must have both min and max bounds",
            )
        if self.min > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Min value greater than max value, swapping",
            )
            self.min, self.max = self.max, self.min
        self.value = self._validate(self.value)


@dataclass(init=False)
class IntegerRangeParameter(Parameter[Tuple[int, int]]):
    """
    Parameter for a range of bounded integer values.

    Creates a range slider in the GUI for selecting a range of whole numbers.
    See :meth:`~syd.viewer.Viewer.add_integer_range` and
    :meth:`~syd.viewer.Viewer.update_integer_range` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[Tuple[int, int], NoInitialValue]
        Initial (low, high) values
    min : int
        Minimum allowed value for both low and high
    max : int
        Maximum allowed value for both low and high

    Examples
    --------
    >>> age_range = IntegerRangeParameter("age_range",
    ...     value=(25, 35), min=18, max=100)
    >>> age_range.value
    (25, 35)
    >>> age_range.update({"value": (35, 25)})  # Values will be swapped
    >>> age_range.value
    (25, 35)
    >>> age_range.update({"value": (15, 40)})  # Low will be clamped
    >>> age_range.value
    (18, 40)
    """

    min: int
    max: int

    def __init__(
        self,
        name: str,
        value: Union[Tuple[int, int], NoInitialValue],
        min: int,
        max: int,
    ):
        self.name = name
        self.min = self._validate_single(min, context="min")
        self.max = self._validate_single(max, context="max")
        if isinstance(value, NoInitialValue):
            value = (self.min, self.max)
        self._value = self._validate(value)

    def _validate_single(self, new_value: Any, context: Optional[str] = None) -> int:
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
        except Exception:
            msg = f"Value {new_value} cannot be converted to int"
            if context:
                msg += f" for {context}"
            raise ValueError(msg)

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
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Low value {low} greater than high value {high}, swapping",
            )
            low, high = high, low

        if low < self.min:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Low value {low} below minimum {self.min}, clamping",
            )
            low = self.min
        if high > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"High value {high} above maximum {self.max}, clamping",
            )
            high = self.max

        return (low, high)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures min <= max, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        if self.min is None or self.max is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "IntegerRangeParameter must have both min and max bounds",
            )
        if self.min > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Min value greater than max value, swapping",
            )
            self.min, self.max = self.max, self.min
        self.value = self._validate(self.value)


@dataclass(init=False)
class FloatRangeParameter(Parameter[Tuple[float, float]]):
    """
    Parameter for a range of bounded decimal numbers.

    Creates a range slider in the GUI for selecting a range of numbers.
    See :meth:`~syd.viewer.Viewer.add_float_range` and
    :meth:`~syd.viewer.Viewer.update_float_range` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[Tuple[float, float], NoInitialValue]
        Initial (low, high) values
    min : float
        Minimum allowed value for both low and high
    max : float
        Maximum allowed value for both low and high
    step : float, optional
        Size of each increment (default is 0.001)

    Examples
    --------
    >>> temp_range = FloatRangeParameter("temperature_range",
    ...     value=(98.6, 100.4), min=95.0, max=105.0, step=0.1)
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

    min: float
    max: float
    step: float

    def __init__(
        self,
        name: str,
        value: Union[Tuple[float, float], NoInitialValue],
        min: float,
        max: float,
        step: float = 0.001,
    ):
        self.name = name
        self.step = step
        self.min = self._validate_single(min, context="min")
        self.max = self._validate_single(max, context="max")
        if isinstance(value, NoInitialValue):
            value = (self.min, self.max)
        self._value = self._validate(value)

    def _validate_single(self, new_value: Any, context: Optional[str] = None) -> float:
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
        except Exception:
            msg = f"Value {new_value} cannot be converted to float"
            if context:
                msg += f" for {context}"
            raise ValueError(msg)

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
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Low value {low} greater than high value {high}, swapping",
            )
            low, high = high, low

        if low < self.min:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Low value {low} below minimum {self.min}, clamping",
            )
            low = self.min
        if high > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"High value {high} above maximum {self.max}, clamping",
            )
            high = self.max

        return (low, high)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures min <= max, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        if self.min is None or self.max is None:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                "FloatRangeParameter must have both min and max bounds",
            )
        if self.min > self.max:
            warn_parameter_update(
                self.name,
                type(self).__name__,
                f"Min value greater than max value, swapping",
            )
            self.min, self.max = self.max, self.min
        self.value = self._validate(self.value)


@dataclass(init=False)
class UnboundedIntegerParameter(Parameter[int]):
    """
    Parameter for optionally bounded integer values.

    Creates a text input box in the GUI for entering whole numbers.
    See :meth:`~syd.viewer.Viewer.add_unbounded_integer` and
    :meth:`~syd.viewer.Viewer.update_unbounded_integer` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[int, NoInitialValue]
        Initial value

    Examples
    --------
    >>> count = UnboundedIntegerParameter("count", value=10)
    >>> count.value
    10
    >>> count.update({"value": 1000000})  # No maximum, so this is allowed
    >>> count.value
    1000000

    Notes
    -----
    Use this instead of IntegerParameter when you:
    - Don't have any reason to bound the value
    - Need to allow very large numbers that would be impractical with a slider
    """

    def __init__(
        self,
        name: str,
        value: Union[int, NoInitialValue],
    ):
        self.name = name
        if isinstance(value, NoInitialValue):
            value = 0
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> int:
        """
        Validate and convert value to integer.

        Args:
            new_value: Value to validate

        Returns:
            Validated integer value

        Raises:
            ValueError: If value cannot be converted to int
        """
        try:
            new_value = int(new_value)
        except ValueError:
            raise ValueError(f"Value {new_value} cannot be converted to int")

        return int(new_value)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        self.value = self._validate(self.value)


@dataclass(init=False)
class UnboundedFloatParameter(Parameter[float]):
    """
    Parameter for optionally bounded decimal numbers.

    Creates a text input box in the GUI for entering numbers.
    See :meth:`~syd.viewer.Viewer.add_unbounded_float` and
    :meth:`~syd.viewer.Viewer.update_unbounded_float` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    value : Union[float, NoInitialValue]
        Initial value
    step : float, optional
        Size of each increment (default is None, meaning no rounding)

    Examples
    --------
    >>> price = UnboundedFloatParameter("price", value=19.99)
    >>> price.value
    19.99
    >>> price.update({"value": 19.987})  # Will be rounded to step
    >>> price.value
    19.99

    Notes
    -----
    Use this instead of FloatParameter when you:
    - Don't know a reasonable maximum value
    - Need to allow very large or precise numbers that would be impractical with a slider

    If step is provided, values will be rounded:
    - step=0.1 rounds to 1.0, 1.1, 1.2, etc.
    - step=0.01 rounds to 1.00, 1.01, 1.02, etc.
    - step=5.0 rounds to 0.0, 5.0, 10.0, etc.
    """

    step: Optional[float]

    def __init__(
        self,
        name: str,
        value: Union[float, NoInitialValue],
        step: Optional[float] = None,
    ):
        self.name = name
        self.step = step
        if isinstance(value, NoInitialValue):
            value = 0
        self._value = self._validate(value)

    def _validate(self, new_value: Any) -> float:
        """
        Validate and convert value to float.
        Only rounds to step if step is not None.

        Args:
            new_value: Value to validate

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

        return float(new_value)

    def _validate_update(self) -> None:
        """
        Validate complete parameter state after updates.

        Ensures min <= max, swapping if needed.
        Re-validates current value against potentially updated bounds.

        Raises:
            ParameterUpdateError: If bounds are invalid (e.g. None when required)
        """
        self.value = self._validate(self.value)


@dataclass(init=False)
class ButtonAction(Parameter[None]):
    """
    Parameter for creating clickable buttons with callbacks.

    Creates a button in the GUI that executes a callback function when clicked.
    See :meth:`~syd.viewer.Viewer.add_button` and
    :meth:`~syd.viewer.Viewer.update_button` for usage.

    Parameters
    ----------
    name : str
        The name of the parameter
    label : Union[str, NoInitialValue]
        Text to display on the button (default is the button's name)
    callback : callable
        Function to execute when the button is clicked
    replot : bool, optional
        Whether to replot the figure after the callback is called.
        (default: True)

    Examples
    --------
    >>> def print_hello():
    ...     print("Hello!")
    >>> button = ButtonAction("greeting", label="Say Hello", callback=print_hello, replot=False)
    >>> button.callback()  # Simulates clicking the button
    Hello!
    >>> # Update the button's label and callback
    >>> def print_goodbye():
    ...     print("Goodbye!")
    >>> button.update({"label": "Say Goodbye", "callback": print_goodbye})
    >>> button.callback()
    Goodbye!

    Notes
    -----
    Unlike other Parameter types, ButtonAction:
    - Has no value (always None, therefore cannot be updated through the value property
    - Executes code directly rather than storing state
    - Has an option to turn off replotting after the callback is called for cases where you want to access the last figure only.
    """

    label: str
    callback: Callable
    replot: bool
    value: None = field(default=None, repr=False)
    _is_action: bool = field(default=True, repr=False)

    def __init__(
        self,
        name: str,
        label: Union[str, NoInitialValue],
        callback: Callable,
        replot: bool = True,
    ):
        """
        Initialize a button.

        Parameters
        ----------
        name : str
            The name of the parameter
        label : Union[str, NoInitialValue]
            Text to display on the button (default is the button's name)
        callback : callable
            Function to execute when the button is clicked
        replot : bool, optional
            Whether to replot the figure after the callback is called.
            (default: True)
        """
        self.name = name
        if isinstance(label, NoInitialValue):
            label = name
        self.label = label
        self.callback = callback
        self.replot = replot
        self._value = None

    def _validate(self, new_value: Any) -> None:
        """Validate the button's value."""
        return None

    def _validate_update(self) -> None:
        """Validate the button's value after updates."""
        if not callable(self.callback):
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                f"Callback {self.callback} is not callable",
            )
        if not isinstance(self.replot, bool):
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                f"Replet must be a boolean, got {type(self.replot)}",
            )
        try:
            str(self.label)
        except Exception:
            raise ParameterUpdateError(
                self.name,
                type(self).__name__,
                f"Label {self.label} doesn't have a string representation",
            )


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


class ActionType(Enum):
    button = ButtonAction
