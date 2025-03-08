"""
Tests for the notebook deployer plot updates and synchronization.
"""

import pytest
from unittest.mock import Mock, patch, call
import time

from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


class TestPlotUpdates:
    """Tests for plot update functionality."""

    @patch("matplotlib.pyplot.figure")
    @patch("IPython.display.display")
    def test_plot_update_mechanism(self, mock_display, mock_figure, notebook_deployer):
        """Test that plot updates correctly when parameters change."""
        deployer = notebook_deployer

        # Mock the output widget
        deployer.output_widget = Mock()

        # Call update plot
        deployer._update_plot()

        # Verify the viewer's plot method was called
        deployer.viewer.plot.assert_called_once()

        # Verify display was called with the figure
        deployer.output_widget.clear_output.assert_called_once()

    @patch("time.time")
    def test_debounce_functionality(self, mock_time, notebook_deployer):
        """Test that the debounce decorator works correctly."""
        # Set up time mock to return increasing values
        mock_time.side_effect = [0.0, 0.1, 0.2]

        deployer = notebook_deployer

        # Mock the update plot method
        deployer._update_plot = Mock()

        # Call the handler multiple times in quick succession
        deployer._handle_widget_engagement("text_param")
        deployer._handle_widget_engagement("bool_param")

        # Verify update_plot was only called once due to debouncing
        assert deployer._update_plot.call_count == 1

    @patch("time.time")
    def test_debounce_allows_after_wait(self, mock_time, notebook_deployer):
        """Test that debounce allows calls after wait time."""
        # Set up time mock to return values that exceed wait time
        mock_time.side_effect = [0.0, 1.0, 2.0]  # 1 second between calls

        deployer = notebook_deployer

        # Mock the update plot method
        deployer._update_plot = Mock()

        # Call the handler multiple times with sufficient time between
        deployer._handle_widget_engagement("text_param")
        deployer._handle_widget_engagement("bool_param")

        # Verify update_plot was called twice (once for each engagement)
        assert deployer._update_plot.call_count == 2


class TestWidgetStateSynchronization:
    """Tests for widget state synchronization."""

    def test_sync_widgets_with_state(self, notebook_deployer):
        """Test that widgets sync correctly with state."""
        deployer = notebook_deployer

        # Change a parameter value directly
        deployer.viewer.parameters["text_param"].value = "new value"

        # Call sync method
        deployer._sync_widgets_with_state()

        # Verify widget value was updated
        assert deployer.parameter_widgets["text_param"].value == "new value"

    def test_sync_widgets_with_exclude(self, notebook_deployer):
        """Test that sync excludes specified widgets."""
        deployer = notebook_deployer

        # Change parameter values directly
        deployer.viewer.parameters["text_param"].value = "new text"
        deployer.viewer.parameters["int_param"].value = 8

        # Call sync method with exclude
        deployer._sync_widgets_with_state(exclude="text_param")

        # Verify excluded widget wasn't updated but others were
        assert (
            deployer.parameter_widgets["text_param"].value == "test"
        )  # Original value
        assert deployer.parameter_widgets["int_param"].value == 8  # Updated value

    def test_sync_multiple_excludes(self, notebook_deployer):
        """Test sync with multiple excluded parameters."""
        deployer = notebook_deployer

        # Change all parameter values
        deployer.viewer.parameters["text_param"].value = "new text"
        deployer.viewer.parameters["bool_param"].value = False
        deployer.viewer.parameters["select_param"].value = "B"
        deployer.viewer.parameters["int_param"].value = 8

        # Call sync method with multiple excludes
        deployer._sync_widgets_with_state(exclude=["text_param", "bool_param"])

        # Verify excluded widgets weren't updated but others were
        assert deployer.parameter_widgets["text_param"].value == "test"  # Original
        assert deployer.parameter_widgets["bool_param"].value is True  # Original
        assert deployer.parameter_widgets["select_param"].value == "B"  # Updated
        assert deployer.parameter_widgets["int_param"].value == 8  # Updated


class TestParameterChangeHandling:
    """Tests for parameter change handling."""

    def test_handle_widget_engagement(self, notebook_deployer):
        """Test handling of widget engagement."""
        deployer = notebook_deployer

        # Mock the update plot method
        with patch.object(deployer, "_update_plot") as mock_update_plot:
            # Call the handler
            deployer._handle_widget_engagement("text_param")

            # Verify update_plot was called
            mock_update_plot.assert_called_once()

    def test_widget_to_parameter_sync(self, notebook_deployer):
        """Test that widget changes sync to parameters."""
        deployer = notebook_deployer

        # Change a widget value
        widget = deployer.parameter_widgets["text_param"]
        widget.value = "new widget value"

        # Verify parameter was updated
        assert deployer.viewer.parameters["text_param"].value == "new widget value"

    def test_parameter_to_widget_sync(self, notebook_deployer):
        """Test that parameter changes sync to widgets."""
        deployer = notebook_deployer

        # Change a parameter value
        deployer.viewer.parameters["text_param"].value = "new param value"

        # Call sync method
        deployer._sync_widgets_with_state()

        # Verify widget was updated
        assert deployer.parameter_widgets["text_param"].value == "new param value"
