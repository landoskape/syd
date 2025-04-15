# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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