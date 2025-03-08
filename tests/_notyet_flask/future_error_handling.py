"""
Tests for the Flask deployment error handling.
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestFlaskErrorHandling:
    """Tests for Flask error handling."""

    def test_invalid_parameter_value(self, flask_client):
        """Test handling of invalid parameter values."""
        # Try to update int_param with a string
        response = flask_client.post(
            "/update/int_param",
            data=json.dumps({"value": "not an integer"}),
            content_type="application/json",
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    def test_missing_value_in_update(self, flask_client):
        """Test handling of missing value in update request."""
        # Try to update without providing a value
        response = flask_client.post(
            "/update/text_param", data=json.dumps({}), content_type="application/json"
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_json_in_update(self, flask_client):
        """Test handling of invalid JSON in update request."""
        # Try to update with invalid JSON
        response = flask_client.post(
            "/update/text_param", data="not valid json", content_type="application/json"
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_content_type(self, flask_client):
        """Test handling of invalid content type in update request."""
        # Try to update with wrong content type
        response = flask_client.post(
            "/update/text_param",
            data="value=test",
            content_type="application/x-www-form-urlencoded",
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_plot_format(self, flask_client):
        """Test handling of invalid plot format."""
        # Try to get plot with invalid format
        response = flask_client.get("/plot?format=invalid")

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_plot_dpi(self, flask_client):
        """Test handling of invalid plot dpi."""
        # Try to get plot with invalid dpi
        response = flask_client.get("/plot?dpi=invalid")

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data

    @patch("matplotlib.pyplot.savefig")
    def test_plot_generation_error(self, mock_savefig, flask_client):
        """Test handling of plot generation error."""
        # Make savefig raise an exception
        mock_savefig.side_effect = Exception("Plot error")

        # Try to get plot
        response = flask_client.get("/plot")

        # Should return 500 Internal Server Error
        assert response.status_code == 500

        # Response should contain error message
        data = json.loads(response.data)
        assert "error" in data
