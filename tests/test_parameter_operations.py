import pytest
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from syd.parameters import ParameterAddError, ParameterUpdateError, ParameterType
from tests.support import MockViewer


def test_text_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_text(123, value="hello")

    with pytest.raises(ParameterUpdateError):
        viewer.update_text(123, value="hello")

    # Test basic add and update
    viewer.add_text("text_1", value="hello")
    assert viewer.parameters["text_1"].value == "hello"

    viewer.update_text("text_1", value="world")
    assert viewer.parameters["text_1"].value == "world"

    # Test adding duplicate parameter
    with pytest.raises(ParameterAddError):
        viewer.add_text("text_1", value="hello")

    # Test adding while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_text("text_deployed", value="hello")

    # Test updating non-existent parameter
    with pytest.raises(ParameterUpdateError):
        viewer.update_text("text_doesnt_exist", value="hello")

    # Test type conversion on add
    viewer.add_text("text_convert", value=123)
    assert viewer.parameters["text_convert"].value == "123"

    viewer.add_text("text_convert_float", value=456.789)
    assert viewer.parameters["text_convert_float"].value == "456.789"

    # Test type conversion on update
    viewer.update_text("text_convert", value=789)
    assert viewer.parameters["text_convert"].value == "789"

    # Test empty update does nothing
    old_value = viewer.parameters["text_1"].value
    viewer.update_text("text_1")
    assert viewer.parameters["text_1"].value == old_value


def test_boolean_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_boolean(123, value=True)

    with pytest.raises(ParameterUpdateError):
        viewer.update_boolean(123, value=True)

    # Test basic add and update
    viewer.add_boolean("bool_1", value=True)
    assert viewer.parameters["bool_1"].value is True

    viewer.update_boolean("bool_1", value=False)
    assert viewer.parameters["bool_1"].value is False

    # Test adding duplicate parameter
    with pytest.raises(ParameterAddError):
        viewer.add_boolean("bool_1", value=True)

    # Test adding while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_boolean("bool_deployed", value=True)

    # Test updating non-existent parameter
    with pytest.raises(ParameterUpdateError):
        viewer.update_boolean("bool_doesnt_exist", value=True)

    # Test type conversion on add
    viewer.add_boolean("bool_convert_1", value=1)
    assert viewer.parameters["bool_convert_1"].value is True

    viewer.add_boolean("bool_convert_2", value=0)
    assert viewer.parameters["bool_convert_2"].value is False

    viewer.add_boolean("bool_convert_3", value="hello")
    assert viewer.parameters["bool_convert_3"].value is True

    viewer.add_boolean("bool_convert_4", value=[])
    assert viewer.parameters["bool_convert_4"].value is False

    # Test type conversion on update
    viewer.update_boolean("bool_convert_1", value=0)
    assert viewer.parameters["bool_convert_1"].value is False

    # Test empty update does nothing
    old_value = viewer.parameters["bool_1"].value
    viewer.update_boolean("bool_1")
    assert viewer.parameters["bool_1"].value == old_value


def test_selection_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_selection(123, value="a", options=["a", "b", "c"])

    with pytest.raises(ParameterUpdateError):
        viewer.update_selection(123, value="a", options=["a", "b", "c"])

    # Test basic add and update
    viewer.add_selection("selection_1", value="a", options=["a", "b", "c"])
    assert viewer.parameters["selection_1"].value == "a"

    viewer.update_selection("selection_1", value="b")
    assert viewer.parameters["selection_1"].value == "b"

    new_options = ["a", "b", "c", "d"]
    viewer.update_selection("selection_1", options=new_options)
    assert viewer.parameters["selection_1"].options == new_options
    assert viewer.parameters["selection_1"].value == "b"

    # Test that disjoint options convert the value to the first option
    disjoint_options = ["x", "y", "z"]
    with pytest.warns(UserWarning):
        viewer.update_selection("selection_1", options=disjoint_options)
    assert viewer.parameters["selection_1"].options == disjoint_options
    assert viewer.parameters["selection_1"].value == "x"

    # Test that you can convert the value to any other than the first option in disjoint options
    disjoint_options = ["xx", "yy", "zz"]
    viewer.update_selection("selection_1", options=disjoint_options, value="yy")
    assert viewer.parameters["selection_1"].options == disjoint_options
    assert viewer.parameters["selection_1"].value == "yy"

    # Test adding duplicate parameter
    with pytest.raises(ParameterAddError):
        viewer.add_selection("selection_1", value="a", options=["a", "b", "c"])

    # Test adding while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_selection("selection_deployed", value="a", options=["a", "b", "c"])

    # Test updating non-existent parameter
    with pytest.raises(ParameterUpdateError):
        viewer.update_selection("selection_doesnt_exist", value="a", options=["a", "b", "c"])

    # Test empty update does nothing
    old_value = viewer.parameters["selection_1"].value
    old_options = viewer.parameters["selection_1"].options
    viewer.update_selection("selection_1")
    assert viewer.parameters["selection_1"].value == old_value
    assert viewer.parameters["selection_1"].options == old_options

    # Test that failed update does nothing
    with pytest.raises(ParameterUpdateError):
        viewer.update_selection("selection_1", value="d", options=["a", "b", "c"])
    assert viewer.parameters["selection_1"].value == old_value
    assert viewer.parameters["selection_1"].options == old_options

    # Test that options need to be lists
    with pytest.raises(ParameterAddError):
        viewer.add_selection("selection_add_error", value="a", options=1)
    with pytest.raises(ParameterUpdateError):
        viewer.update_selection("selection_1", value="a", options=1)
    assert viewer.parameters["selection_1"].value == old_value
    assert viewer.parameters["selection_1"].options == old_options


def test_multiple_selection_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_multiple_selection(123, value=["a"], options=["a", "b", "c"])

    with pytest.raises(ParameterUpdateError):
        viewer.update_multiple_selection(123, value=["a"], options=["a", "b", "c"])

    # Test basic add and update
    viewer.add_multiple_selection("multiple_selection_1", value=["a"], options=["a", "b", "c"])
    assert viewer.parameters["multiple_selection_1"].value == ["a"]

    viewer.add_multiple_selection("multiple_selection_2", value=["b", "c"], options=["a", "b", "c"])
    assert viewer.parameters["multiple_selection_2"].value == ["b", "c"]

    viewer.update_multiple_selection("multiple_selection_1", value=["b"])
    assert viewer.parameters["multiple_selection_1"].value == ["b"]

    viewer.update_multiple_selection("multiple_selection_1", value=[])
    assert viewer.parameters["multiple_selection_1"].value == []

    viewer.update_multiple_selection("multiple_selection_1", value=["a", "b"])
    assert viewer.parameters["multiple_selection_1"].value == ["a", "b"]

    new_options = ["a", "b", "c", "d"]
    viewer.update_multiple_selection("multiple_selection_1", options=new_options)
    assert viewer.parameters["multiple_selection_1"].options == new_options
    assert viewer.parameters["multiple_selection_1"].value == ["a", "b"]

    # Test that disjoint options convert the value to an empty list
    disjoint_options = ["x", "y", "z"]
    with pytest.warns(UserWarning):
        viewer.update_multiple_selection("multiple_selection_1", options=disjoint_options)
    assert viewer.parameters["multiple_selection_1"].options == disjoint_options
    assert viewer.parameters["multiple_selection_1"].value == []

    # Test that you can convert the value to any other than the first option in disjoint options
    disjoint_options = ["xx", "yy", "zz"]
    viewer.update_multiple_selection("multiple_selection_1", options=disjoint_options, value=["yy"])
    assert viewer.parameters["multiple_selection_1"].options == disjoint_options
    assert viewer.parameters["multiple_selection_1"].value == ["yy"]

    # Test adding duplicate parameter
    with pytest.raises(ParameterAddError):
        viewer.add_multiple_selection("multiple_selection_1", value=["a"], options=["a", "b", "c"])

    # Test adding while deployed
    with pytest.raises(RuntimeError):
        with viewer.deploy_app():
            viewer.add_multiple_selection("multiple_selection_deployed", value=["a"], options=["a", "b", "c"])

    # Test updating non-existent parameter
    with pytest.raises(ParameterUpdateError):
        viewer.update_multiple_selection("multiple_selection_doesnt_exist", value=["a"], options=["a", "b", "c"])

    # Test empty update does nothing
    old_value = viewer.parameters["multiple_selection_1"].value
    old_options = viewer.parameters["multiple_selection_1"].options
    viewer.update_multiple_selection("multiple_selection_1")
    assert viewer.parameters["multiple_selection_1"].value == old_value
    assert viewer.parameters["multiple_selection_1"].options == old_options

    # Test that failed update does nothing
    with pytest.raises(ParameterUpdateError):
        viewer.update_multiple_selection("multiple_selection_1", value=["d"], options=["a", "b", "c"])
    assert viewer.parameters["multiple_selection_1"].value == old_value
    assert viewer.parameters["multiple_selection_1"].options == old_options

    # Test that values need to be lists
    with pytest.raises(ParameterUpdateError):
        viewer.update_multiple_selection("multiple_selection_1", value="a")
    assert viewer.parameters["multiple_selection_1"].value == old_value
    assert viewer.parameters["multiple_selection_1"].options == old_options

    # Test that values need to be strings
    viewer.update_multiple_selection("multiple_selection_1", value=[1, "b"], options=[1, "b", "c"])
    assert viewer.parameters["multiple_selection_1"].value == [1, "b"]

    # Test that options need to be lists
    with pytest.raises(ParameterAddError):
        viewer.add_multiple_selection("multiple_selection_1", value=["a"], options=1)
    with pytest.raises(ParameterUpdateError):
        viewer.update_multiple_selection("multiple_selection_1", options=1)
    assert viewer.parameters["multiple_selection_1"].value == [1, "b"]


def test_integer_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_integer(123, value=1)
    with pytest.raises(ParameterUpdateError):
        viewer.update_integer(123, value=1)

    # Test basic add and update
    viewer.add_integer("integer_1", value=1, min_value=0, max_value=10)
    assert viewer.parameters["integer_1"].value == 1

    viewer.update_integer("integer_1", value=2)
    assert viewer.parameters["integer_1"].value == 2

    # Test type conversion on update
    viewer.update_integer("integer_1", value="10")
    assert viewer.parameters["integer_1"].value == 10

    # Test that value clamps to min/max
    with pytest.warns(UserWarning):
        viewer.add_integer("integer_clamp_down", value=100, min_value=0, max_value=10)
    with pytest.warns(UserWarning):
        viewer.add_integer("integer_clamp_up", value=-100, min_value=0, max_value=10)
    with pytest.warns(UserWarning):
        viewer.update_integer("integer_1", value=100)
    assert viewer.parameters["integer_1"].value == 10

    with pytest.warns(UserWarning):
        viewer.update_integer("integer_1", value=-100)
    assert viewer.parameters["integer_1"].value == 0

    # Test type conversion on update
    viewer.add_integer("integer_2", value="5", min_value=0, max_value=10)
    assert viewer.parameters["integer_2"].value == 5

    # Test that invalid conversion fails add/update and does nothing
    with pytest.raises(ParameterAddError):
        viewer.add_integer("integer_3", value="invalid", min_value=0, max_value=10)
    assert "integer_3" not in viewer.parameters

    with pytest.raises(ParameterUpdateError):
        viewer.update_integer("integer_2", value="invalid")
    assert viewer.parameters["integer_2"].value == 5

    # Test that empty update does nothing
    old_value = viewer.parameters["integer_2"].value
    old_min_value = viewer.parameters["integer_2"].min_value
    old_max_value = viewer.parameters["integer_2"].max_value
    viewer.update_integer("integer_2")
    assert viewer.parameters["integer_2"].value == old_value
    assert viewer.parameters["integer_2"].min_value == old_min_value
    assert viewer.parameters["integer_2"].max_value == old_max_value

    # Test that failed update does nothing
    with pytest.raises(ParameterUpdateError):
        viewer.update_integer("integer_2", value="hello")
    assert viewer.parameters["integer_2"].value == old_value
    assert viewer.parameters["integer_2"].min_value == old_min_value
    assert viewer.parameters["integer_2"].max_value == old_max_value


def test_float_parameter_operations():
    viewer = MockViewer()

    # Test invalid parameter name
    with pytest.raises(ParameterAddError):
        viewer.add_float(123, value=1)
    with pytest.raises(ParameterUpdateError):
        viewer.update_float(123, value=1)

    # Test basic add and update
    viewer.add_float("float_1", value=1.5, min_value=0, max_value=10, step=1.0)
    assert viewer.parameters["float_1"].value == 1.5

    viewer.update_float("float_1", value=2.5)
    assert viewer.parameters["float_1"].value == 2.5

    # Test type conversion on update
    viewer.update_float("float_1", value="10")
    assert viewer.parameters["float_1"].value == 10

    # Test that value clamps to min/max
    with pytest.warns(UserWarning):
        viewer.add_float("float_clamp_down", value=100, min_value=0, max_value=10)
    with pytest.warns(UserWarning):
        viewer.add_float("float_clamp_up", value=-100, min_value=0, max_value=10)
    with pytest.warns(UserWarning):
        viewer.update_float("float_1", value=100)
    assert viewer.parameters["float_1"].value == 10

    with pytest.warns(UserWarning):
        viewer.update_float("float_1", value=-100)
    assert viewer.parameters["float_1"].value == 0

    # Test type conversion on update
    viewer.add_float("float_2", value="5", min_value=0, max_value=10)
    assert viewer.parameters["float_2"].value == 5

    # Test that invalid conversion fails add/update and does nothing
    with pytest.raises(ParameterAddError):
        viewer.add_float("float_3", value="invalid", min_value=0, max_value=10)
    assert "float_3" not in viewer.parameters

    with pytest.raises(ParameterUpdateError):
        viewer.update_float("float_2", value="invalid")
    assert viewer.parameters["float_2"].value == 5

    # Test that empty update does nothing
    old_value = viewer.parameters["float_2"].value
    old_min_value = viewer.parameters["float_2"].min_value
    old_max_value = viewer.parameters["float_2"].max_value
    viewer.update_float("float_2")
    assert viewer.parameters["float_2"].value == old_value
    assert viewer.parameters["float_2"].min_value == old_min_value
    assert viewer.parameters["float_2"].max_value == old_max_value

    # Test that failed update does nothing
    with pytest.raises(ParameterUpdateError):
        viewer.update_float("float_2", value="hello")
    assert viewer.parameters["float_2"].value == old_value
    assert viewer.parameters["float_2"].min_value == old_min_value
    assert viewer.parameters["float_2"].max_value == old_max_value
