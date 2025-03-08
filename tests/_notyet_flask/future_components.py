"""
Tests for the Flask deployment components.
"""

import pytest
from unittest.mock import Mock, patch

from syd.flask_deployment.deployer import create_component


class TestFlaskComponents:
    """Tests for Flask component creation."""

    def test_text_component_creation(self, basic_flask_viewer):
        """Test creation of text component."""
        param = basic_flask_viewer.parameters["text_param"]
        component = create_component(param)

        # Verify HTML contains the parameter name and value
        assert "text_param" in component.html
        assert "test" in component.html
        assert 'type="text"' in component.html

    def test_boolean_component_creation(self, basic_flask_viewer):
        """Test creation of boolean component."""
        param = basic_flask_viewer.parameters["bool_param"]
        component = create_component(param)

        # Verify HTML contains the parameter name and checked state
        assert "bool_param" in component.html
        assert 'type="checkbox"' in component.html
        assert "checked" in component.html

    def test_selection_component_creation(self, basic_flask_viewer):
        """Test creation of selection component."""
        param = basic_flask_viewer.parameters["select_param"]
        component = create_component(param)

        # Verify HTML contains the parameter name and options
        assert "select_param" in component.html
        assert "<select" in component.html
        assert ">A<" in component.html
        assert ">B<" in component.html
        assert ">C<" in component.html
        assert "selected" in component.html

    def test_integer_component_creation(self, basic_flask_viewer):
        """Test creation of integer component."""
        param = basic_flask_viewer.parameters["int_param"]
        component = create_component(param)

        # Verify HTML contains the parameter name and value
        assert "int_param" in component.html
        assert 'type="number"' in component.html
        assert 'value="5"' in component.html
        assert 'min="0"' in component.html
        assert 'max="10"' in component.html

    def test_component_creation_validation(self):
        """Test component creation with invalid parameter."""
        with pytest.raises(ValueError):
            create_component(Mock())


class TestComponentEdgeCases:
    """Tests for component edge cases."""

    def test_component_with_empty_options(self, basic_flask_viewer):
        """Test selection component with empty options."""
        basic_flask_viewer.add_selection("empty_select", value=None, options=[])
        param = basic_flask_viewer.parameters["empty_select"]
        component = create_component(param)

        # Verify HTML contains the parameter name but no options
        assert "empty_select" in component.html
        assert "<select" in component.html
        assert "selected" not in component.html  # No selected option

    def test_component_with_long_description(self, basic_flask_viewer):
        """Test component with very long description."""
        long_name = "x" * 50  # 50 character name
        basic_flask_viewer.add_text(long_name, value="test")
        param = basic_flask_viewer.parameters[long_name]
        component = create_component(param)

        # Verify HTML contains the long parameter name
        assert long_name in component.html

    def test_component_with_special_characters(self, basic_flask_viewer):
        """Test component with special characters in name."""
        special_name = "test!@#$%^&*()"
        basic_flask_viewer.add_text(special_name, value="test")
        param = basic_flask_viewer.parameters[special_name]
        component = create_component(param)

        # Verify HTML contains the special parameter name (possibly escaped)
        assert (
            special_name in component.html
            or special_name.replace("&", "&amp;") in component.html
        )


class TestComponentUpdates:
    """Tests for component update functionality."""

    def test_component_value_update(self, basic_flask_viewer):
        """Test updating component value."""
        param = basic_flask_viewer.parameters["text_param"]
        component = create_component(param)

        # Update parameter value
        param.value = "new value"
        component.update_from_parameter(param)

        # Verify HTML reflects the new value
        assert "new value" in component.html

    def test_selection_component_options_update(self, basic_flask_viewer):
        """Test updating selection component options."""
        param = basic_flask_viewer.parameters["select_param"]
        component = create_component(param)

        # Update options through parameter
        new_options = ["X", "Y", "Z"]
        param.update({"options": new_options, "value": "X"})
        component.update_from_parameter(param)

        # Verify HTML contains the new options
        assert ">X<" in component.html
        assert ">Y<" in component.html
        assert ">Z<" in component.html
        assert ">A<" not in component.html  # Old option should be gone

    def test_boolean_component_update(self, basic_flask_viewer):
        """Test updating boolean component."""
        param = basic_flask_viewer.parameters["bool_param"]
        component = create_component(param)

        # Initially should be checked
        assert "checked" in component.html

        # Update to false
        param.value = False
        component.update_from_parameter(param)

        # Should no longer be checked
        assert "checked" not in component.html
