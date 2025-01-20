import pytest
from typing import List
from inspect import signature
from syd.parameters import ParameterType, get_parameter_attributes
from tests.support import MockViewer


def get_method_parameters(method) -> List[str]:
    """Extract parameter types from method signature, excluding 'self' and 'name'"""
    sig = signature(method)
    return [name for name in sig.parameters if name != "self"]


def test_all_parameter_types_have_methods():
    """Check that each ParameterType has corresponding add/update methods"""
    viewer = MockViewer()

    for param_type in ParameterType:
        method_base = param_type.name
        add_method = f"add_{method_base}"
        update_method = f"update_{method_base}"

        assert hasattr(viewer, add_method), f"Missing add method for {param_type}"
        assert hasattr(viewer, update_method), f"Missing update method for {param_type}"


def test_all_methods_have_parameter_types():
    """Check that each add/update method corresponds to a ParameterType"""
    viewer = MockViewer()

    # Get all method names
    methods = [method for method in dir(viewer) if not method.startswith("_")]

    # Check add methods
    add_methods = [m[4:] for m in methods if m.startswith("add_")]
    update_methods = [m[7:] for m in methods if m.startswith("update_")]

    param_names = {param_type.name for param_type in ParameterType}

    assert (
        set(add_methods) == param_names
    ), "Mismatch between add methods and parameter types"
    assert (
        set(update_methods) == param_names
    ), "Mismatch between update methods and parameter types"


@pytest.mark.parametrize("param_type", ParameterType)
def test_method_signatures_match_parameters(param_type):
    """Check that method signatures match parameter attributes"""
    viewer = MockViewer()
    param_class = param_type.value

    # Get parameter attributes (excluding name and internal attributes)
    param_attrs = get_parameter_attributes(param_class)

    # Test add method
    add_method = getattr(viewer, f"add_{param_type.name}")
    add_params = get_method_parameters(add_method)

    # For add methods, all parameters should be required (no _NoUpdate)
    for attr_name in param_attrs:
        assert attr_name in add_params, f"Missing {attr_name} in add_{param_type.name}"

    # Test update method
    update_method = getattr(viewer, f"update_{param_type.name}")
    update_params = get_method_parameters(update_method)

    for attr_name in param_attrs:
        assert (
            attr_name in update_params
        ), f"Missing {attr_name} in update_{param_type.name}"


def test_no_extra_parameters():
    """Check that methods don't have extra parameters not present in parameter classes"""
    viewer = MockViewer()

    for param_type in ParameterType:
        param_class = param_type.value
        param_attrs = get_parameter_attributes(param_class)

        # Check add method
        add_method = getattr(viewer, f"add_{param_type.name}")
        add_params = get_method_parameters(add_method)
        assert set(add_params) <= set(
            param_attrs
        ), f"Extra parameters in add_{param_type.name}"

        # Check update method
        update_method = getattr(viewer, f"update_{param_type.name}")
        update_params = get_method_parameters(update_method)
        assert set(update_params) <= set(
            param_attrs
        ), f"Extra parameters in update_{param_type.name}"
