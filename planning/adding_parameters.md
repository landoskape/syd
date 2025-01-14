# Parameter Addition Methods Guide

## Design Philosophy

DataViewer provides two approaches for adding parameters to viewers: method-based (primary API) and string-based (advanced API). The method-based approach is recommended for most users.

## Method-Based API

### Core Design
```python
viewer = ViewerBuilder()\
    .add_text("title")\
    .add_selection("dataset", ["A", "B"])\
    .add_float("threshold", 0, 1)\
    .add_range("dates", min="2023-01-01", max="2024-01-01")\
    .build()
```

### Available Methods

Each parameter type has its own dedicated method:

```python
add_text(name: str, default: str = "") -> Builder
add_selection(name: str, options: List[Any], default: str = None) -> Builder
add_multiple_selection(name: str, options: List[Any], defaults: List[Any] = None) -> Builder
add_integer(name: str, min_value: int, max_value: int, step: int = 1) -> Builder
add_float(name: str, min_value: float, max_value: float, step: float = 0.1) -> Builder
add_boolean(name: str, default: bool = False) -> Builder
add_pair(name: str, min_value: Union[int, float], max_value: Union[int, float]) -> Builder
add_range(name: str, min_value: Union[int, float], max_value: Union[int, float]) -> Builder
```

### Advantages
- Type safety and IDE support
- Clear parameter validation
- Discoverable API
- Less prone to errors
- Self-documenting

### Disadvantages
- Less flexible for extensions
- More implementation code
- Harder for programmatic generation

## String-Based API (Advanced)

### Core Design
```python
viewer = ViewerBuilder()\
    .add_parameter("dataset", type="selection", options=["A", "B"])\
    .add_parameter("threshold", type="float", min=0, max=1)\
    .build()
```

### Usage
```python
add_parameter(
    name: str,
    type: str,
    **config: Dict[str, Any]
) -> Builder
```

### Advantages
- More flexible for extensions
- Easier programmatic generation
- Better for serialization
- Supports dynamic parameters

### Disadvantages
- Less IDE support
- Runtime type checking only
- More prone to errors
- Less discoverable

## Implementation Strategy

1. Implement method-based API as primary interface
2. Build string-based API on top of method-based
3. Share validation logic between both approaches

```python
class ViewerBuilder:
    def add_selection(self, name: str, options: List[Any], default: str = None) -> 'ViewerBuilder':
        """Primary API method for selection parameters."""
        self._validate_selection_params(name, options, default)
        return self.add_parameter(name, type="selection", options=options, default=default)

    def add_parameter(self, name: str, type: str, **config: Dict[str, Any]) -> 'ViewerBuilder':
        """Advanced API method for flexible parameter addition."""
        if type not in PARAMETER_TYPES:
            raise ValueError(f"Unknown parameter type: {type}")
        # Delegate to appropriate validation method
        getattr(self, f"_validate_{type}_params")(name, **config)
        self.parameters[name] = {
            "type": type,
            **config
        }
        return self
```

## Best Practices

1. Parameter Naming:
```python
# Good
.add_selection("dataset", ["A", "B"])
.add_float("threshold", 0, 1)

# Avoid
.add_selection("d", ["A", "B"])  # Too short
.add_float("my_very_long_parameter_name", 0, 1)  # Too long
```

2. Default Values:
```python
# Good - sensible defaults
.add_integer("bins", 1, 100, default=10)
.add_boolean("show_grid", default=True)

# Avoid - unclear defaults
.add_integer("bins", 1, 100)  # No default
.add_selection("color", ["red", "blue"], default="chartreuse")  # Unexpected default
```

3. Value Ranges:
```python
# Good - logical ranges
.add_float("opacity", 0, 1)
.add_integer("age", 0, 150)

# Avoid - arbitrary ranges
.add_float("opacity", -1000, 1000)
.add_integer("age", -100, 1000)
```

## Error Handling

Provide clear error messages for common issues:

```python
def add_selection(self, name: str, options: List[Any], default: str = None):
    if not options:
        raise ValueError(f"Parameter '{name}': Options list cannot be empty")
    if default and default not in options:
        raise ValueError(f"Parameter '{name}': Default value '{default}' not in options")
    # ... rest of implementation
```

## Type Hints

Use comprehensive type hints for better IDE support:

```python
from typing import List, Union, TypeVar, Optional

T = TypeVar('T', bound='ViewerBuilder')

class ViewerBuilder:
    def add_selection(
        self: T,
        name: str,
        options: List[Any],
        default: Optional[str] = None
    ) -> T:
        ...
```

This design balances ease of use with flexibility, making the API accessible to newcomers while supporting advanced use cases.