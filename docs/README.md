# Hiero Timeline Review Tool

A Python-based automation extension for Foundry's Hiero/Nuke Studio that automates VFX review timeline creation.

## Features

- **Automated Timeline Building**: Automatically scan project directories and build review timelines
- **Version Management**: Navigate between versions (previous/next/latest)
- **Department Switching**: Toggle between different department outputs (comp, lighting, FX, etc.)
- **Audio Synchronization**: Automatically match and sync audio files
- **Image Sequence Support**: Handle EXR, DPX, and other image sequences
- **Caching**: Two-tier caching (memory + disk) for fast repeated scans
- **Qt-based UI**: Modern dark-themed interface matching Hiero's look

## Installation

### Requirements

- Python 3.8+
- Foundry Hiero/Nuke Studio 13.0+
- PySide2 or PySide6 (included with Hiero)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hiero-review.git
   cd hiero-review
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your project in `config/projects/`:
   ```json
   {
     "project_name": "MyProject",
     "project_root": "/path/to/project",
     "media_paths": {
       "renders": "renders",
       "plates": "plates",
       "audio": "audio"
     }
   }
   ```

4. Launch Hiero with the tool:
   ```bash
   # Windows
   hiero_launcher.bat
   
   # Linux/Mac
   python hiero_launcher.py
   ```

## Usage

### Quick Start

1. Launch Hiero using the custom launcher
2. Go to **Tools > Review Tool** in the menu
3. Select your project, episode, and sequence
4. Choose department and version preferences
5. Click **Build Timeline**

### Version Navigation

- Use the version controls to navigate between versions
- **Previous**: Go to previous version
- **Next**: Go to next version
- **Latest**: Jump to latest version

### Department Switching

- Select shots in the timeline
- Right-click and choose **Switch Department**
- Select the target department

## Project Structure

```
hiero-review/
├── config/                 # Configuration files
│   └── projects/          # Project-specific configs
├── src/
│   ├── config/            # Configuration management
│   ├── core/              # Core business logic
│   ├── models/            # Data models
│   ├── ui/                # Qt-based UI components
│   └── utils/             # Utility functions
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── resources/             # Icons and resources
```

## Configuration

### Project Configuration

Create a JSON file in `config/projects/` for each project:

```json
{
  "project_name": "ProjectName",
  "project_root": "/path/to/project",
  "media_paths": {
    "renders": "renders",
    "plates": "plates",
    "audio": "audio"
  },
  "departments": ["comp", "lighting", "fx", "anim"],
  "naming_convention": {
    "episode_pattern": "Ep\\d{2}",
    "sequence_pattern": "sq\\d{4}",
    "shot_pattern": "SH\\d{4}"
  }
}
```

### User Preferences

User preferences are stored in `~/.hiero_review/config.json`:

- `last_project`: Last used project
- `recent_projects`: List of recent projects
- `default_department`: Default department selection
- `auto_refresh`: Enable/disable auto-refresh

## API Reference

See [API.md](API.md) for detailed API documentation.

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_version_manager.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

