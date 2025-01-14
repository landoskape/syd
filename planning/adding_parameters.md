# Parameter Addition Methods Guide

## Design Philosophy

InteractiveViewer provides two distinct phases for parameter handling: addition (pre-deployment) and updating (during deployment). This separation ensures parameter consistency while allowing runtime flexibility.

## Parameter Addition API (Pre-deployment)

### Core Design
```python
class MyViewer(InteractiveViewer):
    def __init__(self):
        super().__init__()
        self.add_text("title")
        self.add_selection("dataset", ["A", "B"])
        self.add_float("threshold", 0, 1)
        self.add_boolean("show_grid", default=True)
```

### Available Methods

Each parameter type has its own dedicated method:

```python
add_text(name: str, default: str = "") -> None
add_selection(name: str, options: List[Any], default: Any = None) -> None
add_multiple_selection(name: str, options: List[Any], defaults: List[Any] = None) -> None
add_integer(name: str, min_value: int, max_value: int, default: int = None) -> None
add_float(name: str, min_value: float, max_value: float, step: float = 0.1, default: float = None) -> None
add_boolean(name: str, default: bool = False) -> None
add_integer_pair(name: str, min_value: int, max_value: int, default_low: int = None, default_high: int = None) -> None
add_float_pair(name: str, min_value: float, max_value: float, step: float = 0.1, default_low: float = None, default_high: float = None) -> None
```

## Parameter Update API (During Deployment)

### Core Design
```python
# During deployment
viewer.update_text("title", default="New Title")
viewer.update_selection("dataset", ["A", "B", "C"])
viewer.update_float("threshold", 0, 2)
```

### Available Methods

Each parameter type has a corresponding update method with the same signature as its add method:

```python
update_text(name: str, default: str = "") -> None
update_selection(name: str, options: List[Any], default: Any = None) -> None
update_multiple_selection(name: str, options: List[Any], defaults: List[Any] = None) -> None
update_integer(name: str, min_value: int, max_value: int, default: int = None) -> None
update_float(name: str, min_value: float, max_value: float, step: float = 0.1, default: float = None) -> None
update_boolean(name: str, default: bool = False) -> None
update_integer_pair(name: str, min_value: int, max_value: int, default_low: int = None, default_high: int = None) -> None
update_float_pair(name: str, min_value: float, max_value: float, step: float = 0.1, default_low: float = None, default_high: float = None) -> None
```

## Implementation Strategy

1. Parameter Registration (Pre-deployment):
```python
class MyViewer(InteractiveViewer):
    def __init__(self):
        super().__init__()
        # Add initial parameters
        self.add_selection("dataset", ["A", "B"])
        self.add_float("threshold", 0, 1)
        
        # Register callbacks
        self.on_change("dataset", self._update_threshold_range)
    
    def _update_threshold_range(self, dataset: str):
        """Update threshold range based on dataset."""
        with self._app_deployed():
            if dataset == "A":
                self.update_float("threshold", 0, 1)
            else:
                self.update_float("threshold", 0, 2)
```

2. Runtime Updates (During Deployment):
```python
viewer = MyViewer()
with viewer._app_deployed():
    viewer.update_selection("dataset", ["A", "B", "C"])
    viewer.update_float("threshold", 0, 3)
```

## Best Practices

1. Parameter Naming:
```python
# Good
viewer.add_selection("dataset", ["A", "B"])
viewer.add_float("threshold", 0, 1)

# Avoid
viewer.add_selection("d", ["A", "B"])  # Too short
viewer.add_float("my_very_long_parameter_name", 0, 1)  # Too long
```

2. Default Values:
```python
# Good - sensible defaults
viewer.add_integer("bins", 1, 100, default=10)
viewer.add_boolean("show_grid", default=True)

# Avoid - unclear defaults
viewer.add_integer("bins", 1, 100)  # No default
viewer.add_selection("color", ["red", "blue"], default="chartreuse")  # Unexpected default
```

3. Value Ranges:
```python
# Good - logical ranges
viewer.add_float("opacity", 0, 1)
viewer.add_integer("age", 0, 150)

# Avoid - arbitrary ranges
viewer.add_float("opacity", -1000, 1000)
viewer.add_integer("age", -100, 1000)
```

## Error Handling

The system provides clear error messages for common issues:

```python
# Adding parameter during deployment
with viewer._app_deployed():
    viewer.add_float("new_param", 0, 1)  # Raises RuntimeError

# Updating non-existent parameter
viewer.update_float("unknown", 0, 1)  # Raises ValueError

# Updating with wrong type
viewer.update_integer("float_param", 0, 1)  # Raises TypeError
```

## Type Hints

Method signatures include comprehensive type hints:

```python
from typing import List, Union, TypeVar, Optional

def add_selection(
    self,
    name: str,
    options: List[Any],
    default: Optional[Any] = None
) -> None:
    ...
```

This design maintains consistency while providing flexibility for runtime updates, with clear separation between parameter addition and update operations.