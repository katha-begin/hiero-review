# API Reference

## Core Modules

### VersionManager

Static methods for version string manipulation.

```python
from src.core import VersionManager

# Parse version string
version_num = VersionManager.parse_version("v001")  # Returns: 1

# Format version number
version_str = VersionManager.format_version(5)  # Returns: "v005"
version_str = VersionManager.format_version(5, 4)  # Returns: "v0005"

# Sort versions
sorted_vers = VersionManager.sort_versions(["v003", "v001", "v002"])
# Returns: ["v001", "v002", "v003"]

# Compare versions
result = VersionManager.compare_versions("v001", "v002")  # Returns: -1

# Get latest version
latest = VersionManager.get_latest_version(["v001", "v003", "v002"])
# Returns: "v003"

# Increment/decrement
next_ver = VersionManager.increment_version("v001")  # Returns: "v002"
prev_ver = VersionManager.decrement_version("v005")  # Returns: "v004"
```

### ProjectScanner

Scans project directories for media files.

```python
from src.core import ProjectScanner

scanner = ProjectScanner("/path/to/project")

# Scan episodes
episodes = scanner.scan_episodes()  # Returns: ["Ep01", "Ep02", ...]

# Scan sequences in episode
sequences = scanner.scan_sequences("Ep01")  # Returns: ["sq0010", "sq0020", ...]

# Scan shots in sequence
shots = scanner.scan_shots("Ep01", "sq0010")  # Returns: ["SH0010", "SH0020", ...]

# Full scan
result = scanner.scan_full(["Ep01"])  # Returns: ScanResult dataclass
```

### TimelineBuilder

Builds Hiero timelines from scanned data.

```python
from src.core import TimelineBuilder, ProjectScanner

scanner = ProjectScanner("/path/to/project")
builder = TimelineBuilder(scanner)

# Build timeline
result = builder.build_timeline(
    episode="Ep01",
    sequence="sq0010",
    department="comp",
    version="latest"
)
```

### CacheManager

Two-tier caching system.

```python
from src.core import CacheManager

cache = CacheManager()

# Store value
cache.set({"data": "value"}, "key", "subkey")

# Retrieve value
value = cache.get("key", "subkey")

# Invalidate
cache.invalidate("key", "subkey")

# Clear all
cache.clear()
```

## Models

### ProjectConfig

```python
from src.models import ProjectConfig, MediaPaths

config = ProjectConfig(
    project_name="MyProject",
    project_root="/path/to/project",
    media_paths=MediaPaths(
        renders="renders",
        plates="plates",
        audio="audio"
    )
)
```

### ShotInfo

```python
from src.models import ShotInfo, DepartmentInfo

shot = ShotInfo(
    episode="Ep01",
    sequence="sq0010",
    shot="SH0010",
    departments={
        "comp": DepartmentInfo(
            name="comp",
            versions=["v001", "v002"],
            current_version="v002"
        )
    }
)

# Properties
shot.full_name  # "Ep01_sq0010_SH0010"
```

## Utilities

### Path Parser

```python
from src.utils.path_parser import (
    parse_shot_path,
    extract_episode,
    extract_sequence,
    extract_shot,
    parse_frame_number
)

# Parse full path
result = parse_shot_path("/project/Ep01/sq0010/SH0010/comp/v001/file.mov")
# Returns: {"ep": "Ep01", "seq": "sq0010", "shot": "SH0010", "dept": "comp"}

# Extract components
ep = extract_episode(path)    # "Ep01"
seq = extract_sequence(path)  # "sq0010"
shot = extract_shot(path)     # "SH0010"

# Parse frame number
frame = parse_frame_number("file.1001.exr")  # 1001
```

### Validators

```python
from src.utils.validators import (
    validate_naming_convention,
    validate_version_format,
    validate_frame_sequence,
    ValidationReport
)

# Validate naming
is_valid = validate_naming_convention("Ep01_sq0010_SH0010_comp_v001.mov")

# Validate version
is_valid = validate_version_format("v001")

# Validate sequence
result = validate_frame_sequence(["file.1001.exr", "file.1002.exr"])
# Returns: {"complete": True, "missing": [], "start": 1001, "end": 1002}
```

## UI Components

### ReviewToolDialog

Main dialog window.

```python
from src.ui import ReviewToolDialog

dialog = ReviewToolDialog(parent=None)
dialog.show()
```

### Menu Integration

```python
from src.ui import register_menu

# Register in Hiero menu
register_menu()
```

