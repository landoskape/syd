"""
Common fixtures for notebook deployment tests.
"""

import pytest
from unittest.mock import Mock, patch
import ipywidgets as widgets
from matplotlib.figure import Figure

from syd.viewer import Viewer
from syd.notebook_deployment.widgets import (
    create_widget,
    TextWidget,
    SelectionWidget,
    BooleanWidget,
)
from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


@pytest.fixture
def basic_parameters():
    """
    Create a basic viewer with test parameters for testing.
    """

    class TestViewer(Viewer):
        def plot(self, state) -> Figure:
            # Return a mock figure
            return Mock(spec=Figure)

    mock_viewer = TestViewer()
    # Add test parameters using keyword arguments
    mock_viewer.add_text("text_param", value="test")
    mock_viewer.add_boolean("bool_param", value=True)
    mock_viewer.add_selection("select_param", value="A", options=["A", "B", "C"])
    mock_viewer.add_integer("int_param", value=5, min_value=0, max_value=10)
    return mock_viewer


@pytest.fixture
def notebook_deployer(basic_parameters):
    """
    Create a NotebookDeployer instance with default configuration.
    """
    deployer = NotebookDeployer(basic_parameters)
    deployer._create_parameter_widgets()
    return deployer


@pytest.fixture
def notebook_deployer_with_config(basic_parameters):
    """
    Create a NotebookDeployer instance with custom configuration.
    """
    config = LayoutConfig(
        controls_position="right",
        figure_width=10.0,
        figure_height=8.0,
        controls_width_percent=40,
    )
    deployer = NotebookDeployer(basic_parameters, config)
    deployer._create_parameter_widgets()
    return deployer
