"""
Tests for the notebook deployment widgets.
"""

import pytest
from unittest.mock import Mock, patch
import ipywidgets as widgets

from syd.notebook_deployment.widgets import (
    create_widget,
    TextWidget,
    SelectionWidget,
    BooleanWidget,
    IntegerWidget,
    FloatWidget,
)


class TestWidgetCreation:
    """Tests for widget creation functionality."""

    def test_text_widget_creation(self, basic_parameters):
        """Test creation of text widget."""
        param = basic_parameters.parameters["text_param"]
        widget = create_widget(param)

        assert isinstance(widget, TextWidget)
        assert isinstance(widget.widget, widgets.Text)
        assert widget.value == "test"
        assert widget.widget.description == "text_param"

    def test_selection_widget_creation(self, basic_parameters):
        """Test creation of selection widget."""
        param = basic_parameters.parameters["select_param"]
        widget = create_widget(param)

        assert isinstance(widget, SelectionWidget)
        assert isinstance(widget.widget, widgets.Dropdown)
        assert widget.value == "A"
        assert list(widget.widget.options) == ["A", "B", "C"]

    def test_boolean_widget_creation(self, basic_parameters):
        """Test creation of boolean widget."""
        param = basic_parameters.parameters["bool_param"]
        widget = create_widget(param)

        assert isinstance(widget, BooleanWidget)
        assert isinstance(widget.widget, widgets.ToggleButton)
        assert widget.value is True

    def test_integer_widget_creation(self, basic_parameters):
        """Test creation of integer widget."""
        param = basic_parameters.parameters["int_param"]
        widget = create_widget(param)

        assert isinstance(widget, IntegerWidget)
        assert widget.value == 5
        assert widget.widget.min == 0
        assert widget.widget.max == 10

    def test_widget_creation_validation(self):
        """Test widget creation with invalid parameter."""
        with pytest.raises(ValueError):
            create_widget(Mock())


class TestWidgetEdgeCases:
    """Tests for widget edge cases."""

    def test_widget_with_long_description(self, basic_parameters):
        """Test widget with very long description."""
        mock_viewer = basic_parameters
        long_name = "x" * 50  # 50 character name
        mock_viewer.add_text(long_name, value="test")
        param = mock_viewer.parameters[long_name]
        widget = create_widget(param)

        assert isinstance(widget, TextWidget)
        assert widget.widget.description == long_name

    def test_widget_with_special_characters(self, basic_parameters):
        """Test widget with special characters in name."""
        mock_viewer = basic_parameters
        special_name = "test!@#$%^&*()"
        mock_viewer.add_text(special_name, value="test")
        param = mock_viewer.parameters[special_name]
        widget = create_widget(param)

        assert isinstance(widget, TextWidget)
        assert widget.widget.description == special_name


class TestWidgetUpdates:
    """Tests for widget update functionality."""

    def test_widget_value_update(self, basic_parameters):
        """Test updating widget value."""
        param = basic_parameters.parameters["text_param"]
        widget = create_widget(param)

        widget.value = "new value"
        assert widget.value == "new value"

        # Test update from parameter
        param.value = "param update"
        widget.update_from_parameter(param)
        assert widget.value == "param update"

    def test_selection_widget_options_update(self, basic_parameters):
        """Test updating selection widget options."""
        param = basic_parameters.parameters["select_param"]
        widget = create_widget(param)

        # Update options through parameter
        new_options = ["X", "Y", "Z"]
        param.update({"options": new_options, "value": "X"})
        widget.update_from_parameter(param)

        assert list(widget.widget.options) == new_options
        assert widget.value == "X"

    def test_parameter_validation_during_update(self, basic_parameters):
        """Test parameter validation during update."""
        param = basic_parameters.parameters["int_param"]
        widget = create_widget(param)

        # Test value clamping
        widget.value = 15  # Above max_value
        assert widget.value == 10  # Should be clamped to max_value

        widget.value = -5  # Below min_value
        assert widget.value == 0  # Should be clamped to min_value


class TestWidgetCallbacks:
    """Tests for widget callback functionality."""

    def test_widget_callback_registration(self, basic_parameters):
        """Test registering callbacks on widgets."""
        param = basic_parameters.parameters["int_param"]
        widget = create_widget(param)

        callback = Mock()
        widget.observe(callback)

        widget.value = 7
        callback.assert_called_once()

        # Verify callback is not called when value doesn't change
        callback.reset_mock()
        widget.value = 7
        callback.assert_not_called()

    def test_callback_disable_reenable(self, basic_parameters):
        """Test disabling and re-enabling callbacks."""
        param = basic_parameters.parameters["int_param"]
        widget = create_widget(param)

        callback = Mock()
        widget.observe(callback)

        widget.disable_callbacks()
        widget.value = 7
        callback.assert_not_called()

        widget.reenable_callbacks()
        widget.value = 8
        callback.assert_called_once()

    def test_multiple_callbacks(self, basic_parameters):
        """Test registering multiple callbacks."""
        param = basic_parameters.parameters["int_param"]
        widget = create_widget(param)

        callback1 = Mock()
        callback2 = Mock()
        widget.observe(callback1)
        widget.observe(callback2)

        widget.value = 7
        callback1.assert_called_once()
        callback2.assert_called_once()
