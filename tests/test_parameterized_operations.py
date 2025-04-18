import pytest
from itertools import combinations
from syd.parameters import ParameterType, ActionType
from syd.support import ParameterAddError, ParameterUpdateError, ParameterUpdateWarning
from tests.support import MockViewer, check_no_change


def valid_button_callback(state):
    pass


# Test configurations for different parameter types
PARAM_CONFIGS = {
    ParameterType.text: {
        "basic_value": "hello",
        "updated_value": "world",
        "convert_values": [(123, "123"), (456.789, "456.789")],
        "default_value": "",
    },
    ParameterType.boolean: {
        "basic_value": True,
        "updated_value": False,
        "convert_values": [(1, True), (0, False), ("hello", True), ([], False)],
        "default_value": True,
    },
    ParameterType.selection: {
        "basic_value": "a",
        "updated_value": "b",
        "default_value": "a",
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
        "default_value": [],
        "options": ["a", "b", "c"],
        "extra_kwargs": {"options": ["a", "b", "c"]},
        "consistent_options": ["a", "b", "c", "d"],
        "disjoint_options": ["x", "y", "z"],
        "disjoint_fallback_value": [],
        "bad_value": 123,
        "bad_options": 123,
        "varied_value": [1, "2"],
        "varied_options": [1, "2", 3, "4"],
        "excessive_values": ["a", "a", "b", "b", "c", "c"],
    },
    ParameterType.integer: {
        "basic_value": 1,
        "updated_value": 2,
        "default_value": 0,
        "extra_kwargs": {"min": 0, "max": 10},
        "convert_values": [("5", 5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
    ParameterType.float: {
        "basic_value": 1.5,
        "updated_value": 2.5,
        "default_value": 0,
        "extra_kwargs": {"min": 0, "max": 10},
        "convert_values": [("5.5", 5.5)],
        "clamping_values": [(-100, 0), (100, 10)],
    },
    ParameterType.integer_range: {
        "basic_value": (1, 5),
        "updated_value": (2, 6),
        "default_value": (0, 10),
        "extra_kwargs": {"min": 0, "max": 10},
        "convert_values": [(("5", "8"), (5, 8))],
        "clamping_values": [((-100, 110), (0, 10))],
    },
    ParameterType.float_range: {
        "basic_value": (1.5, 5.5),
        "updated_value": (2.5, 6.5),
        "default_value": (0, 10),
        "extra_kwargs": {"min": 0, "max": 10},
        "convert_values": [(("5.5", "8.5"), (5.5, 8.5))],
        "clamping_values": [((-100, 110), (0, 10))],
    },
    ParameterType.unbounded_integer: {
        "basic_value": 1,
        "updated_value": 2,
        "default_value": 0,
        "extra_kwargs": {},
        "convert_values": [("5", 5)],
    },
    ParameterType.unbounded_float: {
        "basic_value": 1.5,
        "updated_value": 2.5,
        "default_value": 0,
        "extra_kwargs": {"step": 0.1},
        "convert_values": [("5.5", 5.5)],
    },
    ActionType.button: {
        "extra_kwargs": {
            "label": "Click me",
            "callback": valid_button_callback,
        },
    },
}

all_params = list(ParameterType) + list(ActionType)
all_pairs = list(combinations(all_params, 2))


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
def test_remove_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    assert viewer.parameters[param_name].value == config["basic_value"]

    viewer.remove_parameter(param_name)
    assert param_name not in viewer.parameters
    assert param_name not in viewer.state


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
        with viewer._deploy_app():
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
        with pytest.warns(ParameterUpdateWarning):
            add_method(f"{param_type.name}_clamp_{i}", value=input_value, **kwargs)
        assert viewer.parameters[f"{param_type.name}_clamp_{i}"].value == expected

    for i, (input_value, expected) in enumerate(clamping_values):
        with pytest.warns(ParameterUpdateWarning):
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
    with pytest.warns(ParameterUpdateWarning):
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

    # Test that the options list can't be empty
    with pytest.raises(ParameterAddError):
        add_method(
            f"{param_type.name}_empty_options",
            value=config["basic_value"],
            options=[],
        )

    if param_type == ParameterType.multiple_selection:
        update_method(
            f"{param_type.name}_1",
            value=config["excessive_values"],
            options=config["options"],
        )
        assert viewer.parameters[f"{param_type.name}_1"].value == config["options"]

    if param_type == ParameterType.multiple_selection:
        update_method(
            f"{param_type.name}_1",
            value=config["excessive_values"],
            options=config["options"] + config["options"],
        )
        assert viewer.parameters[f"{param_type.name}_1"].value == config["options"]
        assert viewer.parameters[f"{param_type.name}_1"].options == config["options"]


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

    # Test that large values aren't clamped with no bound
    update_method(f"{param_type.name}_1", value=1000)
    assert viewer.parameters[f"{param_type.name}_1"].value == 1000

    update_method(f"{param_type.name}_1", value=-1000)
    assert viewer.parameters[f"{param_type.name}_1"].value == -1000


@pytest.mark.parametrize("param_type", ParameterType)
def test_not_action_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    assert hasattr(viewer.parameters[param_name], "_is_action")
    assert not viewer.parameters[param_name]._is_action


@pytest.mark.parametrize("param_type", ActionType)
def test_is_action_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, **kwargs)
    assert hasattr(viewer.parameters[param_name], "_is_action")
    assert viewer.parameters[param_name]._is_action


@pytest.mark.parametrize("param_type", ParameterType)
def test_not_is_action_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    value = config.get("basic_value", None)
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=value, **kwargs)
    assert hasattr(viewer.parameters[param_name], "_is_action")
    assert not viewer.parameters[param_name]._is_action


@pytest.mark.parametrize("param_type", ParameterType)
def test_no_value_parameter(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"
    add_method(param_name, **kwargs)
    assert viewer.parameters[param_name].value == config["default_value"]


def test_no_label_button_parameter():
    param_type = ActionType.button
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    kwargs.pop("label", None)
    param_name = f"{param_type.name}_1"
    add_method(param_name, **kwargs)
    assert viewer.parameters[param_name].label == param_name


def test_on_change_no_parameter():
    def valid_callable(viewer, state):
        pass

    viewer = MockViewer()
    with pytest.raises(ValueError):
        viewer.on_change("not_a_parameter", valid_callable)

    msg = "Callback should not be added when parameter doesn't exist"
    assert "not_a_parameter" not in viewer.callbacks, msg


@pytest.mark.parametrize("param_type", ParameterType)
def test_setting_parameter_values(param_type):
    viewer = MockViewer()
    config = PARAM_CONFIGS[param_type]
    add_method = getattr(viewer, f"add_{param_type.name}")
    kwargs = config.get("extra_kwargs", {})
    param_name = f"{param_type.name}_1"

    add_method(param_name, value=config["basic_value"], **kwargs)
    assert viewer.parameters[param_name].value == config["basic_value"]

    viewer.set_parameter_value(param_name, config["updated_value"])
    assert viewer.parameters[param_name].value == config["updated_value"]

    with pytest.raises(ValueError):
        viewer.set_parameter_value(
            param_name + "_wontfindthis", config["updated_value"]
        )


@pytest.mark.parametrize("param_type1, param_type2", all_pairs)
def test_parameter_type_compatibility(param_type1, param_type2):
    param_name = "parameter_name"
    config1 = PARAM_CONFIGS[param_type1]
    config2 = PARAM_CONFIGS[param_type2]

    kwargs1 = {}
    kwargs2 = {}
    if "basic_value" in config1:
        kwargs1["value"] = config1["basic_value"]
    if "basic_value" in config2:
        kwargs2["value"] = config2["basic_value"]

    if "extra_kwargs" in config1:
        kwargs1.update(config1["extra_kwargs"])
    if "extra_kwargs" in config2:
        kwargs2.update(config2["extra_kwargs"])

    viewer = MockViewer()
    add_method1 = getattr(viewer, f"add_{param_type1.name}")
    add_method2 = getattr(viewer, f"add_{param_type2.name}")
    update_method2 = getattr(viewer, f"update_{param_type2.name}")
    add_method1(param_name, **kwargs1)
    with pytest.raises(ParameterAddError):
        add_method2(param_name, **kwargs2)
    with pytest.raises(ParameterUpdateError):
        update_method2(param_name, **kwargs2)

    viewer = MockViewer()
    add_method1 = getattr(viewer, f"add_{param_type1.name}")
    update_method1 = getattr(viewer, f"update_{param_type1.name}")
    add_method2 = getattr(viewer, f"add_{param_type2.name}")
    add_method2(param_name, **kwargs2)
    with pytest.raises(ParameterAddError):
        add_method1(param_name, **kwargs1)
    with pytest.raises(ParameterUpdateError):
        update_method1(param_name, **kwargs1)
