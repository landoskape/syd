# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2025-04-29

### Added
- Now, the Syd GUI (i.e. the deployers) store a reference to the last figure generated in the viewer. This
  is available via the `viewer.figure` property method and returns None when no figure has been generated yet.
- Added `save_figure` example to the tutorial.

### Changed
- Buttons now have a `replot` keyword argument to control whether the figure is replotted when the button is clicked. If this
  is set to False, the button will only trigger the callback function, and update parameters, but not replot the figure. 

### Fixed
- Previously, the deployer was aggressive at rejecting matplotlib backends that weren't recognized. Now, it permits any backend,
but just sends a warning that there might be strange behavior. 

## [1.2.1] - 2025-04-25

### Fixed
- The type hints in the support module were incompatible with Python 3.9. Fixed. 


## [1.2.0] - 2025-04-25

This is the first release of Syd as a "complete" package with all the promised functionality. This is the first changelog entry that
really matters since everything before was essentially just pre-release testing and development. 

### Added
- Web browser deployment via Flask and SocketIO (`viewer.share()`). Includes dynamic HTML/JS frontend (`index.html`, `viewer.js`, `styles.css`).
- Notebook deployment refactored into `NotebookDeployer` using `ipywidgets`.
- `make_viewer` factory function for simplified viewer instantiation.
- `NoInitialValue` singleton to allow creating parameters without an initial value.
- Explicit callback registration system (`viewer.on_change`).
- Comprehensive documentation built with Sphinx (`pydata-sphinx-theme`), including tutorials, API reference, and core concepts.
- New example notebook for hierarchical callbacks (`4-hierarchical_callbacks.ipynb`).

### Changed
- **Breaking**: Renamed main class `InteractiveViewer` to `Viewer`. Access via `from syd import Viewer`.
- **Breaking**: Simplified deployment API: `viewer.show()` for notebooks and `viewer.share()` for web browser replace `viewer.deploy(env=...)`.
- **Breaking**: Integer and Float parameters now use `min` and `max` keyword arguments instead of `min_value` and `max_value`.
- **Breaking**: Callback function signature simplified to accept only the `state` dictionary.
- Refactored parameter implementation into base `Parameter` class and specific subclasses (`syd.parameters`).
- Improved parameter validation using `ParameterAddError`, `ParameterUpdateError`, and `ParameterUpdateWarning`.
- Improved state management and update logic within the `Viewer` class.
- Enhanced notebook deployment with debouncing and better handling of `%matplotlib widget`.
- Enhanced web deployment with debouncing for smoother updates.
- Updated all example notebooks (`1-simple_example.ipynb`, `2a-complex_example.ipynb`, `2b-subclass_example.ipynb`, `3-data_loading.ipynb`) to align with API changes.

### Removed
- Old deployment functions/logic superseded by `Viewer.show()` and `Viewer.share()`.
- Deprecated parameter exception classes.
- Removed internal `syd.support` module; functionality integrated into relevant modules.

## [0.2.0] - 2025-04-15

### Added
- Support for web browser viewing alongside Jupyter notebooks.
- New parameter types and improved parameter handling, including `NoInitialValue` for default parameter values so it's possible to create a parameter without defining the initial value.

### Changed
- Refactored parameter validation and update logic for better consistency and error handling.
- Improved documentation for parameter operations and viewer class methods.
- **Breaking**: integer and float parameters now use "min" and "max" instead of "min_value" and "max_value".

### Removed
- Deprecated old parameter exception classes in favor of a unified approach.

## [0.1.7] - 2025-03-05

### Added
- New documentation pages with improved examples and tutorials
- Added detailed To-Do list section in README with development priorities
- Added support for dynamic versioning

### Changed
- **Breaking**: Renamed the main class from "InteractiveViewer" to "Viewer" throughout the codebase
- **Breaking**: Simplified callback functions to use a single argument (state) instead of (viewer, state)
- Clarified in README that web browser viewing is a future feature (currently only works in Jupyter notebooks)
- Improved documentation with clearer examples and better structure

### New
- Technical documentation for extending Syd to support Plotly and Pandas plotting alongside Matplotlib

## [0.1.6] - 2025-01-22

Initial tracked release. 