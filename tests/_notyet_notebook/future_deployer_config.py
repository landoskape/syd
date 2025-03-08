"""
Tests for the notebook deployer configuration.
"""

import pytest
from unittest.mock import Mock, patch

from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


class TestLayoutConfig:
    """Tests for the LayoutConfig class."""

    def test_valid_layout_configs(self):
        """Test valid layout configurations."""
        # Test valid configurations
        config = LayoutConfig(controls_position="left")
        assert config.is_horizontal is True

        config = LayoutConfig(controls_position="right")
        assert config.is_horizontal is True

        config = LayoutConfig(controls_position="top")
        assert config.is_horizontal is False

        config = LayoutConfig(controls_position="bottom")
        assert config.is_horizontal is False

    def test_invalid_layout_config(self):
        """Test invalid layout configuration."""
        # Test invalid configuration
        with pytest.raises(ValueError):
            LayoutConfig(controls_position="invalid")

    def test_default_values(self):
        """Test default values for LayoutConfig."""
        config = LayoutConfig()
        assert config.controls_position == "left"
        assert config.figure_width == 8.0
        assert config.figure_height == 6.0
        assert config.controls_width_percent == 30
        assert config.is_horizontal is True


class TestDeployerInitialization:
    """Tests for NotebookDeployer initialization."""

    def test_deployer_initialization_with_config(self, basic_parameters):
        """Test initialization with explicit config object."""
        deployer = NotebookDeployer(
            basic_parameters,
            controls_position="right",
            figure_width=10.0,
            figure_height=8.0,
            controls_width_percent=40,
        )

        assert deployer.config.controls_position == "right"
        assert deployer.config.figure_width == 10.0
        assert deployer.config.figure_height == 8.0
        assert deployer.config.controls_width_percent == 40
        assert deployer.config.is_horizontal is True

    def test_deployer_initialization_with_kwargs(self, basic_parameters):
        """Test initialization with kwargs instead of config."""
        deployer = NotebookDeployer(
            basic_parameters,
            controls_position="bottom",
            figure_width=12.0,
            figure_height=9.0,
            controls_width_percent=25,
        )

        assert deployer.config.controls_position == "bottom"
        assert deployer.config.figure_width == 12.0
        assert deployer.config.figure_height == 9.0
        assert deployer.config.controls_width_percent == 25
        assert deployer.config.is_horizontal is False

    def test_deployer_initialization_with_defaults(self, basic_parameters):
        """Test initialization with default configuration."""
        deployer = NotebookDeployer(basic_parameters)

        assert deployer.config.controls_position == "left"
        assert deployer.config.figure_width == 8.0
        assert deployer.config.figure_height == 6.0
        assert deployer.config.controls_width_percent == 30
        assert deployer.config.is_horizontal is True
