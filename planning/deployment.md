# DataViewer Deployment Guide

## Overview

DataViewer is designed to be accessible to users of all skill levels while maintaining the flexibility needed for advanced use cases. This guide covers the different ways to deploy DataViewer applications, with special attention to deployment state management.

## Core Concepts

Every DataViewer application consists of:

1. Parameter definitions (what users can control)
2. Plot function (how data is visualized)
3. Deployment method (how users interact with the viewer)
4. Deployment state (when parameters can be modified)

## Deployment State Management

DataViewer enforces strict rules about when parameters can be modified:

```python
# Pre-deployment: Can add parameters
viewer = MyViewer()
viewer.add_selection("dataset", ["A", "B"])  # ✓ Allowed

# During deployment: Can only update existing parameters
with viewer._app_deployed():
    viewer.update_selection("dataset", ["A", "B", "C"])  # ✓ Allowed
    viewer.add_float("new_param", 0, 1)  # ✗ Raises RuntimeError
```

## Deployment Options

### 1. Jupyter Notebook Integration
**Difficulty Level: 2/10**

```python
from dataviewer import ViewerBuilder

# Define parameters before deployment
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .add_float("threshold", 0, 1)\
    .build()

# Run with automatic deployment state management
viewer.run_in_notebook()  # Handles _app_deployed context
```

**Implementation Requirements:**
- Special notebook renderer class
- IPython widget integration
- Automatic deployment state management
- Notebook-specific state handling

### 2. Standalone Python Script
**Difficulty Level: 3/10**

```python
# view_data.py
from dataviewer import ViewerBuilder

class MyViewer(ViewerBuilder):
    def __init__(self):
        super().__init__()
        # Add parameters before deployment
        self.add_selection("dataset", ["A", "B"])
        
        # Register callbacks for parameter updates
        self.on_change("dataset", self._update_params)
    
    def _update_params(self, dataset: str):
        # Updates happen during deployment
        if dataset == "A":
            self.update_float("threshold", 0, 1)
        else:
            self.update_float("threshold", 0, 2)

if __name__ == "__main__":
    viewer = MyViewer()
    viewer.run()  # Handles deployment state internally
```

### 3. Web Application
**Difficulty Level: 3/10**

```python
from dataviewer.web import create_web_app

# Define parameters before deployment
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .build()

app = create_web_app(viewer)
app.run()  # Handles deployment state
```

### 4. Desktop Application
**Difficulty Level: 3/10**

```python
from dataviewer.desktop import create_desktop_app

# Define parameters before deployment
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .build()

app = create_desktop_app(viewer)
app.run()  # Handles deployment state
```

### 5. Command Line Interface
**Difficulty Level: 3/10**

```python
from dataviewer.cli import CLI

viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .build()

CLI(viewer).run()  # Handles deployment state
```

## Making Deployment Easy

### 1. Project Templates
```bash
# Command line tools that handle deployment state
dataviewer create notebook
dataviewer create script
dataviewer create webapp
dataviewer create desktop
```

### 2. Configuration Files
```yaml
# config.yaml
viewer:
  parameters:
    - name: dataset
      type: selection
      options: [A, B]
  
deployment:
  type: web
  settings:
    port: 8080
    auto_deploy: true  # Automatically handles deployment state
```

## Error Handling During Deployment

```python
class MyViewer(InteractiveViewer):
    def handle_deployment_errors(self):
        try:
            with self._app_deployed():
                # Parameter updates allowed
                self.update_float("threshold", 0, 2)
                
                # These will raise errors
                self.add_new_param()  # RuntimeError
                self.update_wrong_type()  # TypeError
                self.update_missing()  # ValueError
        except RuntimeError:
            # Handle deployment state violations
            pass
        except TypeError:
            # Handle type mismatches
            pass
        except ValueError:
            # Handle missing parameters
            pass
```

## Implementation Guidelines

### Core Architecture
1. Separate parameter definition from deployment
2. Use dependency injection for platform-specific code
3. Implement common interface for all deployment types
4. Maintain deployment state consistency

### Testing Strategy
1. Unit tests for viewer building
2. Integration tests for each deployment type
3. End-to-end tests for complete workflows
4. Deployment state transition tests
5. Error handling tests

### Security Considerations
1. Data handling and privacy
2. Web security for server deployment
3. File system access controls
4. Network security for remote data
5. Deployment state validation

## Development Roadmap
1. Phase 1: Core viewer functionality and state management
2. Phase 2: Notebook and script deployment
3. Phase 3: Web deployment
4. Phase 4: Desktop and CLI deployment
5. Phase 5: Interactive builder and tools