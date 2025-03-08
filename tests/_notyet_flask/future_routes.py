"""
Tests for the Flask deployment routes.
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestFlaskRoutes:
    """Tests for Flask routes."""

    def test_index_route(self, flask_client):
        """Test the main index route returns 200 and contains expected HTML."""
        response = flask_client.get("/")

        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data
        assert b"text_param" in response.data
        assert b"bool_param" in response.data
        assert b"select_param" in response.data
        assert b"int_param" in response.data

    def test_state_route(self, flask_client, basic_flask_viewer):
        """Test the state route returns the current state as JSON."""
        response = flask_client.get("/state")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify state contains all parameters with correct values
        assert data["text_param"] == "test"
        assert data["bool_param"] is True
        assert data["select_param"] == "A"
        assert data["int_param"] == 5

    def test_update_route_text(self, flask_client, basic_flask_viewer):
        """Test the update route correctly updates text parameter values."""
        # Update a text parameter
        response = flask_client.post(
            "/update/text_param",
            data=json.dumps({"value": "new value"}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify parameter was updated in the viewer
        assert basic_flask_viewer.parameters["text_param"].value == "new value"

    def test_update_route_boolean(self, flask_client, basic_flask_viewer):
        """Test the update route correctly updates boolean parameter values."""
        # Update a boolean parameter
        response = flask_client.post(
            "/update/bool_param",
            data=json.dumps({"value": False}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify parameter was updated in the viewer
        assert basic_flask_viewer.parameters["bool_param"].value is False

    def test_update_route_selection(self, flask_client, basic_flask_viewer):
        """Test the update route correctly updates selection parameter values."""
        # Update a selection parameter
        response = flask_client.post(
            "/update/select_param",
            data=json.dumps({"value": "B"}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify parameter was updated in the viewer
        assert basic_flask_viewer.parameters["select_param"].value == "B"

    def test_update_route_integer(self, flask_client, basic_flask_viewer):
        """Test the update route correctly updates integer parameter values."""
        # Update an integer parameter
        response = flask_client.post(
            "/update/int_param",
            data=json.dumps({"value": 8}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify parameter was updated in the viewer
        assert basic_flask_viewer.parameters["int_param"].value == 8

    def test_update_nonexistent_parameter(self, flask_client):
        """Test the update route handles nonexistent parameters."""
        # Try to update a nonexistent parameter
        response = flask_client.post(
            "/update/nonexistent",
            data=json.dumps({"value": "test"}),
            content_type="application/json",
        )

        # Should return 404 Not Found
        assert response.status_code == 404

    @patch("matplotlib.pyplot.savefig")
    def test_plot_route(self, mock_savefig, flask_client):
        """Test the plot route returns a plot image."""
        response = flask_client.get("/plot")

        assert response.status_code == 200
        assert response.mimetype == "image/png"

        # Verify savefig was called
        mock_savefig.assert_called()

    def test_plot_route_with_format(self, flask_client):
        """Test the plot route with different format parameters."""
        # Test with svg format
        response = flask_client.get("/plot?format=svg")

        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"

        # Test with pdf format
        response = flask_client.get("/plot?format=pdf")

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"

    def test_plot_route_with_dpi(self, flask_client):
        """Test the plot route with dpi parameter."""
        response = flask_client.get("/plot?dpi=200")

        assert response.status_code == 200
        assert response.mimetype == "image/png"
