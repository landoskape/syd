# SYD Testing Suite

This directory contains tests for the SYD package, including specialized tests for the GUI deployment modules.

## Test Organization

The tests are organized into the following directories:

- `tests/`: Root directory containing tests for core functionality
  - `test_notebook/`: Tests for the notebook deployment module
  - `test_flask/`: Tests for the flask deployment module

## Notebook Deployment Tests

The notebook deployment tests are organized into the following files:

- `test_widgets.py`: Tests for widget creation, updates, and callbacks
- `test_deployer_config.py`: Tests for deployer configuration
- `test_deployer_layout.py`: Tests for layout creation and positioning
- `test_deployer_updates.py`: Tests for plot updates and synchronization
- `test_deployer_integration.py`: Integration tests for the notebook deployer

## Flask Deployment Tests

The flask deployment tests are organized into the following files:

- `test_components.py`: Tests for component creation and updates
- `test_routes.py`: Tests for Flask routes
- `test_error_handling.py`: Tests for error handling
- `test_integration.py`: Integration tests for the Flask deployment

## Running the Tests

To run all tests:

```bash
pytest
```

To run only the notebook deployment tests:

```bash
pytest tests/test_notebook
```

To run only the flask deployment tests:

```bash
pytest tests/test_flask
```

To run a specific test file:

```bash
pytest tests/test_notebook/test_widgets.py
```

## Testing Approach

### Mocking Strategy

Since both the notebook and Flask deployments create interactive GUIs, we use a robust mocking strategy:

1. **For Notebook Deployment:**
   - Mock `IPython.display.display` to verify it's called with the correct widgets
   - Mock `matplotlib.pyplot` functions to avoid actual plot rendering
   - Mock `ipywidgets` components to verify they're created with the right properties

2. **For Flask Deployment:**
   - Use Flask's test client to simulate HTTP requests
   - Mock `matplotlib.pyplot.savefig` to avoid actual plot rendering
   - Verify HTML responses contain the expected elements

### Test Coverage

The tests aim to cover:

1. **Unit Tests:**
   - Widget/component creation and updates
   - Layout configuration and creation
   - Parameter synchronization

2. **Integration Tests:**
   - End-to-end workflows
   - Multiple parameter updates
   - Plot generation and updates

### Fixtures

Common test fixtures are defined in `conftest.py` files in each test directory:

- `basic_parameters`: Creates a basic viewer with test parameters
- `notebook_deployer`: Creates a NotebookDeployer instance
- `flask_app`: Creates a Flask app for testing
- `flask_client`: Creates a Flask test client 