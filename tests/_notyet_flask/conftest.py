"""
Common fixtures for flask deployment tests.
"""

import pytest
from unittest.mock import Mock, patch
import json
from flask import Flask
from matplotlib.figure import Figure

from syd.viewer import Viewer
from syd.flask_deployment.deployer import FlaskDeployer


@pytest.fixture
def basic_flask_viewer():
    """
    Create a basic viewer for testing Flask deployment.
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
def flask_deployer(basic_flask_viewer):
    """
    Create a FlaskDeployer instance.
    """
    deployer = FlaskDeployer(basic_flask_viewer)
    return deployer


@pytest.fixture
def flask_app(flask_deployer):
    """
    Create a Flask app for testing.
    """
    return flask_deployer.app


@pytest.fixture
def flask_client(flask_app):
    """
    Create a Flask test client.
    """
    with flask_app.test_client() as client:
        yield client
