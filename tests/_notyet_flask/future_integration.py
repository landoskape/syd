"""
Integration tests for the Flask deployment.
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestFlaskIntegration:
    """Integration tests for Flask deployment."""

    @patch("matplotlib.pyplot.savefig")
    def test_parameter_update_triggers_plot_update(
        self, mock_savefig, flask_client, basic_flask_viewer
    ):
        """Test that updating a parameter triggers a plot update."""
        # Get initial plot
        initial_response = flask_client.get("/plot")
        assert initial_response.status_code == 200

        # Update a parameter
        update_response = flask_client.post(
            "/update/int_param",
            data=json.dumps({"value": 8}),
            content_type="application/json",
        )
        assert update_response.status_code == 200

        # Get updated plot
        updated_response = flask_client.get("/plot")
        assert updated_response.status_code == 200

        # Verify savefig was called twice (once for each plot request)
        assert mock_savefig.call_count == 2

        # Verify parameter was updated
        assert basic_flask_viewer.parameters["int_param"].value == 8

    def test_multiple_parameter_updates(self, flask_client, basic_flask_viewer):
        """Test multiple parameter updates in sequence."""
        # Update multiple parameters
        flask_client.post(
            "/update/text_param",
            data=json.dumps({"value": "updated text"}),
            content_type="application/json",
        )

        flask_client.post(
            "/update/bool_param",
            data=json.dumps({"value": False}),
            content_type="application/json",
        )

        flask_client.post(
            "/update/select_param",
            data=json.dumps({"value": "B"}),
            content_type="application/json",
        )

        # Get the state and verify all updates were applied
        response = flask_client.get("/state")
        data = json.loads(response.data)

        assert data["text_param"] == "updated text"
        assert data["bool_param"] is False
        assert data["select_param"] == "B"

    def test_state_reflects_parameter_updates(self, flask_client, basic_flask_viewer):
        """Test that the state endpoint reflects parameter updates."""
        # Get initial state
        initial_response = flask_client.get("/state")
        initial_data = json.loads(initial_response.data)
        assert initial_data["int_param"] == 5

        # Update a parameter
        flask_client.post(
            "/update/int_param",
            data=json.dumps({"value": 8}),
            content_type="application/json",
        )

        # Get updated state
        updated_response = flask_client.get("/state")
        updated_data = json.loads(updated_response.data)

        # Verify state was updated
        assert updated_data["int_param"] == 8

    def test_full_workflow(self, flask_client, basic_flask_viewer):
        """Test the full workflow of the Flask deployment."""
        # 1. Get initial page
        index_response = flask_client.get("/")
        assert index_response.status_code == 200

        # 2. Get initial state
        state_response = flask_client.get("/state")
        initial_state = json.loads(state_response.data)

        # 3. Get initial plot
        with patch("matplotlib.pyplot.savefig") as mock_savefig:
            plot_response = flask_client.get("/plot")
            assert plot_response.status_code == 200
            assert mock_savefig.call_count == 1

        # 4. Update parameters
        flask_client.post(
            "/update/text_param",
            data=json.dumps({"value": "workflow test"}),
            content_type="application/json",
        )

        flask_client.post(
            "/update/int_param",
            data=json.dumps({"value": 7}),
            content_type="application/json",
        )

        # 5. Get updated state
        updated_state_response = flask_client.get("/state")
        updated_state = json.loads(updated_state_response.data)

        # Verify state was updated
        assert updated_state["text_param"] == "workflow test"
        assert updated_state["int_param"] == 7

        # 6. Get updated plot
        with patch("matplotlib.pyplot.savefig") as mock_savefig:
            updated_plot_response = flask_client.get("/plot")
            assert updated_plot_response.status_code == 200
            assert mock_savefig.call_count == 1

    @patch("matplotlib.pyplot.savefig")
    def test_plot_format_changes(self, mock_savefig, flask_client):
        """Test changing plot format."""
        # Get plot in different formats
        png_response = flask_client.get("/plot?format=png")
        assert png_response.status_code == 200
        assert png_response.mimetype == "image/png"

        svg_response = flask_client.get("/plot?format=svg")
        assert svg_response.status_code == 200
        assert svg_response.mimetype == "image/svg+xml"

        pdf_response = flask_client.get("/plot?format=pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.mimetype == "application/pdf"

        # Verify savefig was called for each format
        assert mock_savefig.call_count == 3
