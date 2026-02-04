---
name: syd
description: Use Syd when creating interactive matplotlib-based GUIs for data visualization with parameterized plotting interfaces. Works in Jupyter notebooks or web browsers.
---

# Syd Skills Guide

Syd creates interactive matplotlib GUIs from plotting functions. Convert functions with parameters into interactive interfaces for Jupyter notebooks or web browsers.

## Core Concepts

**Workflow:** Define plot function (`state` dict → matplotlib Figure) → Create Viewer → Add parameters → Deploy (`show()` for notebook, `share()` for browser)

**Creating Viewers:**
- **Simple/Ad-hoc (notebooks):** Use `make_viewer(plot_func)` - easiest for quick interactive exploration
- **Complex (modules):** Subclass `Viewer` - ideal for reusable classes with callbacks, data management, or complex logic

**State:** Plot functions receive `state: Dict[str, Any]` with current parameter values. Access via `state["param_name"]` or `viewer.state`.

**Lifecycle:** Add parameters BEFORE deployment (`add_*`), update AFTER deployment (`update_*`).

## Basic Example

```python
import numpy as np
import matplotlib.pyplot as plt
from syd import make_viewer

def plot(state):
    fig = plt.figure()
    t = np.linspace(0, 2 * np.pi, 1000)
    ax = plt.gca()
    ax.plot(t, state["amplitude"] * np.sin(state["frequency"] * t), 
            color=state["color"])
    return fig

viewer = make_viewer(plot)
viewer.add_float("amplitude", value=1.0, min=0.1, max=2.0)
viewer.add_float("frequency", value=1.0, min=0.1, max=5.0)
viewer.add_selection("color", value="red", options=["red", "blue", "green"])
viewer.show()  # or viewer.share() for browser
```

## Class-Based Approach

**When to subclass:** For complex, reusable viewers in modules - especially when you need callbacks, data management, or hierarchical dependencies. For simple ad-hoc viewers in notebooks, `make_viewer()` is easier.

```python
class MyViewer(Viewer):
    def __init__(self):
        self.add_float("x", value=1.0, min=0, max=10)
        self.add_selection("mode", value="linear", options=["linear", "log"])
        self.on_change("x", self.update_mode)
    
    def update_mode(self, state):
        if state["x"] > 5:
            self.update_selection("mode", value="log")
    
    def plot(self, state):
        return plt.figure()  # Use state["x"], state["mode"]
```

## Data Loading

Load data before creating viewer (closure or instance variable), not inside plot function:

```python
# Closure pattern
data = load_data()
def plot(state):
    return plt.figure()  # Access data from closure
viewer = make_viewer(plot)

# Class pattern
class DataViewer(Viewer):
    def __init__(self, data):
        self.data = data
        self.add_integer("index", min=0, max=len(data)-1)
    def plot(self, state):
        return plt.figure()  # Access self.data
```

## Callbacks

**Register:** `viewer.on_change("param", callback)` or `on_change(["p1", "p2"], callback)`

**Signature:** `callback(state: Dict[str, Any]) -> None`. Use `update_*` methods to modify parameters.

**Execution flow:** When a parameter value changes:
1. Parameter value is updated in `viewer.parameters[name].value`
2. `viewer.state` is computed (reads current values from all parameters)
3. Callbacks registered for that parameter are executed with `viewer.state` as argument

**Important:** The `state` dict passed to callbacks reflects the updated parameter value. However, if your callback updates other parameters, use `self.state` (not the callback's `state` arg) after those updates to get fresh values, as cascading updates may occur.

**Hierarchical dependencies:** When parameters depend on each other (e.g., mouse → session → neuron):
- Use `self.state` (not callback's `state` arg) after updates to get fresh values
- Each callback updates its level and calls the next level
- Initialize in `__init__` to set up initial state

```python
class HierarchicalViewer(Viewer):
    def __init__(self, mice_names):
        self.add_selection("mouse", options=mice_names)
        self.add_integer("session", min=0, max=1)
        self.add_integer("neuron", min=0, max=1)
        self.on_change("mouse", self.update_mouse)
        self.on_change("session", self.update_session)
        self.update_mouse(self.state)  # Initialize
    
    def update_mouse(self, state):
        self.update_integer("session", max=get_num_sessions(state["mouse"]) - 1)
        self.update_session(self.state)  # Use fresh state
    
    def update_session(self, state):
        self.update_integer("neuron", max=get_num_neurons(state["mouse"], state["session"]) - 1)
```

## Deployment

```python
viewer.show()  # Notebook: controls_position="left", controls_width_percent=20, update_threshold=1.0
viewer.share()  # Browser: fig_dpi=300, host=None (localhost), port=None (auto), open_browser=True
viewer.deploy(env="notebook")  # or "browser"
```

## Parameter Reference

### Adding Parameters

| Method | Required | Optional | Defaults |
|--------|----------|----------|----------|
| `add_text(name, value=...)` | - | - | `value=""` |
| `add_boolean(name, value=...)` | - | - | `value=True` |
| `add_selection(name, options, value=...)` | `options` | - | `value=options[0]` |
| `add_multiple_selection(name, options, value=...)` | `options` | - | `value=[]` |
| `add_integer(name, min, max, value=...)` | `min`, `max` | - | `value=min` |
| `add_float(name, min, max, value=..., step=...)` | `min`, `max` | `step` | `value=min`, `step=0.01` |
| `add_integer_range(name, min, max, value=...)` | `min`, `max` | - | `value=(min, max)` |
| `add_float_range(name, min, max, value=..., step=...)` | `min`, `max` | `step` | `value=(min, max)`, `step=0.01` |
| `add_unbounded_integer(name, value=...)` | - | - | `value=0` |
| `add_unbounded_float(name, value=..., step=...)` | - | `step` | `value=0`, `step=None` |
| `add_button(name, callback, label=..., replot=...)` | `callback` | `label`, `replot` | `label=name`, `replot=True` |

**Notes:** `value` accepts `NO_INITIAL_VALUE` for defaults. `options` must be hashable/non-empty. Numeric params clamp to bounds. Range params swap if `low > high`. Floats round to `step`.

### Updating Parameters

| Method | Updatable Fields |
|--------|------------------|
| `update_text(name, value=...)` | `value` |
| `update_boolean(name, value=...)` | `value` |
| `update_selection(name, value=..., options=...)` | `value`, `options` |
| `update_multiple_selection(name, value=..., options=...)` | `value`, `options` |
| `update_integer(name, value=..., min=..., max=...)` | `value`, `min`, `max` |
| `update_float(name, value=..., min=..., max=..., step=...)` | `value`, `min`, `max`, `step` |
| `update_integer_range(name, value=..., min=..., max=...)` | `value`, `min`, `max` |
| `update_float_range(name, value=..., min=..., max=..., step=...)` | `value`, `min`, `max`, `step` |
| `update_unbounded_integer(name, value=...)` | `value` |
| `update_unbounded_float(name, value=..., step=...)` | `value`, `step` |
| `update_button(name, label=..., callback=..., replot=...)` | `label`, `callback`, `replot` |

**Updates:** Only work AFTER deployment. Omit parameters to update only specific fields.

## Common Patterns

```python
# Button
viewer.add_button("save", callback=lambda s: viewer.figure.savefig('out.png'), replot=False)

# Conditional updates
viewer.on_change("mode", lambda s: self.update_float("threshold", max=1.0 if s["mode"]=="advanced" else 0.5))

# Access last figure
viewer.figure  # Returns matplotlib Figure or None
```

## Gotchas

**Parameter constraints:**
- `options` cannot be empty for selection parameters (raises `ParameterAddError`)
- `options` must be hashable (raises `ParameterAddError` if not)
- Selection values must be in `options` (raises `ParameterUpdateError` if not)
- Parameter names must be strings (not ints/other types)
- Cannot add duplicate parameter names (raises `ParameterAddError`)

**Lifecycle restrictions:**
- Cannot add parameters while deployed (raises `RuntimeError`)
- Cannot update parameters before deployment (raises `ParameterUpdateError`)
- Cannot update non-existent parameters (raises `ParameterUpdateError`)
- Cannot register `on_change()` for non-existent parameters (raises `ValueError`)

**Value constraints:**
- Values outside `min/max` get clamped (with warnings) - cannot force value outside bounds
- When updating `min/max`, current value gets clamped if outside new range
- If `min > max`, they get swapped (with warning)
- Range parameters: if `low > high`, values get swapped

**Callback requirements:**
- Callbacks must have exactly one positional parameter: `callback(state)` 
- Invalid signatures raise `ValueError` (e.g., no args, two args, wrong kwargs)

## Best Practices

- Plot function: Create new figure, return it (don't call `plt.show()`), access data via closure/instance vars
- Parameters: Add before deployment, use `self.state` after updates in callbacks
- Performance: Use `update_threshold` for slow plots, `share()` for fast plots, `show()` for slow plots
- Data: Load before creating viewer, avoid loading inside plot function
