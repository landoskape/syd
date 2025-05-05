from typing import List, Any, Callable, Dict, Tuple, Union, Optional, Literal
from functools import wraps, partial
import inspect
from contextlib import contextmanager
from matplotlib.figure import Figure

from .parameters import ParameterType, ActionType, Parameter
from .support import NoUpdate, NoInitialValue, ParameterAddError, ParameterUpdateError

# Create the singleton instances
NO_UPDATE = NoUpdate()
NO_INITIAL_VALUE = NoInitialValue()


def make_viewer(plot_func: Optional[Callable] = None) -> "Viewer":
    """Create an empty viewer object.

    Parameters
    ----------
    plot_func : Callable, optional
        A function that takes a state dictionary and returns a matplotlib figure.

    Returns
    -------
    viewer : Viewer
        A new viewer object

    Examples
    --------
    >>> from syd import make_viewer
    >>> def plot(state):
    >>>     ... generate figure, plot stuff ...
    >>>     return fig
    >>> viewer = make_viewer(plot)
    >>> viewer.add_float('x', value=1.0, min=0, max=10)
    >>> viewer.on_change('x', viewer.update_based_on_x)
    >>> viewer.show()
    """
    viewer = Viewer()
    if plot_func is not None:
        viewer.set_plot(plot_func)
    return viewer


def validate_parameter_operation(
    operation: str,
    parameter_type: Union[ParameterType, ActionType],
) -> Callable:
    """
    Decorator that validates parameter operations for the viewer class.

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

        # Validate operation matches method name (add/update)
        if not func.__name__.startswith(operation):
            raise ValueError(
                f"Invalid operation type specified ({operation}) for method {func.__name__}"
            )

        @wraps(func)
        def wrapper(self: "Viewer", name: Any, *args, **kwargs):
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
                if not isinstance(self.parameters[name], parameter_type.value):
                    msg = f"Parameter called {name} was found but is registered as a different parameter type ({type(self.parameters[name])}). Expecting {parameter_type.value}."
                    raise ParameterUpdateError(name, parameter_type.name, msg)

            return func(self, name, *args, **kwargs)

        return wrapper

    return decorator


class Viewer:
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
    >>> class MyViewer(Viewer):
    ...     def plot(self, state: Dict[str, Any]):
    ...         fig = plt.figure()
    ...         plt.plot([0, state['x']])
    ...         return fig
    ...
    ...     def update_based_on_x(self, state: Dict[str, Any]):
    ...         self.update_float('x', value=state['x'])
    ...
    >>> viewer = MyViewer()
    >>> viewer.add_float('x', value=1.0, min=0, max=10)
    >>> viewer.on_change('x', viewer.update_based_on_x)
    >>> viewer.show()
    """

    parameters: Dict[str, Parameter]
    callbacks: Dict[str, List[Callable]]
    _app_deployed: bool
    _in_callbacks: bool
    _figure: Figure

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.parameters = {}
        instance.callbacks = {}
        instance._app_deployed = False
        instance._in_callbacks = False
        instance._figure = None
        return instance

    @property
    def state(self) -> Dict[str, Any]:
        """
        Get the current values of all parameters.


        Returns
        -------
        dict
            Dictionary mapping parameter names to their current values

        Examples
        --------
        >>> viewer.add_float('x', value=1.0, min=0, max=10)
        >>> viewer.add_text('label', value='data')
        >>> viewer.state
        {'x': 1.0, 'label': 'data'}
        """
        return {
            name: param.value
            for name, param in self.parameters.items()
            if not param._is_action
        }

    @property
    def figure(self) -> Figure:
        """
        Get the last opened figure. Returns None if no figure has been opened yet.
        """
        return self._figure

    def plot(self, state: Dict[str, Any]) -> Figure:
        """Create and return a matplotlib figure.

        This is a placeholder. You must either:

        1. Call set_plot() with your plotting function
        This will look like this:
        >>> def plot(state):
        >>>     ... generate figure, plot stuff ...
        >>>     return fig
        >>> viewer.set_plot(plot))

        2. Subclass Viewer and override this method
        This will look like this:
        >>> class YourViewer(Viewer):
        >>>     def plot(self, state):
        >>>         ... generate figure, plot stuff ...
        >>>         return fig

        Parameters
        ----------
        state : dict
            Current parameter values

        Returns
        -------
        matplotlib.figure.Figure
            The figure to display

        Notes
        -----
        - Create a new figure each time, don't reuse old ones
        - Access parameter values using state['param_name']
        - Access your viewer class using self (or viewer for the set_plot() method)
        - Return the figure object, don't call plt.show()!
        """
        raise NotImplementedError(
            "Plot method not implemented. Either subclass "
            "Viewer and override plot(), or use "
            "set_plot() to provide a plotting function."
        )

    def set_plot(self, func: Callable) -> None:
        """Set the plot method for the viewer"""
        self.plot = self._prepare_function(func, context="Setting plot:")

    def show(
        self,
        controls_position: Literal["left", "top", "right", "bottom"] = "left",
        controls_width_percent: int = 20,
        suppress_warnings: bool = True,
        update_threshold: float = 1.0,
    ):
        """Show the viewer in a notebook

        Same as deploy(env="notebook") except it doesn't return the viewer object.
        """
        _ = self.deploy(
            env="notebook",
            controls_position=controls_position,
            controls_width_percent=controls_width_percent,
            suppress_warnings=suppress_warnings,
            update_threshold=update_threshold,
        )

    def share(
        self,
        controls_position: str = "left",
        fig_dpi: int = 300,
        controls_width_percent: int = 20,
        plot_margin_percent: float = 2.5,
        suppress_warnings: bool = True,
        debug: bool = False,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        open_browser: bool = True,
        update_threshold: float = 1.0,
        timeout_threshold: float = 10.0,
    ):
        """Share the viewer on a web browser using Flask

        Same as deploy(env="browser") except it doesn't return the viewer object.
        """
        _ = self.deploy(
            env="browser",
            controls_position=controls_position,
            fig_dpi=fig_dpi,
            controls_width_percent=controls_width_percent,
            plot_margin_percent=plot_margin_percent,
            suppress_warnings=suppress_warnings,
            debug=debug,
            host=host,
            port=port,
            open_browser=open_browser,
            update_threshold=update_threshold,
            timeout_threshold=timeout_threshold,
        )

    def deploy(self, env: str = "notebook", **kwargs):
        """Deploy the app in a notebook or standalone environment"""
        env = env.lower()
        if env == "notebook":
            # On demand import because the deployers need to import the viewer
            from .notebook_deployment.deployer import NotebookDeployer

            deployer = NotebookDeployer(self, **kwargs)
            deployer.deploy()
            return self

        elif env == "browser":
            # On demand import because the deployers need to import the viewer
            from .flask_deployment.deployer import FlaskDeployer

            if "port" not in kwargs:
                kwargs["port"] = None

            deployer = FlaskDeployer(self, **kwargs)
            deployer.deploy()
            return self

        else:
            raise ValueError(
                f"Unsupported environment: {env}, only 'notebook', 'browser' are supported right now."
            )

    @contextmanager
    def _deploy_app(self):
        """Internal context manager to control app deployment state"""
        self._app_deployed = True
        try:
            yield
        finally:
            self._app_deployed = False

    def _prepare_function(
        self,
        func: Callable,
        context: Optional[str] = "",
    ) -> Callable:
        # Check if func is Callable
        if not callable(func):
            raise ValueError(f"Function {func} is not callable")

        # Handle partial functions
        if isinstance(func, partial):
            get_self = (
                lambda func: hasattr(func.func, "__self__") and func.func.__self__
            )
            get_name = lambda func: func.func.__name__
        else:
            get_self = lambda func: hasattr(func, "__self__") and func.__self__
            get_name = lambda func: func.__name__

        # Get function signature
        try:
            params = list(inspect.signature(func).parameters.values())
        except ValueError:
            # Handle built-ins or other objects without signatures
            raise ValueError(context + f"Cannot inspect function signature for {func}")

        # Look through params and check if there are two positional parameters (including self for bound methods)
        bound_method = get_self(func) is self
        positional_params = 0
        required_kwargs = 0
        optional_part = ""
        for param in params:
            # Check if it's a positional parameter. If it is, count it.
            # We need at least 1 positional parameter. When we already have 1,
            # we need to make sure any other positional parameters have defaults.
            if param.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY,
            ):
                if positional_params < 1:
                    positional_params += 1
                else:
                    if param.default == inspect.Parameter.empty:
                        positional_params += 1
                    else:
                        optional_part += f", {param.name}={param.default!r}"
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                optional_part += f", **{param.name}"
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                optional_part += (
                    f", {param.name}={param.default!r}"
                    if param.default != inspect.Parameter.empty
                    else f""
                )
                if param.default == inspect.Parameter.empty:
                    required_kwargs += 1

        if positional_params != 1 or required_kwargs != 0:
            func_name = get_name(func)
            if isinstance(func, partial):
                func_sig = str(inspect.signature(func))
                if bound_method:
                    func_sig = "(" + "self, " + func_sig[1:]
                msg = (
                    context
                    + "\n"
                    + f"Your partial function '{func_name}' has an incorrect signature.\n"
                    "Partial functions must have exactly one positional parameter\n"
                    "which corresponds to a dictionary of the current state of the viewer.\n"
                    "\nYour partial function effectivelylooks like this:\n"
                    f"def {func_name}{func_sig}:\n"
                    "    ... your function code ..."
                )
                raise ValueError(msg)

            if bound_method:
                original_method = getattr(get_self(func).__class__, get_name(func))
                func_sig = str(inspect.signature(original_method))

                msg = (
                    context + "\n"
                    f"Your bound method '{func_name}{func_sig}' has an incorrect signature.\n"
                    "Bound methods must have exactly one positional parameter in addition to self.\n"
                    "The first parameter should be self (required for bound methods).\n"
                    "The second parameter should be state -- a dictionary of the current state of the viewer.\n"
                    "\nYour method looks like this:\n"
                    "class YourViewer(Viewer):\n"
                    f"    def {func_name}{func_sig}:\n"
                    "        ... your function code ...\n"
                    "\nIt should look like this:\n"
                    "class YourViewer(Viewer):\n"
                    f"    def {func_name}(self, state{optional_part}):\n"
                    "        ... your function code ..."
                )
                raise ValueError(msg)
            else:
                func_sig = str(inspect.signature(func))
                bound_elsewhere = get_self(func) and get_self(func) is not self
                if bound_elsewhere:
                    func_name = f"self.{func_name}"
                    func_sig = f"(self, {func_sig[1:]})"
                    add_self = True
                else:
                    add_self = False
                msg = (
                    context + "\n"
                    f"Your function '{func_name}{func_sig}' has an incorrect signature.\n"
                    "Functions must have exactly one positional parameter\n"
                    "which corresponds to a dictionary of the current state of the viewer.\n"
                    "\nYour function looks like this:\n"
                    f"def {func_name}{func_sig}:\n"
                    "    ... your function code ...\n"
                    "\nIt should look like this:\n"
                    f"def {func_name}({'self, ' if add_self else ''}state{optional_part}):\n"
                    "    ... your function code ..."
                )
                raise ValueError(msg)

        # If we've made it here, the function has exactly one required positional parameter
        # which means it's callable by the viewer.
        return func

    def perform_callbacks(self, name: str) -> bool:
        """Perform callbacks for all parameters that have changed"""
        if self._in_callbacks:
            return
        try:
            self._in_callbacks = True
            if name in self.callbacks:
                for callback in self.callbacks[name]:
                    callback(self.state)
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

        callback = self._prepare_function(
            callback,
            context="Setting on_change callback:",
        )

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
    def remove_parameter(self, name: str) -> None:
        """
        Remove a parameter from the viewer.

        Parameters
        ----------
        name : str
            Name of the parameter to remove
        """
        if name in self.parameters:
            del self.parameters[name]

    @validate_parameter_operation("add", ParameterType.text)
    def add_text(
        self,
        name: str,
        *,
        value: Union[str, NoInitialValue] = NO_INITIAL_VALUE,
    ) -> None:
        """
        Add a text input parameter to the viewer.

        Creates a text box in the GUI that accepts any string input.
        See :class:`~syd.parameters.TextParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : Union[str, NoInitialValue]
            Initial text value
            If not provided, the parameter will be empty.

        Examples
        --------
        >>> viewer.add_text('title', value='My Plot')
        >>> viewer.state['title']
        'My Plot'
        """
        try:
            new_param = ParameterType.text.value(name, value)
        except Exception as e:
            raise ParameterAddError(name, "text", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.boolean)
    def add_boolean(
        self,
        name: str,
        *,
        value: Union[bool, NoInitialValue] = NO_INITIAL_VALUE,
    ) -> None:
        """
        Add a boolean parameter to the viewer.

        Creates a checkbox in the GUI that can be toggled on/off.
        See :class:`~syd.parameters.BooleanParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : Union[bool, NoInitialValue]
            Initial state (True=checked, False=unchecked)
            If not provided, the parameter will be checked.

        Examples
        --------
        >>> viewer.add_boolean('show_grid', value=True)
        >>> viewer.state['show_grid']
        True
        """
        try:
            new_param = ParameterType.boolean.value(name, value)
        except Exception as e:
            raise ParameterAddError(name, "boolean", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.selection)
    def add_selection(
        self,
        name: str,
        *,
        value: Union[Any, NoInitialValue] = NO_INITIAL_VALUE,
        options: List[Any],
    ) -> None:
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
        >>> viewer.state['color']
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
        self,
        name: str,
        *,
        value: Union[List[Any], NoInitialValue] = NO_INITIAL_VALUE,
        options: List[Any],
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
        value : Union[list, NoInitialValue]
            Initially selected values (must all be in options)
            If not provided, the parameter will be empty.
        options : list
            List of values that can be selected

        Examples
        --------
        >>> viewer.add_multiple_selection('toppings',
        ...     value=['cheese'],
        ...     options=['cheese', 'pepperoni', 'mushrooms'])
        >>> viewer.state['toppings']
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
        value: Union[Union[float, int], NoInitialValue] = NO_INITIAL_VALUE,
        min: Union[float, int],
        max: Union[float, int],
    ) -> None:
        """
        Add an integer parameter to the viewer.

        Creates a slider to select whole numbers between a minimum and maximum.
        See :class:`~syd.parameters.IntegerParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI and internal identifier)
        value : Union[int, NoInitialValue]
            Initial value (default position of the slider)
            If not provided, the parameter will be set to the minimum value.
        min : int
            Minimum allowed value
        max : int
            Maximum allowed value

        Examples
        --------
        >>> viewer.add_integer('age', value=25, min=0, max=120)

        >>> viewer.add_integer('year', value=2023, min=1900, max=2100)
        """
        try:
            new_param = ParameterType.integer.value(name, value, min, max)
        except Exception as e:
            raise ParameterAddError(name, "integer", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.float)
    def add_float(
        self,
        name: str,
        *,
        value: Union[Union[float, int], NoInitialValue] = NO_INITIAL_VALUE,
        min: Union[float, int],
        max: Union[float, int],
        step: float = 0.01,
    ) -> None:
        """
        Add a float parameter to the viewer.

        Creates a slider to select decimal numbers between a minimum and maximum.
        See :class:`~syd.parameters.FloatParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (internal identifier)
        value : Union[float, NoInitialValue]
            Initial value (default position of the slider)
            If not provided, the parameter will be set to the minimum value.
        min : float
            Minimum allowed value
        max : float
            Maximum allowed value
        step : float, optional
            Step size for the slider (default: 0.01)

        Examples
        --------
        >>> viewer.add_float('temperature', value=98.6, min=95.0, max=105.0, step=0.1)

        >>> viewer.add_float('price', value=9.99, min=0.0, max=100.0, step=0.01)
        """
        try:
            new_param = ParameterType.float.value(name, value, min, max, step)
        except Exception as e:
            raise ParameterAddError(name, "float", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.integer_range)
    def add_integer_range(
        self,
        name: str,
        *,
        value: Union[
            Tuple[Union[float, int], Union[float, int]], NoInitialValue
        ] = NO_INITIAL_VALUE,
        min: Union[float, int],
        max: Union[float, int],
    ) -> None:
        """
        Add an integer range parameter to the viewer.

        Creates a range slider to select a range of whole numbers between bounds.
        See :class:`~syd.parameters.IntegerRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (internal identifier)
        value : Union[tuple[int, int], NoInitialValue]
            Initial (low, high) values for the range
            If not provided, the parameter will be set to the full range.
        min : int
            Minimum allowed value for the range
        max : int
            Maximum allowed value for the range

        Examples
        --------
        >>> viewer.add_integer_range('age_range', value=(25, 45), min=18, max=100)

        >>> viewer.add_integer_range('year_range', value=(2000, 2020), min=1900, max=2100)
        """
        try:
            new_param = ParameterType.integer_range.value(name, value, min, max)
        except Exception as e:
            raise ParameterAddError(name, "integer_range", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.float_range)
    def add_float_range(
        self,
        name: str,
        *,
        value: Union[
            Tuple[Union[float, int], Union[float, int]], NoInitialValue
        ] = NO_INITIAL_VALUE,
        min: Union[float, int],
        max: Union[float, int],
        step: float = 0.01,
    ) -> None:
        """
        Add a float range parameter to the viewer.

        Creates a range slider to select a range of decimal numbers between bounds.
        See :class:`~syd.parameters.FloatRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (internal identifier)
        value : Union[tuple[float, float], NoInitialValue]
            Initial (low, high) values for the range
            If not provided, the parameter will be set to the full range.
        min : float
            Minimum allowed value for the range
        max : float
            Maximum allowed value for the range
        step : float, optional
            Step size for the slider (default: 0.01)

        Examples
        --------
        >>> viewer.add_float_range('temp_range', value=(97.0, 99.0), min=95.0, max=105.0, step=0.1)

        >>> viewer.add_float_range('price_range', value=(10.0, 50.0), min=0.0, max=100.0, step=0.01)
        """
        try:
            new_param = ParameterType.float_range.value(name, value, min, max, step)
        except Exception as e:
            raise ParameterAddError(name, "float_range", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.unbounded_integer)
    def add_unbounded_integer(
        self,
        name: str,
        *,
        value: Union[Union[float, int], NoInitialValue] = NO_INITIAL_VALUE,
    ) -> None:
        """
        Add an unbounded integer parameter to the viewer.

        Creates a text input box in the GUI for entering whole numbers. Unlike
        add_integer(), this allows very large numbers without bounds.
        See :class:`~syd.parameters.UnboundedIntegerParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : Union[int, NoInitialValue]
            Initial value
            If not provided, the parameter will be set to 0.

        Examples
        --------
        >>> viewer.add_unbounded_integer('population', value=1000000)
        >>> viewer.state['population']
        1000000
        """
        try:
            new_param = ParameterType.unbounded_integer.value(name, value)
        except Exception as e:
            raise ParameterAddError(name, "unbounded_integer", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ParameterType.unbounded_float)
    def add_unbounded_float(
        self,
        name: str,
        *,
        value: Union[Union[float, int], NoInitialValue] = NO_INITIAL_VALUE,
        step: Optional[float] = None,
    ) -> None:
        """
        Add an unbounded decimal number parameter to the viewer.

        Creates a text input box in the GUI for entering numbers. Unlike add_float(),
        this allows very large or precise numbers without bounds. Values can optionally
        be rounded to a step size.
        See :class:`~syd.parameters.UnboundedFloatParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter (used as label in GUI)
        value : Union[float, NoInitialValue]
            Initial value
            If not provided, the parameter will be set to 0.
        step : float, optional
            Size of each increment (or None for no rounding)

        Examples
        --------
        >>> viewer.add_unbounded_float('wavelength', value=550e-9, step=1e-9)
        >>> viewer.state['wavelength']
        5.5e-07
        >>> # Values will be rounded if step is provided
        >>> viewer.update_unbounded_float('wavelength', value=550.7e-9)
        >>> viewer.state['wavelength']
        5.51e-07
        """
        try:
            new_param = ParameterType.unbounded_float.value(name, value, step)
        except Exception as e:
            raise ParameterAddError(name, "unbounded_float", str(e)) from e
        else:
            self.parameters[name] = new_param

    @validate_parameter_operation("add", ActionType.button)
    def add_button(
        self,
        name: str,
        *,
        label: Union[str, NoInitialValue] = NO_INITIAL_VALUE,
        callback: Callable[[], None],
        replot: bool = True,
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
        label : Union[str, NoInitialValue]
            Text to display on the button
            If not provided, the parameter's label will be set to the name.
        callback : callable
            Function to call when the button is clicked (takes state as a single argument)
        replot : bool, optional
            Whether to replot the figure after the callback is called.
            (default: True)

        Examples
        --------
        >>> def save_figure(state):
        ...     print("Saving figure...")
        ...     viewer.figure.savefig('last_figure.png')
        >>> viewer.add_button('save', label='Save Figure', callback=save_figure, replot=False)

        >>> def print_plot_info(state):
        ...     print(f"Current plot info: {state['plot_info']}")
        >>> viewer.add_button('print_info', label='Print Plot Info', callback=print_plot_info, replot=False)

        >>> def reset_plot(state):
        ...     print("Resetting plot...")
        >>> viewer.add_button('reset', label='Reset Plot', callback=reset_plot)
        """
        try:
            callback = self._prepare_function(
                callback,
                context="Setting button callback:",
            )

            new_param = ActionType.button.value(name, label, callback, replot)
        except Exception as e:
            raise ParameterAddError(name, "button", str(e)) from e
        else:
            self.parameters[name] = new_param

    # -------------------- parameter update methods --------------------
    @validate_parameter_operation("update", ParameterType.text)
    def update_text(
        self, name: str, *, value: Union[str, NoUpdate] = NO_UPDATE
    ) -> None:
        """
        Update a text parameter's value.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_text`.
        See :class:`~syd.parameters.TextParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the text parameter to update
        value : Union[str, NoUpdate], optional
            New text value (if not provided, no change)

        Examples
        --------
        >>> viewer.add_text('title', value='Original Title')
        >>> viewer.update_text('title', value='New Title')
        >>> viewer.state['title']
        'New Title'
        """
        updates = {}
        if not value == NO_UPDATE:
            updates["value"] = value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.boolean)
    def update_boolean(
        self, name: str, *, value: Union[bool, NoUpdate] = NO_UPDATE
    ) -> None:
        """
        Update a boolean parameter's value.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_boolean`.
        See :class:`~syd.parameters.BooleanParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the boolean parameter to update
        value : Union[bool, NoUpdate], optional
            New state (True/False) (if not provided, no change)

        Examples
        --------
        >>> viewer.add_boolean('show_grid', value=True)
        >>> viewer.update_boolean('show_grid', value=False)
        >>> viewer.state['show_grid']
        False
        """
        updates = {}
        if not value == NO_UPDATE:
            updates["value"] = value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.selection)
    def update_selection(
        self,
        name: str,
        *,
        value: Union[Any, NoUpdate] = NO_UPDATE,
        options: Union[List[Any], NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update a selection parameter's value and/or options.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_selection`.
        See :class:`~syd.parameters.SelectionParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the selection parameter to update
        value : Union[Any, NoUpdate], optional
            New selected value (must be in options) (if not provided, no change)
        options : Union[list, NoUpdate], optional
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
        if not value == NO_UPDATE:
            updates["value"] = value
        if not options == NO_UPDATE:
            updates["options"] = options
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.multiple_selection)
    def update_multiple_selection(
        self,
        name: str,
        *,
        value: Union[List[Any], NoUpdate] = NO_UPDATE,
        options: Union[List[Any], NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update a multiple selection parameter's values and/or options.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_multiple_selection`.
        See :class:`~syd.parameters.MultipleSelectionParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the multiple selection parameter to update
        value : Union[list, NoUpdate], optional
            New list of selected values (all must be in options) (if not provided, no change)
        options : Union[list, NoUpdate], optional
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
        if not value == NO_UPDATE:
            updates["value"] = value
        if not options == NO_UPDATE:
            updates["options"] = options
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.integer)
    def update_integer(
        self,
        name: str,
        *,
        value: Union[int, NoUpdate] = NO_UPDATE,
        min: Union[int, NoUpdate] = NO_UPDATE,
        max: Union[int, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update an integer parameter.

        Change the value or bounds of an existing integer parameter.
        See :class:`~syd.parameters.IntegerParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter to update
        value : Union[int, NoUpdate], optional
            New value
        min : Union[int, NoUpdate], optional
            New minimum allowed value
        max : Union[int, NoUpdate], optional
            New maximum allowed value

        Examples
        --------
        >>> viewer.update_integer('age', value=30)  # Update just the value

        >>> viewer.update_integer('year', min=2000, max=2023)  # Update just the bounds
        """
        updates = {}
        if not isinstance(value, NoUpdate):
            updates["value"] = int(value)
        if not isinstance(min, NoUpdate):
            updates["min"] = int(min)
        if not isinstance(max, NoUpdate):
            updates["max"] = int(max)

        parameter = self.parameters[name]
        parameter.update(updates)

    @validate_parameter_operation("update", ParameterType.float)
    def update_float(
        self,
        name: str,
        *,
        value: Union[float, NoUpdate] = NO_UPDATE,
        min: Union[float, NoUpdate] = NO_UPDATE,
        max: Union[float, NoUpdate] = NO_UPDATE,
        step: Union[float, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update a float parameter.

        Change the value, bounds, or step size of an existing float parameter.
        See :class:`~syd.parameters.FloatParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter to update
        value : Union[float, NoUpdate], optional
            New value
        min : Union[float, NoUpdate], optional
            New minimum allowed value
        max : Union[float, NoUpdate], optional
            New maximum allowed value
        step : Union[float, NoUpdate], optional
            New step size for the slider

        Examples
        --------
        >>> viewer.update_float('temperature', value=99.5)  # Update just the value

        >>> viewer.update_float('price', min=5.0, max=200.0, step=0.05)  # Update bounds and step
        """
        updates = {}
        if not isinstance(value, NoUpdate):
            updates["value"] = float(value)
        if not isinstance(min, NoUpdate):
            updates["min"] = float(min)
        if not isinstance(max, NoUpdate):
            updates["max"] = float(max)
        if not isinstance(step, NoUpdate):
            updates["step"] = float(step)

        parameter = self.parameters[name]
        parameter.update(updates)

    @validate_parameter_operation("update", ParameterType.integer_range)
    def update_integer_range(
        self,
        name: str,
        *,
        value: Union[Tuple[int, int], NoUpdate] = NO_UPDATE,
        min: Union[int, NoUpdate] = NO_UPDATE,
        max: Union[int, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update an integer range parameter.

        Change the range values or bounds of an existing integer range parameter.
        See :class:`~syd.parameters.IntegerRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter to update
        value : Union[tuple[int, int], NoUpdate], optional
            New (low, high) values
        min : Union[int, NoUpdate], optional
            New minimum allowed value
        max : Union[int, NoUpdate], optional
            New maximum allowed value

        Examples
        --------
        >>> viewer.update_integer_range('age_range', value=(30, 50))  # Update just the values

        >>> viewer.update_integer_range('year_range', min=1950, max=2023)  # Update just the bounds
        """
        updates = {}
        if not isinstance(value, NoUpdate):
            val_low, val_high = value
            updates["value"] = (int(val_low), int(val_high))
        if not isinstance(min, NoUpdate):
            updates["min"] = int(min)
        if not isinstance(max, NoUpdate):
            updates["max"] = int(max)

        parameter = self.parameters[name]
        parameter.update(updates)

    @validate_parameter_operation("update", ParameterType.float_range)
    def update_float_range(
        self,
        name: str,
        *,
        value: Union[Tuple[float, float], NoUpdate] = NO_UPDATE,
        min: Union[float, NoUpdate] = NO_UPDATE,
        max: Union[float, NoUpdate] = NO_UPDATE,
        step: Union[float, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update a float range parameter.

        Change the range values, bounds, or step size of an existing float range parameter.
        See :class:`~syd.parameters.FloatRangeParameter` for details.

        Parameters
        ----------
        name : str
            Name of the parameter to update
        value : Union[tuple[float, float], NoUpdate], optional
            New (low, high) values
        min : Union[float, NoUpdate], optional
            New minimum allowed value
        max : Union[float, NoUpdate], optional
            New maximum allowed value
        step : Union[float, NoUpdate], optional
            New step size for the slider

        Examples
        --------
        >>> viewer.update_float_range('temp_range', value=(97.5, 98.5))  # Update just the values

        >>> viewer.update_float_range(
        ...     'price_range',
        ...     min=10.0,
        ...     max=500.0,
        ...     step=0.5
        ... )  # Update bounds and step
        """
        updates = {}
        if not isinstance(value, NoUpdate):
            val_low, val_high = value
            updates["value"] = (float(val_low), float(val_high))
        if not isinstance(min, NoUpdate):
            updates["min"] = float(min)
        if not isinstance(max, NoUpdate):
            updates["max"] = float(max)
        if not isinstance(step, NoUpdate):
            updates["step"] = float(step)

        parameter = self.parameters[name]
        parameter.update(updates)

    @validate_parameter_operation("update", ParameterType.unbounded_integer)
    def update_unbounded_integer(
        self,
        name: str,
        *,
        value: Union[int, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update an unbounded integer parameter's value and/or bounds.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_unbounded_integer`.
        See :class:`~syd.parameters.UnboundedIntegerParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the unbounded integer parameter to update
        value : Union[int, NoUpdate], optional
            New value (if not provided, no change)

        Examples
        --------
        >>> viewer.add_unbounded_integer('population', value=1000000)
        >>> # Update just the value
        >>> viewer.update_unbounded_integer('population', value=2000000)
        """
        updates = {}
        if not value == NO_UPDATE:
            updates["value"] = value
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ParameterType.unbounded_float)
    def update_unbounded_float(
        self,
        name: str,
        *,
        value: Union[float, NoUpdate] = NO_UPDATE,
        step: Union[Optional[float], NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update an unbounded float parameter's value, bounds, and/or step size.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_unbounded_float`.
        See :class:`~syd.parameters.UnboundedFloatParameter` for details about value validation.

        Parameters
        ----------
        name : str
            Name of the unbounded float parameter to update
        value : Union[float, NoUpdate], optional
            New value (will be rounded if step is set) (if not provided, no change)
        step : Union[Optional[float], NoUpdate], optional
            New step size for rounding, or None for no rounding (if not provided, no change)

        Examples
        --------
        >>> viewer.add_unbounded_float('wavelength', value=550e-9, step=1e-9)
        >>> # Update value (will be rounded if step is set)
        >>> viewer.update_unbounded_float('wavelength', value=632.8e-9)
        >>> # Change step size
        >>> viewer.update_unbounded_float('wavelength', step=0.1e-9)
        >>> # Remove step size (allow any precision)
        >>> viewer.update_unbounded_float('wavelength', step=None)
        """
        updates = {}
        if not value == NO_UPDATE:
            updates["value"] = value
        if not step == NO_UPDATE:
            updates["step"] = step
        if updates:
            self.parameters[name].update(updates)

    @validate_parameter_operation("update", ActionType.button)
    def update_button(
        self,
        name: str,
        *,
        label: Union[str, NoUpdate] = NO_UPDATE,
        callback: Union[Callable[[], None], NoUpdate] = NO_UPDATE,
        replot: Union[bool, NoUpdate] = NO_UPDATE,
    ) -> None:
        """
        Update a button parameter's label and/or callback function.

        Updates a parameter created by :meth:`~syd.viewer.Viewer.add_button`.
        See :class:`~syd.parameters.ButtonAction` for details.

        Parameters
        ----------
        name : str
            Name of the button parameter to update
        label : Union[str, NoUpdate], optional
            New text to display on the button (if not provided, no change)
        callback : Union[callable, NoUpdate], optional
            New function to call when clicked (if not provided, no change)
        replot : Union[bool, NoUpdate], optional
            Whether to replot the figure after the callback is called.
            (default: True)

        Examples
        --------
        >>> def new_callback(state):
        ...     print("New action...")
        >>> viewer.update_button('reset',
        ...                     label='New Action!',
        ...                     callback=new_callback,
        ...                     replot=False)
        """
        updates = {}
        if not label == NO_UPDATE:
            updates["label"] = label
        if not callback == NO_UPDATE:
            try:
                callback = self._prepare_function(
                    callback,
                    context="Updating button callback:",
                )
            except Exception as e:
                raise ParameterUpdateError(
                    name,
                    "button",
                    str(e),
                ) from e
            else:
                updates["callback"] = callback
        if not replot == NO_UPDATE:
            updates["replot"] = replot
        if updates:
            self.parameters[name].update(updates)
