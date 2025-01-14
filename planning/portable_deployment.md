# Portable Viewer Applications Design

## Overview

This document outlines a design for creating self-contained, shareable viewer applications that can be saved and run without requiring Python knowledge from the end user, with proper deployment state management.

## Core Concepts

1. Bundle Format: A `.viewer` file (actually a zip) containing:
   - Viewer configuration
   - Data files
   - Static assets
   - Standalone executable
   - Deployment state configuration

2. Creation API:
```python
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .add_data("main_data", df)\
    .build()

# Create portable bundle
viewer.export_portable("my_analysis.viewer")
```

## Implementation Details

### 1. Bundle Structure
```
my_analysis.viewer/
  ├── manifest.json        # Viewer configuration and metadata
  ├── deployment.json      # Deployment state configuration
  ├── data/               # Data files
  │   ├── main_data.parquet
  │   └── auxiliary.csv
  ├── assets/             # Static web assets
  │   ├── index.html
  │   ├── styles.css
  │   └── bundle.js
  └── viewer_config.yaml   # Parameter and plot settings
```

### 2. Manifest Format
```json
{
  "version": "1.0",
  "name": "My Analysis",
  "creator": "username",
  "created_date": "2024-01-13",
  "deployment_state": {
    "auto_deploy": true,
    "initial_parameters": [...],
    "update_rules": [...]
  },
  "parameters": [...],
  "data_files": {
    "main_data": {
      "path": "data/main_data.parquet",
      "format": "parquet",
      "rows": 10000
    }
  }
}
```

### 3. Export Process
```python
def export_portable(self, filename: str) -> None:
    """Create a portable viewer bundle."""
    with tempfile.TemporaryDirectory() as tmp:
        # 1. Save configuration
        self._save_config(f"{tmp}/viewer_config.yaml")
        
        # 2. Export deployment state configuration
        self._save_deployment_config(f"{tmp}/deployment.json")
        
        # 3. Export data files
        self._export_data(f"{tmp}/data")
        
        # 4. Copy web assets
        self._copy_assets(f"{tmp}/assets")
        
        # 5. Create manifest
        self._create_manifest(f"{tmp}/manifest.json")
        
        # 6. Create zip bundle
        shutil.make_archive(filename, 'zip', tmp)
        
        # 7. Rename to .viewer
        os.rename(f"{filename}.zip", f"{filename}.viewer")
```

### 4. Launcher Implementation

```javascript
const { app, BrowserWindow } = require('electron')
const server = require('./server')

app.on('ready', () => {
  // Load deployment configuration
  const deployConfig = loadDeploymentConfig()
  
  // Start local server with deployment state
  server.start(deployConfig)
  
  // Open viewer window
  const win = new BrowserWindow({
    width: 800,
    height: 600
  })
  
  win.loadURL('http://localhost:3000')
})
```

Python Server Component:
```python
class ViewerServer:
    def __init__(self, viewer_path: str):
        self.manifest = self._load_manifest(viewer_path)
        self.deployment_config = self._load_deployment_config()
        self.data = self._load_data()
        self.app = self._create_app()
        
    def run(self, port: int = 3000):
        with self.viewer._app_deployed():
            self.app.run(port=port)
```

### 5. Deployment State Management

1. Pre-deployment Configuration:
```python
class PortableViewer:
    def configure_deployment(self):
        # Add initial parameters
        self.add_selection("dataset", ["A", "B"])
        self.add_float("threshold", 0, 1)
        
        # Configure update rules
        self.add_update_rule("dataset", 
            lambda d: self.update_float("threshold", 0, 2 if d == "B" else 1))
```

2. Runtime State Management:
```python
class ViewerRunner:
    def run_portable(self, viewer_path: str):
        viewer = self.load_viewer(viewer_path)
        
        # Enter deployed state
        with viewer._app_deployed():
            # Only updates allowed now
            self.start_server(viewer)
            self.open_interface()
```

### 6. Security Considerations

1. Deployment State Protection:
- Validate state transitions
- Prevent unauthorized parameter modifications
- Ensure callback safety

2. Network Security:
- Local-only server binding
- Random port assignment
- CORS protection

3. File System:
- Sandboxed data access
- Temporary file cleanup
- Permission checks

## Usage Examples

### 1. Creating Portable Viewer
```python
# Create viewer with data and deployment config
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .add_float("threshold", 0, 1)\
    .add_data("main_data", pd.read_csv("data.csv"))\
    .configure_deployment(auto_deploy=True)\
    .build()

# Export as portable application
viewer.export_portable("my_analysis.viewer")
```

### 2. Advanced Configuration
```python
viewer.export_portable(
    "my_analysis.viewer",
    config={
        "name": "Sales Analysis 2024",
        "description": "Monthly sales analysis",
        "deployment": {
            "auto_deploy": True,
            "update_rules": {
                "dataset": "update_threshold_range"
            }
        },
        "port": 8080,
        "password": "optional_password",
        "data_format": "parquet"
    }
)
```

## Distribution

1. Standalone Launcher:
- Windows: .exe installer
- macOS: .dmg bundle
- Linux: .AppImage

2. File Association:
- Register .viewer extension
- Custom icon
- "Open with" integration

## Development Roadmap

1. Phase 1: Basic Bundling
- Implement bundle format
- Create/extract utilities
- Basic web server

2. Phase 2: Deployment State
- State management system
- Update rules
- Error handling

3. Phase 3: Security
- State validation
- Access control
- Error prevention

4. Phase 4: Distribution
- Installers
- Auto-updates
- System integration

5. Phase 5: Advanced Features
- Collaboration
- Cloud sync
- Enterprise features