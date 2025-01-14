# Portable Viewer Applications Design

## Overview

This document outlines a design for creating self-contained, shareable viewer applications that can be saved and run without requiring Python knowledge from the end user.

## Core Concepts

1. Bundle Format: A `.viewer` file (actually a zip) containing:
   - Viewer configuration
   - Data files
   - Static assets
   - Standalone executable

2. Creation API:
```python
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .add_data("main_data", df)  # Include data in bundle
    .build()

# Create portable bundle
viewer.export_portable("my_analysis.viewer")
```

3. Launcher Application:
- Small executable that can open .viewer files
- Handles web server setup automatically
- Provides simple UI for port configuration

## Implementation Details

### 1. Bundle Structure
```
my_analysis.viewer/
  ├── manifest.json      # Viewer configuration and metadata
  ├── data/             # Data files
  │   ├── main_data.parquet
  │   └── auxiliary.csv
  ├── assets/           # Static web assets
  │   ├── index.html
  │   ├── styles.css
  │   └── bundle.js
  └── viewer_config.yaml # Parameter and plot settings
```

### 2. Manifest Format
```json
{
  "version": "1.0",
  "name": "My Analysis",
  "creator": "username",
  "created_date": "2024-01-13",
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
        
        # 2. Export data files
        self._export_data(f"{tmp}/data")
        
        # 3. Copy web assets
        self._copy_assets(f"{tmp}/assets")
        
        # 4. Create manifest
        self._create_manifest(f"{tmp}/manifest.json")
        
        # 5. Create zip bundle
        shutil.make_archive(filename, 'zip', tmp)
        
        # 6. Rename to .viewer
        os.rename(f"{filename}.zip", f"{filename}.viewer")
```

### 4. Launcher Implementation

1. Simple Electron Application:
```javascript
const { app, BrowserWindow } = require('electron')
const server = require('./server')

app.on('ready', () => {
  // Start local server
  server.start()
  
  // Open viewer window
  const win = new BrowserWindow({
    width: 800,
    height: 600
  })
  
  win.loadURL('http://localhost:3000')
})
```

2. Python Server Component:
```python
class ViewerServer:
    def __init__(self, viewer_path: str):
        self.manifest = self._load_manifest(viewer_path)
        self.data = self._load_data()
        self.app = self._create_app()
    
    def run(self, port: int = 3000):
        self.app.run(port=port)
        
    def _create_app(self):
        app = Flask(__name__)
        # Set up routes for data and viewer
        return app
```

### 5. Security Considerations

1. Data Protection:
- Hash check for bundle integrity
- Optional password protection
- Data encryption at rest

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
# Create viewer with data
viewer = ViewerBuilder()\
    .add_selection("dataset", ["A", "B"])\
    .add_float("threshold", 0, 1)\
    .add_data("main_data", pd.read_csv("data.csv"))\
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
        "port": 8080,
        "password": "optional_password",
        "data_format": "parquet"
    }
)
```

### 3. Running Viewer
```bash
# Command line
dataviewer run my_analysis.viewer

# Or double-click .viewer file on supported systems
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

## Future Considerations

1. Updates:
- Version checking
- Asset updating
- Data refresh

2. Collaboration:
- Shared viewing sessions
- Comments/annotations
- Change tracking

3. Integration:
- Export to other formats
- Cloud hosting option
- Enterprise deployment

## Development Roadmap

1. Phase 1: Basic Bundling
- Implement bundle format
- Create/extract utilities
- Basic web server

2. Phase 2: Launcher
- Electron application
- System integration
- Port management

3. Phase 3: Security
- Data protection
- Network security
- Permissions

4. Phase 4: Distribution
- Installers
- Auto-updates
- System integration

5. Phase 5: Advanced Features
- Collaboration
- Cloud sync
- Enterprise features