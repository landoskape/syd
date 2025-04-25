from abc import ABCMeta
from typing import Any, List, Union
from warnings import warn
from contextlib import contextmanager
import matplotlib.pyplot as plt


def show_open_servers():
    """Show all open Flask servers."""
    from .flask_deployment.deployer import server_manager

    print(server_manager.servers)


def close_servers(port: Union[int, None] = None):
    """Close any Flask servers running on a given port (or all of them).

    Parameters
    ----------
    port : int | None, optional
        The port of the Flask server to close. If None, all servers will be closed.

    Examples
    --------
    >>> close()  # Close all Flask servers
    >>> close(8000)  # Close the Flask server running on port 8000
    """
    from .flask_deployment.deployer import server_manager

    server_manager.close_app(port)


@contextmanager
def plot_context():
    plt.ioff()
    try:
        yield
    finally:
        plt.ion()


class NoUpdate:
    """Singleton class to represent a non-update in parameter operations."""

    _instance = None
    _noupdate_identifier = "NO_UPDATE"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __eq__(self, other: Any):
        """This makes sure all comparisons of NoUpdate objects return True"""
        return isinstance(other, NoUpdate) or (
            hasattr(other, "_noupdate_identifier")
            and other._noupdate_identifier == self._noupdate_identifier
        )

    def __repr__(self):
        return "NotUpdated"


class NoInitialValue:
    """Singleton class to represent a non-initial value in parameter operations."""

    _instance = None
    _noinitialvalue_identifier = "NO_INITIAL_VALUE"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __eq__(self, other: Any):
        """This makes sure all comparisons of NoInitialValue objects return True"""
        return isinstance(other, NoInitialValue) or (
            hasattr(other, "_noinitialvalue_identifier")
            and other._noinitialvalue_identifier == self._noinitialvalue_identifier
        )

    def __repr__(self):
        return "NotInitialized"


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


class ParameterUpdateWarning(Warning):
    """
    Warning raised when there is a non-critical issue updating a parameter.

    Parameters
    ----------
    parameter_name : str
        Name of the parameter that had the warning
    parameter_type : str
        Type of the parameter
    message : str, optional
        Additional warning details
    """

    def __init__(self, parameter_name: str, parameter_type: str, message: str = None):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
        super().__init__(
            f"Warning updating {parameter_type} parameter '{parameter_name}'"
            + (f": {message}" if message else "")
        )


def warn_parameter_update(
    parameter_name: str, parameter_type: str, message: str = None
):
    """
    Warn the user that a parameter has been updated to a value behind the scenes.
    """
    warn(ParameterUpdateWarning(parameter_name, parameter_type, message))


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


class ParameterMeta(ABCMeta):
    _parameter_types = {}
    _parameter_ids = {}  # Store unique identifiers for our parameter types

    def __new__(cls, name, bases, namespace):
        parameter_class = super().__new__(cls, name, bases, namespace)
        if name != "Parameter":
            # Generate a unique ID for this parameter type
            type_id = f"syd.parameters.{name}"  # Using fully qualified name
            cls._parameter_ids[name] = type_id

            # Add ID to the class
            if not hasattr(parameter_class, "_parameter_type_id"):
                setattr(parameter_class, "_parameter_type_id", type_id)
            else:
                if getattr(parameter_class, "_parameter_type_id") != type_id:
                    raise ValueError(
                        f"Parameter type {name} has multiple IDs: {type_id} and {getattr(parameter_class, '_parameter_type_id')}"
                    )
            cls._parameter_types[name] = parameter_class
        return parameter_class

    def __instancecheck__(cls, instance):
        type_id = cls._parameter_ids.get(cls.__name__)
        if not type_id:
            return False

        # Check if instance has our type ID
        return getattr(instance.__class__, "_parameter_type_id", None) == type_id
