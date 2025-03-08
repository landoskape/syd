# SYD Testing Suite

This directory contains tests for the SYD package, including specialized tests for the GUI deployment modules.

## Test Organization

The tests are organized into the following directories:

- `tests/`: Root directory containing tests for core functionality
- `tests/_notyet_notebook/`: Future tests for the notebook deployment module (not yet active)
- `tests/_notyet_flask/`: Future tests for the flask deployment module (not yet active)

## Future Notebook Deployment Tests

The notebook deployment tests are organized into the following files (currently prefixed with "future_" to prevent pytest from running them):

- `future_widgets.py`: Tests for widget creation, updates, and callbacks
- `future_deployer_config.py`: Tests for deployer configuration
- `future_deployer_layout.py`: Tests for layout creation and positioning
- `future_deployer_updates.py`: Tests for plot updates and synchronization
- `future_deployer_integration.py`: Integration tests for the notebook deployer

## Future Flask Deployment Tests

The flask deployment tests are organized into the following files (currently prefixed with "future_" to prevent pytest from running them):

- `future_components.py`: Tests for component creation and updates
- `future_routes.py`: Tests for Flask routes
- `future_error_handling.py`: Tests for error handling
- `future_integration.py`: Integration tests for the Flask deployment

## Running the Tests

To run all active tests:

```bash
pytest
```

## Activating Future Tests

To activate the future tests, follow these steps:

1. Rename the directories by removing the "_notyet_" prefix:
   ```bash
   mv tests/_notyet_notebook tests/test_notebook
   mv tests/_notyet_flask tests/test_flask
   ```

2. Rename the test files by changing "future_" to "test_":
   ```bash
   cd tests/test_notebook
   for file in future_*.py; do mv "$file" "test_${file#future_}"; done
   
   cd ../test_flask
   for file in future_*.py; do mv "$file" "test_${file#future_}"; done
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