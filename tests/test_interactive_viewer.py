import pytest
from typing import Dict, Any

from syd.interactive_viewer import InteractiveViewer


class MockViewer(InteractiveViewer):
    """Simple concrete implementation for testing"""

    def plot(self, **kwargs):
        return None


def test_parameter_registration():
    viewer = MockViewer()

    # Test basic parameter registration
    viewer.add_text("text_param", default="default")
    viewer.add_integer("int_param", min_value=0, max_value=10, default=5)
    viewer.add_float("float_param", min_value=0.0, max_value=1.0, default=0.5)

    assert "text_param" in viewer.parameters
    assert "int_param" in viewer.parameters
    assert "float_param" in viewer.parameters

    # Test parameter values
    assert viewer.parameters["text_param"].value == "default"
    assert viewer.parameters["int_param"].value == 5
    assert viewer.parameters["float_param"].value == 0.5


def test_parameter_validation():
    viewer = MockViewer()

    # Test adding parameters while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_text("text_param", default="default")

    # Test updating non-existent parameter
    with pytest.raises(ValueError):
        viewer.update_text("nonexistent", value="value")

    # Test type mismatch
    viewer.add_text("text_param", default="default")
    with pytest.raises(TypeError):
        viewer.update_integer("text_param", minimum=0, maximum=10, value=5)


def test_callbacks():
    viewer = MockViewer()
    callback_called = {"count": 0, "last_state": None}

    def test_callback(state: Dict[str, Any]):
        callback_called["count"] += 1
        callback_called["last_state"] = state

    # Register parameter and callback
    viewer.add_text("param1", default="initial")
    viewer.on_change("param1", test_callback)

    # Test callback triggering
    viewer.set_parameter_value("param1", value="updated")
    assert callback_called["count"] == 1
    assert callback_called["last_state"]["param1"] == "updated"


def test_multiple_callbacks():
    viewer = MockViewer()
    callback_counts = {"param1": 0, "param2": 0}

    def callback1(state: Dict[str, Any]):
        callback_counts["param1"] += 1

    def callback2(state: Dict[str, Any]):
        callback_counts["param2"] += 1

    # Register parameters and callbacks
    viewer.add_text("param1", default="initial")
    viewer.add_text("param2", default="initial")
    viewer.on_change(["param1", "param2"], callback1)
    viewer.on_change("param2", callback2)

    # Test callbacks
    viewer.set_parameter_value("param1", value="updated")
    assert callback_counts["param1"] == 1
    assert callback_counts["param2"] == 0

    viewer.set_parameter_value("param2", value="updated")
    assert callback_counts["param1"] == 2
    assert callback_counts["param2"] == 1


def test_get_state():
    viewer = MockViewer()

    viewer.add_text("text", value="hello")
    viewer.add_integer("int", value=5, min_value=0, max_value=10)
    viewer.add_boolean("bool", value=True)

    state = viewer.get_state()
    assert state == {"text": "hello", "int": 5, "bool": True}


def test_parameter_type_operations():
    viewer = MockViewer()

    # Text parameter
    viewer.add_text("text_param", value="hello")
    assert viewer.parameters["text_param"].value == "hello"
    viewer.update_text("text_param", value="world")
    assert viewer.parameters["text_param"].value == "world"

    # Integer parameter
    viewer.add_integer("int_param", value=5, min_value=0, max_value=10)
    assert viewer.parameters["int_param"].value == 5
    viewer.update_integer("int_param", value=8, min_value=-10, max_value=20)
    assert viewer.parameters["int_param"].value == 8
    assert viewer.parameters["int_param"].min_value == -10
    assert viewer.parameters["int_param"].max_value == 20

    # Float parameter
    viewer.add_float("float_param", value=0.5, min_value=0.0, max_value=1.0)
    assert viewer.parameters["float_param"].value == 0.5
    viewer.update_float("float_param", value=0.8, min_value=-1.0, max_value=2.0)
    assert viewer.parameters["float_param"].value == 0.8
    assert viewer.parameters["float_param"].min_value == -1.0
    assert viewer.parameters["float_param"].max_value == 2.0

    # Boolean parameter
    viewer.add_boolean("bool_param", value=True)
    assert viewer.parameters["bool_param"].value is True
    viewer.update_boolean("bool_param", value=False)
    assert viewer.parameters["bool_param"].value is False

    # Selection parameter
    viewer.add_selection("select_param", value="a", options=["a", "b", "c"])
    assert viewer.parameters["select_param"].value == "a"
    viewer.update_selection("select_param", value="b", options=["a", "b", "c", "d"])
    assert viewer.parameters["select_param"].value == "b"
    assert viewer.parameters["select_param"].options == ["a", "b", "c", "d"]

    # Multiple Selection parameter
    viewer.add_multiple_selection("multiselect_param", value=["x"], options=["x", "y", "z"])
    assert viewer.parameters["multiselect_param"].value == ["x"]
    viewer.update_multiple_selection("multiselect_param", value=["y", "z"], options=["w", "x", "y", "z"])
    assert viewer.parameters["multiselect_param"].value == ["y", "z"]
    assert viewer.parameters["multiselect_param"].options == ["w", "x", "y", "z"]

    # Integer Pair parameter
    viewer.add_integer_pair("int_pair_param", value=(1, 3), min_value=0, max_value=10)
    assert viewer.parameters["int_pair_param"].value == (1, 3)
    viewer.update_integer_pair("int_pair_param", value=(4, 6), min_value=-10, max_value=20)
    assert viewer.parameters["int_pair_param"].value == (4, 6)
    assert viewer.parameters["int_pair_param"].min_value == -10
    assert viewer.parameters["int_pair_param"].max_value == 20

    # Float Pair parameter
    viewer.add_float_pair("float_pair_param", value=(0.1, 0.3), min_value=0.0, max_value=1.0, step=0.1)
    assert viewer.parameters["float_pair_param"].value == (0.1, 0.3)
    viewer.update_float_pair("float_pair_param", value=(0.4, 0.6), min_value=-1.0, max_value=2.0, step=0.2)
    assert viewer.parameters["float_pair_param"].value == (0.4, 0.6)
    assert viewer.parameters["float_pair_param"].min_value == -1.0
    assert viewer.parameters["float_pair_param"].max_value == 2.0
    assert viewer.parameters["float_pair_param"].step == 0.2

    # Unbounded Integer parameter
    viewer.add_unbounded_integer("unbounded_int_param", value=5, min_value=None, max_value=None)
    assert viewer.parameters["unbounded_int_param"].value == 5
    viewer.update_unbounded_integer("unbounded_int_param", value=100, min_value=-10, max_value=None)
    assert viewer.parameters["unbounded_int_param"].value == 100
    assert viewer.parameters["unbounded_int_param"].min_value == -10
    assert viewer.parameters["unbounded_int_param"].max_value is None

    # Unbounded Float parameter
    viewer.add_unbounded_float("unbounded_float_param", value=0.5, min_value=None, max_value=None, step=0.1)
    assert viewer.parameters["unbounded_float_param"].value == 0.5
    viewer.update_unbounded_float("unbounded_float_param", value=10.5, min_value=0.0, max_value=None, step=0.5)
    assert viewer.parameters["unbounded_float_param"].value == 10.5
    assert viewer.parameters["unbounded_float_param"].min_value == 0.0
    assert viewer.parameters["unbounded_float_param"].max_value is None
    assert viewer.parameters["unbounded_float_param"].step == 0.5


def test_parameter_validation_bounds():
    viewer = MockViewer()

    # Test integer bounds validation
    viewer.add_integer("int_param", value=5, min_value=0, max_value=10)
    with pytest.raises(ValueError):
        viewer.update_integer("int_param", value=-1)
    with pytest.raises(ValueError):
        viewer.update_integer("int_param", value=11)

    # Test float bounds validation
    viewer.add_float("float_param", value=0.5, min_value=0.0, max_value=1.0)
    with pytest.raises(ValueError):
        viewer.update_float("float_param", value=-0.1)
    with pytest.raises(ValueError):
        viewer.update_float("float_param", value=1.1)

    # Test select validation
    viewer.add_selection("select_param", value="a", options=["a", "b", "c"])
    with pytest.raises(ValueError):
        viewer.update_selection("select_param", value="d")

    # Test multiselect validation
    viewer.add_multiple_selection("multiselect_param", value=["x"], options=["x", "y", "z"])
    with pytest.raises(ValueError):
        viewer.update_multiple_selection("multiselect_param", value=["w"])

    # Test integer pair bounds validation
    viewer.add_integer_pair("int_pair_param", value=(1, 3), min_value=0, max_value=10)
    with pytest.raises(ValueError):
        viewer.update_integer_pair("int_pair_param", value=(-1, 5))
    with pytest.raises(ValueError):
        viewer.update_integer_pair("int_pair_param", value=(5, 11))

    # Test float pair bounds validation
    viewer.add_float_pair("float_pair_param", value=(0.1, 0.3), min_value=0.0, max_value=1.0)
    with pytest.raises(ValueError):
        viewer.update_float_pair("float_pair_param", value=(-0.1, 0.5))
    with pytest.raises(ValueError):
        viewer.update_float_pair("float_pair_param", value=(0.5, 1.1))

    # Test unbounded integer validation
    viewer.add_unbounded_integer("unbounded_int_param", value=5, min_value=0, max_value=None)
    with pytest.raises(ValueError):
        viewer.update_unbounded_integer("unbounded_int_param", value=-1)  # Below minimum
    viewer.update_unbounded_integer("unbounded_int_param", value=1000)  # Should work (no upper bound)

    # Test unbounded float validation
    viewer.add_unbounded_float("unbounded_float_param", value=0.5, min_value=0.0, max_value=None)
    with pytest.raises(ValueError):
        viewer.update_unbounded_float("unbounded_float_param", value=-0.1)  # Below minimum
    viewer.update_unbounded_float("unbounded_float_param", value=1000.0)  # Should work (no upper bound)
