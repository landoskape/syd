# Parameter Dependencies in InteractiveViewer

## Overview

The InteractiveViewer implements a dynamic parameter dependency system that allows certain parameters to update their properties (like min/max values or available options) based on the current state of other parameters. This system is designed to be simple for basic users while providing power and flexibility for advanced use cases.

## Core Concepts

### Dependent Parameters

Parameters can be marked as "dependent" during registration. These parameters will be recomputed whenever any parameter changes. For example:

```python
class MyViewer(InteractiveViewer):
    def __init__(self):
        super().__init__()
        self.register_selection("experiment_name", ["exp1", "exp2"])
        # Mark unit_selector as dependent
        self.register_integer("unit_selector", 1, 10, dependent=True)
```

### Dependency Computation

When a dependent parameter exists, the system requires implementation of `compute_dependent_parameters()`. This method uses the same familiar registration API to update parameter properties:

```python
def compute_dependent_parameters(self):
    exp_name = self.parameters["experiment_name"]["value"]
    min_unit, max_unit = self.get_unit_range(exp_name)
    # Reuse familiar registration API
    self.register_integer("unit_selector", min_unit, max_unit)
```

## Implementation Details

### Context Manager System

The system uses a context manager internally to differentiate between initial parameter registration and dependency updates:

```python
class InteractiveViewer:
    def __init__(self):
        self._in_dependency_update = False
        
    @contextmanager
    def _updating_dependencies(self):
        self._in_dependency_update = True
        try:
            yield
        finally:
            self._in_dependency_update = False
```

### Registration Behavior

The registration methods behave differently based on context:

- In normal mode (`_in_dependency_update = False`):
  - Creates new parameters
  - Sets initial values and properties
  - Allows marking parameters as dependent

- In dependency update mode (`_in_dependency_update = True`):
  - Only allows updates to existing parameters
  - Validates parameter existence
  - Updates properties while maintaining parameter type

### Update Flow

1. GUI triggers parameter change
2. System enters dependency update mode
3. `compute_dependent_parameters()` is called
4. Dependent parameters are updated
5. System exits dependency update mode
6. GUI receives parameter updates

## Usage Guidelines

### Do's:
- Mark parameters as dependent during initial registration
- Use the same registration API in `compute_dependent_parameters()`
- Keep dependency logic focused on parameter properties

### Don'ts:
- Try to create new parameters in `compute_dependent_parameters()`
- Change parameter types during dependency updates
- Create circular dependencies

## Example Implementation

Here's a complete example showing how to implement dependent parameters:

```python
class ExperimentViewer(InteractiveViewer):
    def __init__(self):
        super().__init__()
        # Register parameters
        self.register_selection("experiment_name", ["exp1", "exp2"])
        self.register_integer("unit_selector", 1, 10, dependent=True)
        self.register_float("threshold", 0.0, 1.0, dependent=True)
        
    def compute_dependent_parameters(self):
        # Get current experiment
        exp_name = self.parameters["experiment_name"]["value"]
        
        # Update unit selector range
        min_unit, max_unit = self.get_unit_range(exp_name)
        self.register_integer("unit_selector", min_unit, max_unit)
        
        # Update threshold range
        min_thresh, max_thresh = self.get_threshold_range(exp_name)
        self.register_float("threshold", min_thresh, max_thresh)
```

## Implementation Notes

Internal validation should be added to prevent common mistakes:

1. Parameter existence validation:
```python
if self._in_dependency_update and name not in self.parameters:
    raise ValueError(f"Cannot create new parameter '{name}' in dependency update")
```

2. Type consistency validation:
```python
if self._in_dependency_update:
    current_type = type(self.parameters[name])
    if current_type != parameter_type:
        raise TypeError(f"Cannot change parameter type during dependency update")
```

3. Value adjustment when ranges change:
```python
def _adjust_value_to_bounds(self, param):
    if param["value"] < param["min_value"]:
        param["value"] = param["min_value"]
    elif param["value"] > param["max_value"]:
        param["value"] = param["max_value"]
```

These validations help prevent runtime errors and maintain system consistency while keeping the API simple for users.