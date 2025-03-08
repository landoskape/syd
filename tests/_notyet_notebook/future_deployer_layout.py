"""
Tests for the notebook deployer layout functionality.
"""

import pytest
from unittest.mock import Mock, patch
import ipywidgets as widgets

from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


class TestNotebookDeployerLayout:
    """Tests for NotebookDeployer layout functionality."""

    @patch("ipywidgets.HBox")
    @patch("ipywidgets.VBox")
    def test_horizontal_layout_creation(
        self, mock_vbox, mock_hbox, notebook_deployer_with_config
    ):
        """Test horizontal layout creation (left/right controls)."""
        # Set up a deployer with horizontal layout
        deployer = notebook_deployer_with_config
        deployer.config.controls_position = "left"
        deployer.config.is_horizontal = True

        # Call the method that creates the layout
        layout = deployer._create_layout()

        # Verify HBox was called for the main container (horizontal layout)
        mock_hbox.assert_called()

    @patch("ipywidgets.HBox")
    @patch("ipywidgets.VBox")
    def test_vertical_layout_creation(
        self, mock_vbox, mock_hbox, notebook_deployer_with_config
    ):
        """Test vertical layout creation (top/bottom controls)."""
        # Set up a deployer with vertical layout
        deployer = notebook_deployer_with_config
        deployer.config.controls_position = "top"
        deployer.config.is_horizontal = False

        # Call the method that creates the layout
        layout = deployer._create_layout()

        # Verify VBox was called for the main container (vertical layout)
        mock_vbox.assert_called()

    def test_controls_container_creation(self, notebook_deployer):
        """Test creation of controls container."""
        deployer = notebook_deployer

        # Call the method that creates the controls container
        controls = deployer._create_controls_container()

        # Verify it's a VBox containing all parameter widgets
        assert isinstance(controls, widgets.VBox)
        assert len(controls.children) == len(deployer.parameter_widgets)

    def test_left_layout_ordering(self, basic_parameters):
        """Test left layout places controls on the left."""
        config = LayoutConfig(controls_position="left")
        deployer = NotebookDeployer(basic_parameters, config)
        deployer._create_parameter_widgets()

        with patch("ipywidgets.HBox") as mock_hbox:
            mock_hbox.return_value = Mock()
            deployer._create_layout()

            # The first argument to HBox should be a list with controls first, then output
            args, _ = mock_hbox.call_args
            children = args[0]

            # First child should be controls (VBox), second should be output
            assert isinstance(children[0], widgets.VBox)  # Controls container
            assert children[1] == deployer.output_widget  # Output widget

    def test_right_layout_ordering(self, basic_parameters):
        """Test right layout places controls on the right."""
        config = LayoutConfig(controls_position="right")
        deployer = NotebookDeployer(basic_parameters, config)
        deployer._create_parameter_widgets()

        with patch("ipywidgets.HBox") as mock_hbox:
            mock_hbox.return_value = Mock()
            deployer._create_layout()

            # The first argument to HBox should be a list with output first, then controls
            args, _ = mock_hbox.call_args
            children = args[0]

            # First child should be output, second should be controls (VBox)
            assert children[0] == deployer.output_widget  # Output widget
            assert isinstance(children[1], widgets.VBox)  # Controls container

    def test_top_layout_ordering(self, basic_parameters):
        """Test top layout places controls on top."""
        config = LayoutConfig(controls_position="top")
        deployer = NotebookDeployer(basic_parameters, config)
        deployer._create_parameter_widgets()

        with patch("ipywidgets.VBox") as mock_vbox:
            mock_vbox.return_value = Mock()
            deployer._create_layout()

            # The first argument to VBox should be a list with controls first, then output
            args, _ = mock_vbox.call_args
            children = args[0]

            # First child should be controls (VBox), second should be output
            assert isinstance(children[0], widgets.VBox)  # Controls container
            assert children[1] == deployer.output_widget  # Output widget

    def test_bottom_layout_ordering(self, basic_parameters):
        """Test bottom layout places controls on bottom."""
        config = LayoutConfig(controls_position="bottom")
        deployer = NotebookDeployer(basic_parameters, config)
        deployer._create_parameter_widgets()

        with patch("ipywidgets.VBox") as mock_vbox:
            mock_vbox.return_value = Mock()
            deployer._create_layout()

            # The first argument to VBox should be a list with output first, then controls
            args, _ = mock_vbox.call_args
            children = args[0]

            # First child should be output, second should be controls (VBox)
            assert children[0] == deployer.output_widget  # Output widget
            assert isinstance(children[1], widgets.VBox)  # Controls container
