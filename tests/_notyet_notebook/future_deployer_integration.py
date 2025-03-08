"""
Integration tests for the notebook deployer.
"""

import pytest
from unittest.mock import Mock, patch
import ipywidgets as widgets
from matplotlib.figure import Figure

from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


class TestNotebookDeployerIntegration:
    """Integration tests for NotebookDeployer."""

    @patch("IPython.display.display")
    def test_deploy_method(self, mock_display, basic_parameters):
        """Test the deploy method creates and displays the UI."""
        deployer = NotebookDeployer(basic_parameters)

        # Call deploy
        deployer.deploy()

        # Verify widgets were created
        assert len(deployer.parameter_widgets) == 4

        # Verify display was called
        mock_display.assert_called()

    @patch("matplotlib.pyplot.figure")
    def test_end_to_end_parameter_change(self, mock_figure, basic_parameters):
        """Test end-to-end flow from parameter change to plot update."""
        deployer = NotebookDeployer(basic_parameters)
        deployer._create_parameter_widgets()

        # Mock the output widget
        deployer.output_widget = Mock()

        # Simulate widget value change
        with patch.object(deployer, "_update_plot") as mock_update_plot:
            # Get the widget and change its value
            widget = deployer.parameter_widgets["int_param"]
            widget.value = 7

            # Verify update_plot was called
            mock_update_plot.assert_called_once()

            # Verify parameter was updated
            assert deployer.viewer.parameters["int_param"].value == 7

    @patch("matplotlib.pyplot.figure")
    def test_multiple_parameter_changes(self, mock_figure, basic_parameters):
        """Test multiple parameter changes in sequence."""
        deployer = NotebookDeployer(basic_parameters)
        deployer._create_parameter_widgets()

        # Mock the output widget
        deployer.output_widget = Mock()

        # Simulate multiple widget value changes
        with patch.object(deployer, "_update_plot") as mock_update_plot:
            # Change multiple widgets
            deployer.parameter_widgets["text_param"].value = "changed text"
            deployer.parameter_widgets["bool_param"].value = False
            deployer.parameter_widgets["select_param"].value = "B"

            # Verify update_plot was called for each change
            assert mock_update_plot.call_count == 3

            # Verify all parameters were updated
            assert deployer.viewer.parameters["text_param"].value == "changed text"
            assert deployer.viewer.parameters["bool_param"].value is False
            assert deployer.viewer.parameters["select_param"].value == "B"

    @patch("IPython.display.display")
    @patch("matplotlib.pyplot.figure")
    def test_continuous_update_mode(self, mock_figure, mock_display, basic_parameters):
        """Test continuous update mode."""
        # Create deployer with continuous update mode
        deployer = NotebookDeployer(basic_parameters, continuous_update=True)
        deployer._create_parameter_widgets()

        # Mock the output widget
        deployer.output_widget = Mock()

        # Verify widgets are set to continuous update mode
        for widget in deployer.parameter_widgets.values():
            if hasattr(widget.widget, "continuous_update"):
                assert widget.widget.continuous_update is True

    @patch("IPython.display.display")
    @patch("matplotlib.pyplot.figure")
    def test_non_continuous_update_mode(
        self, mock_figure, mock_display, basic_parameters
    ):
        """Test non-continuous update mode."""
        # Create deployer with non-continuous update mode
        deployer = NotebookDeployer(basic_parameters, continuous_update=False)
        deployer._create_parameter_widgets()

        # Mock the output widget
        deployer.output_widget = Mock()

        # Verify widgets are set to non-continuous update mode
        for widget in deployer.parameter_widgets.values():
            if hasattr(widget.widget, "continuous_update"):
                assert widget.widget.continuous_update is False

    @patch("IPython.display.display")
    def test_deploy_with_custom_layout(self, mock_display, basic_parameters):
        """Test deploy with custom layout configuration."""
        config = LayoutConfig(
            controls_position="right",
            figure_width=10.0,
            figure_height=8.0,
            controls_width_percent=40,
        )
        deployer = NotebookDeployer(basic_parameters, config)

        # Call deploy
        deployer.deploy()

        # Verify layout configuration was applied
        assert deployer.config.controls_position == "right"
        assert deployer.config.figure_width == 10.0
        assert deployer.config.figure_height == 8.0
        assert deployer.config.controls_width_percent == 40

        # Verify display was called
        mock_display.assert_called()
