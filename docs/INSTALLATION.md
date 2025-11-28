# Installation Guide

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (CentOS 7+, Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Hiero/Nuke Studio**: Version 13.0 or higher

### Python Dependencies

The tool requires the following Python packages:

- PySide2 or PySide6 (included with Hiero)
- pytest (for testing only)

## Installation Methods

### Method 1: Standard Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/hiero-review.git
   cd hiero-review
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Hiero environment**:
   
   Add the tool to your Hiero startup:
   
   **Option A**: Copy to Hiero's plugin directory
   ```bash
   # Windows
   copy -r src %USERPROFILE%\.nuke\Python\hiero_review
   
   # Linux/Mac
   cp -r src ~/.nuke/Python/hiero_review
   ```
   
   **Option B**: Add to HIERO_PLUGIN_PATH
   ```bash
   # Windows (PowerShell)
   $env:HIERO_PLUGIN_PATH = "C:\path\to\hiero-review\src"
   
   # Linux/Mac
   export HIERO_PLUGIN_PATH="/path/to/hiero-review/src"
   ```

### Method 2: Using the Custom Launcher

The custom launcher automatically configures the environment:

1. **Windows**:
   ```batch
   hiero_launcher.bat
   ```

2. **Linux/Mac**:
   ```bash
   python hiero_launcher.py
   ```

## Configuration

### Project Setup

1. Create a project configuration file in `config/projects/`:

   ```json
   {
     "project_name": "MyProject",
     "project_root": "/path/to/project",
     "media_paths": {
       "renders": "renders",
       "plates": "plates",
       "audio": "audio"
     },
     "departments": ["comp", "lighting", "fx"],
     "naming_convention": {
       "episode_pattern": "Ep\\d{2}",
       "sequence_pattern": "sq\\d{4}",
       "shot_pattern": "SH\\d{4}"
     }
   }
   ```

2. Set the default project in `config/default.json`:

   ```json
   {
     "default_project": "MyProject"
   }
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HIERO_REVIEW_CONFIG` | Path to config directory | `./config` |
| `HIERO_REVIEW_CACHE` | Path to cache directory | `~/.hiero_review/cache` |
| `HIERO_REVIEW_LOG_LEVEL` | Logging level | `INFO` |

## Verification

### Test Installation

1. Launch Hiero using the custom launcher
2. Open the Script Editor (Window > Script Editor)
3. Run:
   ```python
   from src.core import VersionManager
   print(VersionManager.format_version(1))  # Should print: v001
   ```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### Common Issues

**Import Error: No module named 'src'**
- Ensure the tool directory is in your Python path
- Use the custom launcher which sets up paths automatically

**Qt/PySide not found**
- The tool uses Hiero's built-in PySide
- Make sure you're running within Hiero, not standalone Python

**Permission denied on cache directory**
- Check write permissions for `~/.hiero_review/`
- Set `HIERO_REVIEW_CACHE` to a writable location

### Getting Help

- Check the [FAQ](FAQ.md)
- Open an issue on GitHub
- Contact support

