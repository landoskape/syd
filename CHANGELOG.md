# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2025-04-30

### Added
- Added a functional dot product feature so you can choose cells that don't have bleedthrough. 
- Added a system to the ``SelectionGUI`` to hide and show features. This is useful if you 
  want to hide features that you don't regularly use so that the GUI is not cluttered.
- Added text describing the key commands to the ``SelectionGUI``.

### Changed
- SelectionGUI stacks features vertically so they are united by column. 

## [1.0.3] - 2025-03-13

### Added
- The changelog is now included in the documentation!

### Changed
- Previously, the ``CellectorManager`` class would infer the number of ROIs from
features saved to disk in the cellector directory. This meant that if you used
``CellectorManager.from_roi_processor`` and the ``RoiProcessor`` was using
``save_features=False``, then the ``CellectorManager`` would not know how many ROIs to
expect when building the manual label arrays. Now, the ``CellectorManager`` accepts an
additional optional argument ``num_rois`` which is automatically passed from the 
``RoiProcessor`` instance when using the ``make_from_roi_processor`` class method.


## [1.0.2] - 2025-03-13

### Added
- More type hints to the constructor module for better IDE support

### Changed
- Fixed import statements in gui.py to put PyQt5 before napari and pyqtgraph. This fixes
an issue where pyqtgraph would automatically import PySide6 if installed and prevent the
PyQt5 import from working. It should help make celletor more compatible with other environments.
- Improved README and fixed links.

## [1.0.1] - 2025-02-20

### Added
- Added Sphinx documentation infrastructure
  - New docs directory with comprehensive API reference
  - Added ReadTheDocs configuration
  - Added documentation requirements
  - Converted GUI documentation from markdown to RST
  - Added How It Works and Quickstart guides

### Changed
- Changed black line length from 150 to 88 characters
  - Updated .github/workflows/black.yml configuration
  - Added pyproject.toml black configuration
- Improved code formatting throughout codebase to match new line length
- Restructured documentation
  - Moved examples.md to RST format
  - Reorganized documentation files into source directory
  - Added proper RST documentation structure

### Removed
- Removed examples.md in favor of RST version
- Removed build reminder comments from pyproject.toml

## [1.0.0] - 2024-12-17

> ⚠️ **BREAKING CHANGES WARNING** ⚠️
> 
> This version introduces significant changes that will affect existing cellector 
> installations. Key changes include:
> - File naming conventions for features and criteria
> - Data structure shape for manual selections
> - Target cell filename convention
>
> **Action Required**: Follow the migration guide below before upgrading.

### Migration Guide

Several changes will prevent or complicate backwards compatibility. To address these 
issues, version 1.0.0 includes migration utilities to fix existing data structures. 
Here's what you need to know:

1. **Required Updates**:
   - `targetcell.npy` → `idx_selection.npy`
   - Manual selection shape from `(num_rois, 2)` to `(2, num_rois)`
   - Feature files from `{feature_name}.npy` to `{feature_name}_feature.npy`
   - Criteria files from `{feature_name}_criteria.npy` to `{feature_name}_featurecriteria.npy`

2. **Migration Workflow**:
```python
top_dir = "./some/path" # any path that you know contains all the cellector directories you've made
root_dirs = identify_cellector_folders(top_dir)
update_idx_selection_filenames(root_dirs)
update_manual_selection_shape(root_dirs)
update_feature_paths(root_dirs)
```

The [``tutorial.ipynb``](https://github.com/landoskape/cellector/blob/main/notebooks/tutorial.ipynb)
notebook includes explanations for how to do new things with the package including the deprecation handling.

### Added
A manager module with the ``CellectorManager`` class which can be used to manage the 
processing of data with the Cellector package. In short, this class can be constructed
from a ``root_dir`` or from an ``RoiProcessor`` instance directly, and has access to any
saved data on disk in the cellector directory (``Path(root_dir) / "cellector"``), the 
ability to update criterion values, update manual labels, and save updates including to 
save the master ``idx_selection`` file which is the primary output of cellector (i.e. a
boolean numpy array of which cells meet criteria to match features in a fluorescence 
image). This is now used by the ``SelectionGUI`` to handle all communication with the 
disk and can also be used in scripting (tutorials included). 

A new refactored ``SelectionGUI`` class. Nothing should change for the user, including 
import statements, but the GUI code is hopefully much more transparent. 

A method in ``cellector.io.operations`` called ``identify_feature_files`` which can be
used to identify any feature or feature criterion files stored in a cellector directory.

### Changed
IO Module always uses ``root_dir`` as input argument to all methods, user never has to
explicitly compute the ``save_dir`` (which was always ``Path(root_dir) / "cellector"``).

IO Module now also has methods for saving the ``idx_selection`` - the key output of the
cellector package. This is a numpy array of bools indicating which ROIs are "selected", 
e.g. meet the users criteria and manual labels that match fluorescence features in the 
reference images. 

IO Module method names changed from ``load_saved_{feature/criteria}`` to ``load_{f/c}``. 
The original names are still there but marked as deprecated. They'll be removed 
eventually.

### Removed
The IO module used to have a ``save_selection`` method for saving an entire cellector 
session. This is removed as it has been superceded by the ``CellectorManager`` class.


## [0.2.0] - 2024-12-09

### Added
Saving features is now optional! The create_from_{...} functions now have an optional
input argument called ``save_features`` that is passed to the ``RoiProcessor``. This
determines if feature values are saved to disk automatically. The default value is True,
but you might want to set it to False for your purposes. 

Added more functions for determining paths for consistency and using the DRY principle. 

### Changed
#### Major change: filepath structure for features
The structure of filepaths for features and feature criteria have been changed to
{feature_name}_feature.npy and {feature_name}_featurecriteria.npy. The reason for this
change is so that it's possible to determine which features and criteria have been saved
by inspecting filenames (whereas before only criteria was immediately identifiable). This
will cause backwards incompatibility because files on the old path will not be
recognized. To address this change, two supporting methods are provided called 
``identify_cellector_folders`` and ``update_feature_paths``. You can use ``identify...``
to get all folders that contain a cellector directory and ``update...`` to convert the
filepaths to the new structure. These functions are in cellector/io/operations. 
```python
from pathlib import Path
from cellector.io.operations import identify_cellector_folders, update_feature_paths
top_level_dir = Path(r"C:\Users\Andrew\Documents")
cellector_folders = identify_cellector_folders(top_level_dir)
update_feature_paths(cellector_folders)
```

#### Minor changes: 
Removed the "Control-c" key command for saving. You can save by clicking the button.
The IO module is broken down into a directory and is more organized. 

### Fixed
Updated maximum python version - some dependencies are not compatible with python 3.13 yet.