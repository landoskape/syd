import pytest
from typing import Dict, Any, Optional, Tuple, List, Union
from syd.interactive_viewer import InteractiveViewer, _NoUpdate, _NO_UPDATE
from syd.parameters import ParameterType


class MockViewer(InteractiveViewer):
    """Simple concrete implementation for testing"""

    def plot(self, **kwargs):
        return None


def test_text_parameter():
    viewer = MockViewer()

    # Test adding with default value
    viewer.add_text("text1")
    assert "text1" in viewer.parameters
    assert viewer.parameters["text1"].value == ""

    # Test adding with specific value
    viewer.add_text("text2", value="hello")
    assert viewer.parameters["text2"].value == "hello"

    # Test updating value
    viewer.update_text("text1", value="updated")
    assert viewer.parameters["text1"].value == "updated"

    # Test partial update (no change)
    old_value = viewer.parameters["text1"].value
    viewer.update_text("text1")  # No value provided
    assert viewer.parameters["text1"].value == old_value


def test_selection_parameter():
    viewer = MockViewer()
    options = ["a", "b", "c"]

    # Test adding with default value (first option)
    viewer.add_selection("sel1", value="a", options=options)
    assert viewer.parameters["sel1"].value == "a"
    assert viewer.parameters["sel1"].options == options

    # Test adding with specific value
    viewer.add_selection("sel2", value="b", options=options)
    assert viewer.parameters["sel2"].value == "b"
    assert viewer.parameters["sel2"].options == options

    # Test updating value
    viewer.update_selection("sel1", value="c")
    assert viewer.parameters["sel1"].value == "c"
    assert viewer.parameters["sel1"].options == options

    # Test updating options
    new_options = ["x", "y", "z"]
    viewer.update_selection("sel1", options=new_options)
    assert viewer.parameters["sel1"].options == new_options

    # Test updating both
    viewer.update_selection("sel1", value="y", options=["w", "y", "z"])
    assert viewer.parameters["sel1"].value == "y"
    assert viewer.parameters["sel1"].options == ["w", "y", "z"]

    # Test invalid value
    with pytest.raises(ValueError):
        viewer.update_selection("sel1", value="invalid")


def test_multiple_selection_parameter():
    viewer = MockViewer()
    options = ["a", "b", "c"]

    # Test adding with default value (empty list)
    viewer.add_multiple_selection("multi1", options=options)
    assert viewer.parameters["multi1"].value == []
    assert viewer.parameters["multi1"].options == options

    # Test adding with specific value
    viewer.add_multiple_selection("multi2", value=["a", "b"], options=options)
    assert viewer.parameters["multi2"].value == ["a", "b"]
    assert viewer.parameters["multi2"].options == options

    # Test updating value
    viewer.update_multiple_selection("multi1", value=["c"])
    assert viewer.parameters["multi1"].value == ["c"]

    # Test updating options
    new_options = ["x", "y", "z"]
    viewer.update_multiple_selection("multi1", options=new_options)
    assert viewer.parameters["multi1"].options == new_options

    # Test invalid value
    with pytest.raises(ValueError):
        viewer.update_multiple_selection("multi1", value=["invalid"])


def test_boolean_parameter():
    viewer = MockViewer()

    # Test adding with default value
    viewer.add_boolean("bool1")
    assert viewer.parameters["bool1"].value is True

    # Test adding with specific value
    viewer.add_boolean("bool2", value=False)
    assert viewer.parameters["bool2"].value is False

    # Test updating value
    viewer.update_boolean("bool1", value=False)
    assert viewer.parameters["bool1"].value is False

    # Test partial update (no change)
    viewer.update_boolean("bool1")
    assert viewer.parameters["bool1"].value is False


def test_integer_parameter():
    viewer = MockViewer()

    # Test adding with default values
    viewer.add_integer("int1")
    assert viewer.parameters["int1"].value == 0
    assert viewer.parameters["int1"].min_value is None
    assert viewer.parameters["int1"].max_value is None

    # Test adding with specific values
    viewer.add_integer("int2", value=5, min_value=0, max_value=10)
    assert viewer.parameters["int2"].value == 5
    assert viewer.parameters["int2"].min_value == 0
    assert viewer.parameters["int2"].max_value == 10

    # Test updating value
    viewer.update_integer("int2", value=7)
    assert viewer.parameters["int2"].value == 7
    assert viewer.parameters["int2"].min_value == 0  # Unchanged

    # Test updating bounds
    viewer.update_integer("int2", min_value=-10, max_value=20)
    assert viewer.parameters["int2"].value == 7  # Unchanged
    assert viewer.parameters["int2"].min_value == -10
    assert viewer.parameters["int2"].max_value == 20

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_integer("int2", value=30)


def test_float_parameter():
    viewer = MockViewer()

    # Test adding with default values
    viewer.add_float("float1")
    assert viewer.parameters["float1"].value == 0.0
    assert viewer.parameters["float1"].min_value is None
    assert viewer.parameters["float1"].max_value is None
    assert viewer.parameters["float1"].step == 0.1

    # Test adding with specific values
    viewer.add_float("float2", value=5.5, min_value=0.0, max_value=10.0, step=0.5)
    assert viewer.parameters["float2"].value == 5.5
    assert viewer.parameters["float2"].min_value == 0.0
    assert viewer.parameters["float2"].max_value == 10.0
    assert viewer.parameters["float2"].step == 0.5

    # Test updating value
    viewer.update_float("float2", value=7.5)
    assert viewer.parameters["float2"].value == 7.5
    assert viewer.parameters["float2"].step == 0.5  # Unchanged

    # Test updating bounds and step
    viewer.update_float("float2", min_value=-10.0, max_value=20.0, step=0.2)
    assert viewer.parameters["float2"].value == 7.5  # Unchanged
    assert viewer.parameters["float2"].min_value == -10.0
    assert viewer.parameters["float2"].max_value == 20.0
    assert viewer.parameters["float2"].step == 0.2

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_float("float2", value=30.0)


def test_integer_pair_parameter():
    viewer = MockViewer()

    # Test adding with specific values
    viewer.add_integer_pair("pair1", value=(1, 3), min_value=0, max_value=10)
    assert viewer.parameters["pair1"].value == (1, 3)
    assert viewer.parameters["pair1"].min_value == 0
    assert viewer.parameters["pair1"].max_value == 10

    # Test updating value
    viewer.update_integer_pair("pair1", value=(4, 6))
    assert viewer.parameters["pair1"].value == (4, 6)
    assert viewer.parameters["pair1"].min_value == 0  # Unchanged

    # Test updating bounds
    viewer.update_integer_pair("pair1", min_value=-10, max_value=20)
    assert viewer.parameters["pair1"].value == (4, 6)  # Unchanged
    assert viewer.parameters["pair1"].min_value == -10
    assert viewer.parameters["pair1"].max_value == 20

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_integer_pair("pair1", value=(30, 40))

    # Test invalid value (first > second)
    with pytest.raises(ValueError):
        viewer.update_integer_pair("pair1", value=(6, 4))


def test_float_pair_parameter():
    viewer = MockViewer()

    # Test adding with specific values
    viewer.add_float_pair("pair1", value=(1.0, 3.0), min_value=0.0, max_value=10.0, step=0.5)
    assert viewer.parameters["pair1"].value == (1.0, 3.0)
    assert viewer.parameters["pair1"].min_value == 0.0
    assert viewer.parameters["pair1"].max_value == 10.0
    assert viewer.parameters["pair1"].step == 0.5

    # Test updating value
    viewer.update_float_pair("pair1", value=(4.0, 6.0))
    assert viewer.parameters["pair1"].value == (4.0, 6.0)
    assert viewer.parameters["pair1"].step == 0.5  # Unchanged

    # Test updating bounds and step
    viewer.update_float_pair("pair1", min_value=-10.0, max_value=20.0, step=0.2)
    assert viewer.parameters["pair1"].value == (4.0, 6.0)  # Unchanged
    assert viewer.parameters["pair1"].min_value == -10.0
    assert viewer.parameters["pair1"].max_value == 20.0
    assert viewer.parameters["pair1"].step == 0.2

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_float_pair("pair1", value=(30.0, 40.0))

    # Test invalid value (first > second)
    with pytest.raises(ValueError):
        viewer.update_float_pair("pair1", value=(6.0, 4.0))


def test_unbounded_integer_parameter():
    viewer = MockViewer()

    # Test adding with default values
    viewer.add_unbounded_integer("int1")
    assert viewer.parameters["int1"].value == 0
    assert viewer.parameters["int1"].min_value is None
    assert viewer.parameters["int1"].max_value is None

    # Test adding with specific values
    viewer.add_unbounded_integer("int2", value=5, min_value=0, max_value=10)
    assert viewer.parameters["int2"].value == 5
    assert viewer.parameters["int2"].min_value == 0
    assert viewer.parameters["int2"].max_value == 10

    # Test updating value
    viewer.update_unbounded_integer("int2", value=7)
    assert viewer.parameters["int2"].value == 7
    assert viewer.parameters["int2"].min_value == 0  # Unchanged

    # Test updating bounds
    viewer.update_unbounded_integer("int2", min_value=None, max_value=None)
    assert viewer.parameters["int2"].value == 7  # Unchanged
    assert viewer.parameters["int2"].min_value is None
    assert viewer.parameters["int2"].max_value is None

    # Test value with bounds
    viewer.update_unbounded_integer("int2", min_value=0, max_value=10)
    assert viewer.parameters["int2"].min_value == 0
    assert viewer.parameters["int2"].max_value == 10

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_unbounded_integer("int2", value=30)


def test_unbounded_float_parameter():
    viewer = MockViewer()

    # Test adding with default values
    viewer.add_unbounded_float("float1")
    assert viewer.parameters["float1"].value == 0.0
    assert viewer.parameters["float1"].min_value is None
    assert viewer.parameters["float1"].max_value is None
    assert viewer.parameters["float1"].step is None

    # Test adding with specific values
    viewer.add_unbounded_float("float2", value=5.5, min_value=0.0, max_value=10.0, step=0.5)
    assert viewer.parameters["float2"].value == 5.5
    assert viewer.parameters["float2"].min_value == 0.0
    assert viewer.parameters["float2"].max_value == 10.0
    assert viewer.parameters["float2"].step == 0.5

    # Test updating value
    viewer.update_unbounded_float("float2", value=7.5)
    assert viewer.parameters["float2"].value == 7.5
    assert viewer.parameters["float2"].step == 0.5  # Unchanged

    # Test updating bounds and step
    viewer.update_unbounded_float("float2", min_value=None, max_value=None, step=None)
    assert viewer.parameters["float2"].value == 7.5  # Unchanged
    assert viewer.parameters["float2"].min_value is None
    assert viewer.parameters["float2"].max_value is None
    assert viewer.parameters["float2"].step is None

    # Test value with bounds
    viewer.update_unbounded_float("float2", min_value=0.0, max_value=10.0, step=0.1)
    assert viewer.parameters["float2"].min_value == 0.0
    assert viewer.parameters["float2"].max_value == 10.0
    assert viewer.parameters["float2"].step == 0.1

    # Test invalid value (out of bounds)
    with pytest.raises(ValueError):
        viewer.update_unbounded_float("float2", value=30.0)


def test_invalid_parameter_operations():
    viewer = MockViewer()

    # Test updating non-existent parameter
    with pytest.raises(ValueError):
        viewer.update_text("nonexistent", value="test")

    # Test adding parameter while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_text("text1", value="test")

    # Test type mismatch in update
    viewer.add_text("text1", value="test")
    with pytest.raises(TypeError):
        viewer.update_integer("text1", value=5)
