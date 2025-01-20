import pytest
from syd.parameters import (
    ParameterAddError,
    ParameterUpdateError,
    ParameterType,
)
from tests.support import MockViewer, check_no_change


# Test configurations for different parameter types
PARAM_CONFIGS = {
    ParameterType.text: {
        "basic_value": "hello",
        "updated_value": "world",
        "convert_values": [(123, "123"), (456.789, "456.789")],
    },
    ParameterType.boolean: {
        "basic_value": True,
        "updated_value": False,
        "convert_values": [(1, True), (0, False), ("hello", True), ([], False)],
    },
    ParameterType.selection: {
        "basic_value": "a",
        "updated_value": "b",
        "options": ["a", "b", "c"],
        "extra_kwargs": {"options": ["a", "b", "c"]},
        "consistent_options": ["a", "b", "c", "d"],
        "disjoint_options": ["x", "y", "z"],
        "disjoint_fallback_value": "x",
        "bad_value": 123,
        "bad_options": 123,
        "varied_value": 1,
        "varied_options": [1, "2", 3, "4"],
    },
    ParameterType.multiple_selection: {
        "basic_value": ["a"],
        "updated_value": ["b"],
        "options": ["a", "b", "c"],
        "extra_kwargs": {"options": ["a", "b", "c"]},
        "consistent_options": ["a", "b", "c", "d"],
        "disjoint_options": ["x", "y", "z"],
        "disjoint_fallback_value": [],
        "bad_value": 123,
        "bad_options": 123,
        "varied_value": [1, "2"],
        "varied_options": [1, "2", 3, "4"],
    },
    ParameterType.integer: {
        "basic_value": 1,
        "updated_value": 2,
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [("5", 5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
    ParameterType.float: {
        "basic_value": 1.5,
        "updated_value": 2.5,
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [("5.5", 5.5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
    ParameterType.integer_range: {
        "basic_value": (1, 5),
        "updated_value": (2, 6),
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [(("5", "8"), (5, 8))],
        "clamping_values": [((-100, 110), (0, 10))],
    },
    ParameterType.float_range: {
        "basic_value": (1.5, 5.5),
        "updated_value": (2.5, 6.5),
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [(("5.5", "8.5"), (5.5, 8.5))],
        "clamping_values": [((-100, 110), (0, 10))],
    },
    ParameterType.unbounded_integer: {
        "basic_value": 1,
        "updated_value": 2,
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [("5", 5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
    ParameterType.unbounded_float: {
        "basic_value": 1.5,
        "updated_value": 2.5,
        "extra_kwargs": {"min_value": 0, "max_value": 10},
        "convert_values": [("5.5", 5.5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
}


@pytest.mark.parametrize("param_type", ParameterType)
def test_invalid_parameter_name(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})

    with pytest.raises(ParameterAddError):
        add_method(123, **kwargs)

    with pytest.raises(ParameterUpdateError):
        update_method(123, **kwargs)


@pytest.mark.parametrize("param_type", ParameterType)
def test_basic_add_and_update(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    assert viewer.parameters[param_name].value == config["basic_value"]

    update_method(param_name, value=config["updated_value"], **kwargs)
    assert viewer.parameters[param_name].value == config["updated_value"]


@pytest.mark.parametrize("param_type", ParameterType)
def test_duplicate_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    with pytest.raises(ParameterAddError):
        add_method(param_name, value=config["basic_value"], **kwargs)


@pytest.mark.parametrize("param_type", ParameterType)
def test_add_while_deployed(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})

    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            add_method(
                f"{param_type.name}_deployed", value=config["basic_value"], **kwargs
            )


@pytest.mark.parametrize("param_type", ParameterType)
def test_update_nonexistent(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})

    with pytest.raises(ParameterUpdateError):
        update_method(
            f"{param_type.name}_doesnt_exist", value=config["basic_value"], **kwargs
        )


@pytest.mark.parametrize("param_type", ParameterType)
def test_empty_update(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    with check_no_change(viewer, param_name):
        update_method(param_name)


ParamsWithConversion = [
    param_type
    for param_type in ParameterType
    if "convert_values" in PARAM_CONFIGS[param_type]
]


@pytest.mark.parametrize("param_type", ParamsWithConversion)
def test_type_conversion(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    convert_values = config["convert_values"]
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_convert"

    for i, (input_value, expected) in enumerate(convert_values):
        add_method(f"{param_name}_{i}", value=input_value, **kwargs)
        assert viewer.parameters[f"{param_name}_{i}"].value == expected

    for i, (input_value, expected) in enumerate(convert_values):
        update_method(f"{param_name}_{i}", value=input_value, **kwargs)
        assert viewer.parameters[f"{param_name}_{i}"].value == expected


ParamsWithClamping = [
    param_type
    for param_type in ParameterType
    if "clamping_values" in PARAM_CONFIGS[param_type]
]


@pytest.mark.parametrize("param_type", ParamsWithClamping)
def test_value_clamping(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    clamping_values = config["clamping_values"]
    kwargs = config.get("extra_kwargs", {})

    for i, (input_value, expected) in enumerate(clamping_values):
        with pytest.warns(UserWarning):
            add_method(f"{param_type.name}_clamp_{i}", value=input_value, **kwargs)
        assert viewer.parameters[f"{param_type.name}_clamp_{i}"].value == expected

    for i, (input_value, expected) in enumerate(clamping_values):
        with pytest.warns(UserWarning):
            update_method(f"{param_type.name}_clamp_{i}", value=input_value, **kwargs)
        assert viewer.parameters[f"{param_type.name}_clamp_{i}"].value == expected


@pytest.mark.parametrize(
    "param_type",
    [ParameterType.selection, ParameterType.multiple_selection],
)
def test_selection_specific_operations(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})

    # Setup selection parameter
    add_method(
        f"{param_type.name}_1",
        value=config["basic_value"],
        **kwargs,
    )
    assert viewer.parameters[f"{param_type.name}_1"].value == config["basic_value"]
    assert viewer.parameters[f"{param_type.name}_1"].options == config["options"]

    # Test that updating with consistent options doesn't change the value
    update_method(f"{param_type.name}_1", options=config["consistent_options"])
    assert viewer.parameters[f"{param_type.name}_1"].value == config["basic_value"]
    assert (
        viewer.parameters[f"{param_type.name}_1"].options
        == config["consistent_options"]
    )

    # Test that disjoint options convert the value to the first option
    with pytest.warns(UserWarning):
        update_method(f"{param_type.name}_1", options=config["disjoint_options"])
    assert (
        viewer.parameters[f"{param_type.name}_1"].value
        == config["disjoint_fallback_value"]
    )
    assert (
        viewer.parameters[f"{param_type.name}_1"].options == config["disjoint_options"]
    )

    # Test that you can't update with a disjoint value from current options
    with check_no_change(viewer, f"{param_type.name}_1"):
        with pytest.raises(ParameterUpdateError):
            update_method(f"{param_type.name}_1", value=config["basic_value"])

    # Test that you can't update with a disjoint value and options
    with check_no_change(viewer, f"{param_type.name}_1"):
        with pytest.raises(ParameterUpdateError):
            update_method(
                f"{param_type.name}_1",
                value=config["basic_value"],
                options=config["disjoint_options"],
            )

    # Test that options need to be lists
    with pytest.raises(ParameterAddError):
        add_method(
            f"{param_type.name}_add_error",
            value=config["bad_value"],
            options=config["bad_options"],
        )
    with check_no_change(viewer, f"{param_type.name}_1"):
        with pytest.raises(ParameterUpdateError):
            update_method(f"{param_type.name}_1", options=config["bad_options"])

    # Test that options can be varied in type
    add_method(
        f"{param_type.name}_varied",
        value=config["varied_value"],
        options=config["varied_options"],
    )
    assert (
        viewer.parameters[f"{param_type.name}_varied"].value == config["varied_value"]
    )
    assert (
        viewer.parameters[f"{param_type.name}_varied"].options
        == config["varied_options"]
    )


@pytest.mark.parametrize(
    "param_type",
    [ParameterType.unbounded_integer, ParameterType.unbounded_float],
)
def test_unbounded_specific_operations(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    update_method = getattr(viewer, f"update_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})

    add_method(f"{param_type.name}_1", value=config["basic_value"], **kwargs)
    assert viewer.parameters[f"{param_type.name}_1"].value == config["basic_value"]

    # Test that you can remove a min/max value
    update_method(f"{param_type.name}_1", min_value=None, max_value=None)
    assert viewer.parameters[f"{param_type.name}_1"].min_value is None
    assert viewer.parameters[f"{param_type.name}_1"].max_value is None

    # Test that large values aren't clamped with no bound
    update_method(f"{param_type.name}_1", value=1000)
    assert viewer.parameters[f"{param_type.name}_1"].value == 1000

    update_method(f"{param_type.name}_1", value=-1000)
    assert viewer.parameters[f"{param_type.name}_1"].value == -1000

    # Test that you can add a min/max value and it clamps the current value
    with pytest.warns(UserWarning):
        update_method(f"{param_type.name}_1", min_value=0, max_value=10)
    assert viewer.parameters[f"{param_type.name}_1"].value == 0
    assert viewer.parameters[f"{param_type.name}_1"].min_value == 0
    assert viewer.parameters[f"{param_type.name}_1"].max_value == 10

    # Test that values are clamped within the min/max value
    with pytest.warns(UserWarning):
        update_method(f"{param_type.name}_1", value=15)
    assert viewer.parameters[f"{param_type.name}_1"].value == 10

    with pytest.warns(UserWarning):
        update_method(f"{param_type.name}_1", value=-5)
    assert viewer.parameters[f"{param_type.name}_1"].value == 0
