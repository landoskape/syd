from typing import List, Any, Callable, Dict, Tuple, Union, Optional
from functools import wraps
from contextlib import contextmanager
from abc import ABC, abstractmethod
from matplotlib.figure import Figure

from .parameters import (
    ParameterType,
    Parameter,
    ParameterAddError,
    ParameterUpdateError,
)


class _NoUpdate:
    """Singleton class to represent a non-update in parameter operations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


# Create the singleton instance
_NO_UPDATE = _NoUpdate()


def validate_parameter_operation(
    operation: str, parameter_type: ParameterType
) -> Callable:
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
        if operation not in ["add", "update"]:
            raise ValueError(
                "Incorrect use of validate_parameter_operation decorator. Must be called with 'add' or 'update' as the first argument."
            )

        @wraps(func)
        def wrapper(self: "InteractiveViewer", name: Any, *args, **kwargs):
            # Validate operation matches method name (add/update)
            if not func.__name__.startswith(operation):
                raise ValueError(
                    f"Invalid operation type specified ({operation}) for method {func.__name__}"
                )

            # Validate parameter name is a string
            if not isinstance(name, str):
                if operation == "add":
                    raise ParameterAddError(
                        name, parameter_type.name, "Parameter name must be a string"
                    )
                elif operation == "update":
                    raise ParameterUpdateError(
                        name, parameter_type.name, "Parameter name must be a string"
                    )

            # Validate deployment state
            if operation == "add" and self._app_deployed:
                raise RuntimeError(
                    "The app is currently deployed, cannot add a new parameter right now."
                )

            if operation == "add":
                if name in self.parameters:
                    raise ParameterAddError(
                        name, parameter_type.name, "Parameter already exists!"
                    )

            # For updates, validate parameter existence and type
            if operation == "update":
                if name not in self.parameters:
                    raise ParameterUpdateError(
                        name,
                        parameter_type.name,
                        "Parameter not found - you can only update registered parameters!",
                    )
                if type(self.parameters[name]) != parameter_type.value:
                    msg = f"Parameter called {name} was found but is registered as a different parameter type ({type(self.parameters[name])})"
                    raise ParameterUpdateError(name, parameter_type.name, msg)

            try:
                return func(self, name, *args, **kwargs)
            except Exception as e:
                if operation == "add":
                    raise ParameterAddError(name, parameter_type.name, str(e)) from e
                elif operation == "update":
                    raise ParameterUpdateError(name, parameter_type.name, str(e)) from e
                else:
                    raise e

        return wrapper

    return decorator


class InteractiveViewer(ABC):
    """
    Base class for creating interactive matplotlib figures with GUI controls.

    This class helps you create interactive visualizations by adding GUI elements
    (like sliders, dropdowns, etc.) that update your plot in real-time. To use it:

    1. Create a subclass and implement the plot() method
    2. Add parameters using add_* methods before deploying
    3. Use on_change() to make parameters update the plot
    4. Use update_* methods to update parameter values and properties
    5. Deploy the app to show the interactive figure

    Examples
    --------
    >>> class MyViewer(InteractiveViewer):
    ...     def plot(self, state: Dict[str, Any]):
    ...         fig = plt.figure()
    ...         plt.plot([0, state['x']])
    ...         return fig
    ...
    ...     def update_based_on_x(self, state: Dict[str, Any]):
    ...         self.update_float('x', value=state['x'])
    ...
    >>> viewer = MyViewer()
    >>> viewer.add_float('x', value=1.0, min_value=0, max_value=10)
    >>> viewer.on_change('x', viewer.update_based_on_x)
    """

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
        """
        Get the current values of all parameters.

        Returns
        -------
        dict
            Dictionary mapping parameter names to their current values

        Examples
        --------
        >>> viewer.add_float('x', value=1.0, min_value=0, max_value=10)
        >>> viewer.add_text('label', value='data')
        >>> viewer.get_state()
        {'x': 1.0, 'label': 'data'}
        """
        return {name: param.value for name, param in self.parameters.items()}

    @abstractmethod
    def plot(self, **kwargs) -> Figure:
        """
        Create and return a matplotlib figure.

        This method must be implemented in your subclass. It should create a new
        figure using the current parameter values from self.parameters.

        Returns
        -------
        matplotlib.figure.Figure
            The figure to display

        Notes
        -----
        - Create a new figure each time, don't reuse old ones
        - Access parameter values using self.parameters['name'].value
        - Return the figure object, don't call plt.show()
        """
        raise NotImplementedError("Subclasses must implement the plot method")

    def deploy(self, env: str = "notebook", **kwargs):
        """Deploy the app in a notebook or standalone environment"""
        if env == "notebook":
            from .notebook_deploy import NotebookDeployment

            deployer = NotebookDeployment(self, **kwargs)
            deployer.deploy()

            return deployer
        else:
            raise ValueError(
                f"Unsupported environment: {env}, only 'notebook' is supported right now."
            )

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
        """
        Register a function to run when parameters change.

        The callback function will receive a dictionary of all current parameter
        values whenever any of the specified parameters change.

        Parameters
        ----------
        parameter_name : str or list of str
            Name(s) of parameters to watch for changes
        callback : callable
            Function to call when changes occur. Should accept a single dict argument
            containing the current state.

        Examples
        --------
        >>> def update_plot(state):
        ...     print(f"x changed to {state['x']}")
        >>> viewer.on_change('x', update_plot)
        >>> viewer.on_change(['x', 'y'], lambda s: viewer.plot())  # Update on either change
        """
        if isinstance(parameter_name, str):
            parameter_name = [parameter_name]

        for param_name in parameter_name:
            if param_name not in self.parameters:
                raise ValueError(f"Parameter '{param_name}' is not registered!")
            if param_name not in self.callbacks:
                self.callbacks[param_name] = []
            self.callbacks[param_name].append(callback)

    def set_parameter_value(self, name: str, value: Any) -> None:
        """
        Update a parameter's value and trigger any callbacks.

        This is a lower-level method - usually you'll want to use the update_*
        methods instead (e.g., update_float, update_text, etc.).

        Parameters
        ----------
        name : str
            Name of the parameter to update
        value : Any
            New value for the parameter

        Raises
        ------
        ValueError
            If the parameter doesn't exist or the value is invalid
        """
        if name not in self.parameters:
            raise ValueError(f"Parameter {name} not found")

        # Update the parameter value
        self.parameters[name].value = value

        # Perform callbacks
        self.perform_callbacks(name)

    # -------------------- parameter registration methods --------------------
    @validate_parameter_operation("add", ParameterType.text)
    def add_text(self, name: str, *, value: str) -> None:
        """
        Add a text input parameter to the viewer.

        Creates a text box in the GUI that accepts any string input.
        See :class:`~syd.parameters.TextParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : str
            Initial text value

        Examples
        --------
        >>> viewer.add_text('title', value='My Plot')
        >>> viewer.get_state()['title']
        'My Plot'
        """
        try:
            new_param = ParameterType.text.value(name, value)
        except Exception as e:
            raise ParameterAddError(name, "text", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.boolean)
    def add_boolean(self, name: str, *, value: bool) -> None:
        """
        Add a boolean parameter to the viewer.

        Creates a checkbox in the GUI that can be toggled on/off.
        See :class:`~syd.parameters.BooleanParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : bool
            Initial state (True=checked, False=unchecked)

        Examples
        --------
        >>> viewer.add_boolean('show_grid', value=True)
        >>> viewer.get_state()['show_grid']
        True
        """
        try:
            new_param = ParameterType.boolean.value(name, value)
        except Exception as e:
            raise ParameterAddError(name, "boolean", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.selection)
    def add_selection(self, name: str, *, value: Any, options: List[Any]) -> None:
        """
        Add a single-selection parameter to the viewer.

        Creates a dropdown menu in the GUI where users can select one option.
        See :class:`~syd.parameters.SelectionParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : Any
            Initially selected value (must be one of the options)
        options : list
            List of values that can be selected

        Examples
        --------
        >>> viewer.add_selection('color', value='red',
        ...                     options=['red', 'green', 'blue'])
        >>> viewer.get_state()['color']
        'red'
        """
        try:
            new_param = ParameterType.selection.value(name, value, options)
        except Exception as e:
            raise ParameterAddError(name, "selection", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.multiple_selection)
    def add_multiple_selection(
        self, name: str, *, value: List[Any], options: List[Any]
    ) -> None:
        """
        Add a multiple-selection parameter to the viewer.

        Creates a set of checkboxes or a multi-select dropdown in the GUI where
        users can select any number of options.
        See :class:`~syd.parameters.MultipleSelectionParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : list
            Initially selected values (must all be in options)
        options : list
            List of values that can be selected

        Examples
        --------
        >>> viewer.add_multiple_selection('toppings',
        ...     value=['cheese'],
        ...     options=['cheese', 'pepperoni', 'mushrooms'])
        >>> viewer.get_state()['toppings']
        ['cheese']
        """
        try:
            new_param = ParameterType.multiple_selection.value(name, value, options)
        except Exception as e:
            raise ParameterAddError(name, "multiple_selection", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.integer)
    def add_integer(
        self,
        name: str,
        *,
        value: Union[float, int],
        min_value: Union[float, int],
        max_value: Union[float, int],
    ) -> None:
        """
        Add an integer parameter to the viewer.

        Creates a slider in the GUI that lets users select whole numbers between
        min_value and max_value. Values will be clamped to stay within bounds.
        See :class:`~syd.parameters.IntegerParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : int
            Initial value (will be clamped between min_value and max_value)
        min_value : int
            Minimum allowed value
        max_value : int
            Maximum allowed value

        Examples
        --------
        >>> viewer.add_integer('count', value=5, min_value=0, max_value=10)
        >>> viewer.get_state()['count']
        5
        >>> viewer.update_integer('count', value=15)  # Will be clamped to 10
        >>> viewer.get_state()['count']
        10
        """
        try:
            new_param = ParameterType.integer.value(
                name,
                value,
                min_value,
                max_value,
            )
        except Exception as e:
            raise ParameterAddError(name, "number", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.float)
    def add_float(
        self,
        name: str,
        *,
        value: Union[float, int],
        min_value: Union[float, int],
        max_value: Union[float, int],
        step: float = 0.1,
    ) -> None:
        """
        Add a decimal number parameter to the viewer.

        Creates a slider in the GUI that lets users select numbers between
        min_value and max_value. Values will be rounded to the nearest step
        and clamped to stay within bounds.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : float
            Initial value (will be clamped between min_value and max_value)
        min_value : float
            Minimum allowed value
        max_value : float
            Maximum allowed value
        step : float, optional
            Size of each increment (default: 0.1)

        Examples
        --------
        >>> viewer.add_float('temperature', value=20.0,
        ...                  min_value=0.0, max_value=100.0, step=0.5)
        >>> viewer.get_state()['temperature']
        20.0
        >>> viewer.update_float('temperature', value=20.7)  # Will round to 20.5
        >>> viewer.get_state()['temperature']
        20.5
        """
        try:
            new_param = ParameterType.float.value(
                name,
                value,
                min_value,
                max_value,
                step,
            )
        except Exception as e:
            raise ParameterAddError(name, "number", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.integer_range)
    def add_integer_range(
        self,
        name: str,
        *,
        value: Tuple[Union[float, int], Union[float, int]],
        min_value: Union[float, int],
        max_value: Union[float, int],
    ) -> None:
        """
        Add a range parameter for whole numbers to the viewer.

        Creates a range slider in the GUI that lets users select a range of integers
        between min_value and max_value. The range is specified as (low, high) and
        both values will be clamped to stay within bounds.
        See :class:`~syd.parameters.IntegerRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : tuple[int, int]
            Initial (low, high) values
        min_value : int
            Minimum allowed value for both low and high
        max_value : int
            Maximum allowed value for both low and high

        Examples
        --------
        >>> viewer.add_integer_range('age_range',
        ...                         value=(25, 35),
        ...                         min_value=18, max_value=100)
        >>> viewer.get_state()['age_range']
        (25, 35)
        >>> # Values will be swapped if low > high
        >>> viewer.update_integer_range('age_range', value=(40, 30))
        >>> viewer.get_state()['age_range']
        (30, 40)
        """
        try:
            new_param = ParameterType.integer_range.value(
                name,
                value,
                min_value,
                max_value,
            )
        except Exception as e:
            raise ParameterAddError(name, "integer_range", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.float_range)
    def add_float_range(
        self,
        name: str,
        *,
        value: Tuple[Union[float, int], Union[float, int]],
        min_value: Union[float, int],
        max_value: Union[float, int],
        step: float = 0.1,
    ) -> None:
        """
        Add a range parameter for decimal numbers to the viewer.

        Creates a range slider in the GUI that lets users select a range of numbers
        between min_value and max_value. The range is specified as (low, high) and
        both values will be rounded to the nearest step and clamped to stay within bounds.
        See :class:`~syd.parameters.FloatRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : tuple[float, float]
            Initial (low, high) values
        min_value : float
            Minimum allowed value for both low and high
        max_value : float
            Maximum allowed value for both low and high
        step : float, optional
            Size of each increment (default: 0.1)

        Examples
        --------
        >>> viewer.add_float_range('price_range',
        ...                       value=(10.0, 20.0),
        ...                       min_value=0.0, max_value=100.0, step=0.5)
        >>> viewer.get_state()['price_range']
        (10.0, 20.0)
        >>> # Values will be rounded to nearest step
        >>> viewer.update_float_range('price_range', value=(10.7, 19.2))
        >>> viewer.get_state()['price_range']
        (10.5, 19.0)
        """
        try:
            new_param = ParameterType.float_range.value(
                name,
                value,
                min_value,
                max_value,
                step,
            )
        except Exception as e:
            raise ParameterAddError(name, "float_range", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.unbounded_integer)
    def add_unbounded_integer(
        self,
        name: str,
        *,
        value: Union[float, int],
        min_value: Optional[Union[float, int]] = None,
        max_value: Optional[Union[float, int]] = None,
    ) -> None:
        """
        Add an unbounded integer parameter to the viewer.

        Creates a text input box in the GUI for entering whole numbers. Unlike
        add_integer(), this allows very large numbers and optionally no minimum
        or maximum bounds.
        See :class:`~syd.parameters.UnboundedIntegerParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : int
            Initial value
        min_value : int, optional
            Minimum allowed value (or None for no minimum)
        max_value : int, optional
            Maximum allowed value (or None for no maximum)

        Examples
        --------
        >>> viewer.add_unbounded_integer('population',
        ...                             value=1000000,
        ...                             min_value=0)  # No maximum
        >>> viewer.get_state()['population']
        1000000
        >>> # Values below minimum will be clamped
        >>> viewer.update_unbounded_integer('population', value=-5)
        >>> viewer.get_state()['population']
        0
        """
        try:
            new_param = ParameterType.unbounded_integer.value(
                name,
                value,
                min_value,
                max_value,
            )
        except Exception as e:
            raise ParameterAddError(name, "unbounded_integer", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.unbounded_float)
    def add_unbounded_float(
        self,
        name: str,
        *,
        value: Union[float, int],
        min_value: Optional[Union[float, int]] = None,
        max_value: Optional[Union[float, int]] = None,
        step: Optional[float] = None,
    ) -> None:
        """
        Add an unbounded decimal number parameter to the viewer.

        Creates a text input box in the GUI for entering numbers. Unlike add_float(),
        this allows very large or precise numbers and optionally no minimum or
        maximum bounds. Values can optionally be rounded to a step size.
        See :class:`~syd.parameters.UnboundedFloatParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : float
            Initial value
        min_value : float, optional
            Minimum allowed value (or None for no minimum)
        max_value : float, optional
            Maximum allowed value (or None for no maximum)
        step : float, optional
            Size of each increment (or None for no rounding)

        Examples
        --------
        >>> viewer.add_unbounded_float('wavelength',
        ...                           value=550e-9,  # Nanometers
        ...                           min_value=0.0,
        ...                           step=1e-9)  # Round to nearest nanometer
        >>> viewer.get_state()['wavelength']
        5.5e-07
        >>> # Values will be rounded if step is provided
        >>> viewer.update_unbounded_float('wavelength', value=550.7e-9)
        >>> viewer.get_state()['wavelength']
        5.51e-07
        """
        try:
            new_param = ParameterType.unbounded_float.value(
                name,
                value,
                min_value,
                max_value,
                step,
            )
        except Exception as e:
            raise ParameterAddError(name, "unbounded_float", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.button)
    def add_button(
        self,
        name: str,
        *,
        label: str,
        callback: Callable[[], None],
    ) -> None:
        """
        Add a button parameter to the viewer.

        Creates a clickable button in the GUI that triggers the provided callback function
        when clicked. The button's display text can be different from its parameter name.
        See :class:`~syd.parameters.ButtonParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (internal identifier)
        label : str
            Text to display on the button
        callback : callable
            Function to call when the button is clicked (takes no arguments)

        Examples
        --------
        >>> def reset_plot():
        ...     print("Resetting plot...")
        >>> viewer.add_button('reset', label='Reset Plot', callback=reset_plot)
        """
        try:

            # Wrap the callback to include state as an input argument
            def wrapped_callback(button):
                callback(self.get_state())

            new_param = ParameterType.button.value(name, label, wrapped_callback)
        except Exception as e:
            raise ParameterAddError(name, "button", str(e)) from e
        else:
            self.parameters[name] = new_param

    # -------------------- parameter update methods --------------------
    @validate_parameter_operation("update", ParameterType.text)
    def update_text(
        self, name: str, *, value: Union[str, _NoUpdate] = _NO_UPDATE
    ) -> None:
        """
        Update a text parameter's value.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_text`.
        See :class:`~syd.parameters.TextParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the text parameter to update
        value : str, optional
            New text value (if not provided, no change)

        Examples
        --------
        >>> viewer.add_text('title', value='Original Title')
        >>> viewer.update_text('title', value='New Title')
        >>> viewer.get_state()['title']
        'New Title'
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.boolean)
    def update_boolean(
        self, name: str, *, value: Union[bool, _NoUpdate] = _NO_UPDATE
    ) -> None:
        """
        Update a boolean parameter's value.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_boolean`.
        See :class:`~syd.parameters.BooleanParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the boolean parameter to update
        value : bool, optional
            New state (True/False) (if not provided, no change)

        Examples
        --------
        >>> viewer.add_boolean('show_grid', value=True)
        >>> viewer.update_boolean('show_grid', value=False)
        >>> viewer.get_state()['show_grid']
        False
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.selection)
    def update_selection(
        self,
        name: str,
        *,
        value: Union[Any, _NoUpdate] = _NO_UPDATE,
        options: Union[List[Any], _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update a selection parameter's value and/or options.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_selection`.
        See :class:`~syd.parameters.SelectionParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the selection parameter to update
        value : Any, optional
            New selected value (must be in options) (if not provided, no change)
        options : list, optional
            New list of selectable options (if not provided, no change)

        Examples
        --------
        >>> viewer.add_selection('color', value='red',
        ...                     options=['red', 'green', 'blue'])
        >>> # Update just the value
        >>> viewer.update_selection('color', value='blue')
        >>> # Update options and value together
        >>> viewer.update_selection('color',
        ...                        options=['purple', 'orange'],
        ...                        value='purple')
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if options is not _NO_UPDATE:
            updates["options"] = options
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.multiple_selection)
    def update_multiple_selection(
        self,
        name: str,
        *,
        value: Union[List[Any], _NoUpdate] = _NO_UPDATE,
        options: Union[List[Any], _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update a multiple selection parameter's values and/or options.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_multiple_selection`.
        See :class:`~syd.parameters.MultipleSelectionParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the multiple selection parameter to update
        value : list, optional
            New list of selected values (all must be in options) (if not provided, no change)
        options : list, optional
            New list of selectable options (if not provided, no change)

        Examples
        --------
        >>> viewer.add_multiple_selection('toppings',
        ...     value=['cheese'],
        ...     options=['cheese', 'pepperoni', 'mushrooms'])
        >>> # Update selected values
        >>> viewer.update_multiple_selection('toppings',
        ...                                 value=['cheese', 'mushrooms'])
        >>> # Update options (will reset value if current selections not in new options)
        >>> viewer.update_multiple_selection('toppings',
        ...     options=['cheese', 'bacon', 'olives'],
        ...     value=['cheese', 'bacon'])
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if options is not _NO_UPDATE:
            updates["options"] = options
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.integer)
    def update_integer(
        self,
        name: str,
        *,
        value: Union[int, _NoUpdate] = _NO_UPDATE,
        min_value: Union[int, _NoUpdate] = _NO_UPDATE,
        max_value: Union[int, _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update an integer parameter's value and/or bounds.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer`.
        See :class:`~syd.parameters.IntegerParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the integer parameter to update
        value : int, optional
            New value (will be clamped to bounds) (if not provided, no change)
        min_value : int, optional
            New minimum value (if not provided, no change)
        max_value : int, optional
            New maximum value (if not provided, no change)

        Examples
        --------
        >>> viewer.add_integer('count', value=5, min_value=0, max_value=10)
        >>> # Update just the value
        >>> viewer.update_integer('count', value=8)
        >>> # Update bounds (current value will be clamped if needed)
        >>> viewer.update_integer('count', min_value=7, max_value=15)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.float)
    def update_float(
        self,
        name: str,
        *,
        value: Union[float, _NoUpdate] = _NO_UPDATE,
        min_value: Union[float, _NoUpdate] = _NO_UPDATE,
        max_value: Union[float, _NoUpdate] = _NO_UPDATE,
        step: Union[float, _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update a float parameter's value, bounds, and/or step size.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_float`.
        See :class:`~syd.parameters.FloatParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the float parameter to update
        value : float, optional
            New value (will be rounded and clamped) (if not provided, no change)
        min_value : float, optional
            New minimum value (if not provided, no change)
        max_value : float, optional
            New maximum value (if not provided, no change)
        step : float, optional
            New step size (if not provided, no change)

        Examples
        --------
        >>> viewer.add_float('temperature', value=20.0,
        ...                  min_value=0.0, max_value=100.0, step=0.5)
        >>> # Update just the value (will round to step)
        >>> viewer.update_float('temperature', value=20.7)  # Becomes 20.5
        >>> # Update bounds and step size
        >>> viewer.update_float('temperature',
        ...                    min_value=15.0, max_value=30.0, step=0.1)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if step is not _NO_UPDATE:
            updates["step"] = step
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.integer_range)
    def update_integer_range(
        self,
        name: str,
        *,
        value: Union[Tuple[int, int], _NoUpdate] = _NO_UPDATE,
        min_value: Union[int, _NoUpdate] = _NO_UPDATE,
        max_value: Union[int, _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update an integer range parameter's values and/or bounds.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer_range`.
        See :class:`~syd.parameters.IntegerRangeParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the integer range parameter to update
        value : tuple[int, int], optional
            New (low, high) values (will be clamped) (if not provided, no change)
        min_value : int, optional
            New minimum value for both low and high (if not provided, no change)
        max_value : int, optional
            New maximum value for both low and high (if not provided, no change)

        Examples
        --------
        >>> viewer.add_integer_range('age_range',
        ...                         value=(25, 35),
        ...                         min_value=18, max_value=100)
        >>> # Update just the range (values will be swapped if needed)
        >>> viewer.update_integer_range('age_range', value=(40, 30))  # Becomes (30, 40)
        >>> # Update bounds (current values will be clamped if needed)
        >>> viewer.update_integer_range('age_range', min_value=20, max_value=80)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.float_range)
    def update_float_range(
        self,
        name: str,
        *,
        value: Union[Tuple[float, float], _NoUpdate] = _NO_UPDATE,
        min_value: Union[float, _NoUpdate] = _NO_UPDATE,
        max_value: Union[float, _NoUpdate] = _NO_UPDATE,
        step: Union[float, _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update a float range parameter's values, bounds, and/or step size.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_float_range`.
        See :class:`~syd.parameters.FloatRangeParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the float range parameter to update
        value : tuple[float, float], optional
            New (low, high) values (will be rounded and clamped) (if not provided, no change)
        min_value : float, optional
            New minimum value for both low and high (if not provided, no change)
        max_value : float, optional
            New maximum value for both low and high (if not provided, no change)
        step : float, optional
            New step size for rounding values (if not provided, no change)

        Examples
        --------
        >>> viewer.add_float_range('price_range',
        ...                       value=(10.0, 20.0),
        ...                       min_value=0.0, max_value=100.0, step=0.5)
        >>> # Update just the range (values will be rounded and swapped if needed)
        >>> viewer.update_float_range('price_range', value=(15.7, 14.2))  # Becomes (14.0, 15.5)
        >>> # Update bounds and step size
        >>> viewer.update_float_range('price_range',
        ...                          min_value=5.0, max_value=50.0, step=0.1)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if step is not _NO_UPDATE:
            updates["step"] = step
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.unbounded_integer)
    def update_unbounded_integer(
        self,
        name: str,
        *,
        value: Union[int, _NoUpdate] = _NO_UPDATE,
        min_value: Union[Optional[int], _NoUpdate] = _NO_UPDATE,
        max_value: Union[Optional[int], _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update an unbounded integer parameter's value and/or bounds.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_integer`.
        See :class:`~syd.parameters.UnboundedIntegerParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the unbounded integer parameter to update
        value : int, optional
            New value (will be clamped to any bounds) (if not provided, no change)
        min_value : int or None, optional
            New minimum value, or None for no minimum (if not provided, no change)
        max_value : int or None, optional
            New maximum value, or None for no maximum (if not provided, no change)

        Examples
        --------
        >>> viewer.add_unbounded_integer('population',
        ...                             value=1000000,
        ...                             min_value=0)  # No maximum
        >>> # Update just the value
        >>> viewer.update_unbounded_integer('population', value=2000000)
        >>> # Add a maximum bound (current value will be clamped if needed)
        >>> viewer.update_unbounded_integer('population', max_value=1500000)
        >>> # Remove the minimum bound
        >>> viewer.update_unbounded_integer('population', min_value=None)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.unbounded_float)
    def update_unbounded_float(
        self,
        name: str,
        *,
        value: Union[float, _NoUpdate] = _NO_UPDATE,
        min_value: Union[Optional[float], _NoUpdate] = _NO_UPDATE,
        max_value: Union[Optional[float], _NoUpdate] = _NO_UPDATE,
        step: Union[Optional[float], _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update an unbounded float parameter's value, bounds, and/or step size.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_float`.
        See :class:`~syd.parameters.UnboundedFloatParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the unbounded float parameter to update
        value : float, optional
            New value (will be rounded if step is set) (if not provided, no change)
        min_value : float or None, optional
            New minimum value, or None for no minimum (if not provided, no change)
        max_value : float or None, optional
            New maximum value, or None for no maximum (if not provided, no change)
        step : float or None, optional
            New step size for rounding, or None for no rounding (if not provided, no change)

        Examples
        --------
        >>> viewer.add_unbounded_float('wavelength',
        ...                           value=550e-9,  # Nanometers
        ...                           min_value=0.0,
        ...                           step=1e-9)
        >>> # Update value (will be rounded if step is set)
        >>> viewer.update_unbounded_float('wavelength', value=632.8e-9)  # HeNe laser
        >>> # Change step size and add maximum
        >>> viewer.update_unbounded_float('wavelength',
        ...                              step=0.1e-9,  # Finer control
        ...                              max_value=1000e-9)  # Infrared limit
        >>> # Remove step size (allow any precision)
        >>> viewer.update_unbounded_float('wavelength', step=None)
        """
        updates = {}
        if value is not _NO_UPDATE:
            updates["value"] = value
        if min_value is not _NO_UPDATE:
            updates["min_value"] = min_value
        if max_value is not _NO_UPDATE:
            updates["max_value"] = max_value
        if step is not _NO_UPDATE:
            updates["step"] = step
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.button)
    def update_button(
        self,
        name: str,
        *,
        label: Union[str, _NoUpdate] = _NO_UPDATE,
        callback: Union[Callable[[], None], _NoUpdate] = _NO_UPDATE,
    ) -> None:
        """
        Update a button parameter's label and/or callback function.

        Updates a parameter created by :meth:`~syd.interactive_viewer.InteractiveViewer.add_button`.
        See :class:`~syd.parameters.ButtonParameter` for details.

        Parameters
        ----------
        name : str
            Name of the button parameter to update
        label : str, optional
            New text to display on the button (if not provided, no change)
        callback : callable, optional
            New function to call when clicked (if not provided, no change)

        Examples
        --------
        >>> def new_callback():
        ...     print("New action...")
        >>> viewer.update_button('reset',
        ...                     label='Clear Plot',
        ...                     callback=new_callback)
        """
        updates = {}
        if label is not _NO_UPDATE:
            updates["label"] = label
        if callback is not _NO_UPDATE:
            updates["callback"] = callback
        if updates:
            self.parameters[name].update(updates)
