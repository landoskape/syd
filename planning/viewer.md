# Interactive Viewer Design

## Overview
The InteractiveViewer is a base class for creating interactive data visualization applications. It provides a simple API for defining parameters and their relationships.

## Core Concepts

### Parameters
Parameters are the interactive controls that users can adjust. Each parameter has a type, value range, and optional default value.

Available parameter types:
- `add_text()`: Text input
- `add_selection()`: Single selection from a list
- `add_multiple_selection()`: Multiple selections from a list
- `add_integer()`: Integer within a range
- `add_float()`: Float within a range
- `add_boolean()`: True/false toggle
- `add_integer_pair()`: Two related integers
- `add_float_pair()`: Two related floats

### Parameter Dependencies
Dependencies between parameters are handled through callbacks using the `on_change()` method. When a parameter changes, its registered callback function is called with the new value.

## Basic Usage Example

```python
class MLModelViewer(InteractiveViewer):
    def __init__(self):
        super().__init__()
        # Add parameters
        self.add_selection("model", ["cnn", "transformer"])
        self.add_integer("num_layers", 1, 10)
        self.add_float("dropout", 0, 1)
        
        # Register callbacks
        self.on_change("model", self._update_model_params)
    
    def _update_model_params(self, model_type: str):
        """Update layer count and dropout based on model type."""
        if model_type == "cnn":
            self.update_integer("num_layers", 1, 5)
            self.update_float("dropout", 0.2, 0.5)
        else:  # transformer
            self.update_integer("num_layers", 4, 12)
            self.update_float("dropout", 0.1, 0.3)
        
    def plot(self, **kwargs):
        """Create and return the visualization."""
        # Implementation specific to this viewer
        pass
```

## API Reference

### Parameter Registration
```python
add_text(name: str, default: str = "") -> None
add_selection(name: str, options: List[Any], default: Any = None) -> None
add_integer(name: str, min_value: int, max_value: int, default: int = None) -> None
add_float(name: str, min_value: float, max_value: float, default: float = None) -> None
add_boolean(name: str, default: bool = False) -> None
```

### Parameter Updates
```python
update_text(name: str, default: str = "") -> None
update_selection(name: str, options: List[Any], default: Any = None) -> None
update_integer(name: str, min_value: int, max_value: int, default: int = None) -> None
update_float(name: str, min_value: float, max_value: float, default: float = None) -> None
update_boolean(name: str, default: bool = False) -> None
```

### Dependency Management
```python
on_change(parameter_name: str, callback: Callable) -> None
```

## Implementation Guidelines

1. Always inherit from InteractiveViewer
2. Register parameters in `__init__()`
3. Register callbacks after parameter creation
4. Implement the `plot()` method
5. Use clear, descriptive names for callback functions

## Error Handling
- Parameters must be registered before use
- Callbacks can only be registered for existing parameters
- Parameter updates maintain type consistency
- Invalid values are clamped to parameter ranges