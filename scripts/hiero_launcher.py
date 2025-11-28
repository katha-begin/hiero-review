#!/usr/bin/env python
"""
Hiero Review Tool - Custom Launcher
====================================
Launches Hiero with pre-configured project settings.

Usage:
    python hiero_launcher.py [--project PROJECT_NAME] [--list] [--help]

Examples:
    python hiero_launcher.py                    # Uses default project
    python hiero_launcher.py --project SWA      # Uses SWA project config
    python hiero_launcher.py --list             # Lists available projects
"""
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path.home() / ".nuke" / "hiero_review_projects"


def list_available_projects() -> list:
    """List all available project configurations."""
    config_dir = get_config_dir()
    if not config_dir.exists():
        return []
    return [f.stem for f in config_dir.glob("*.json")]


def load_project_config(project_name: str) -> dict:
    """Load project configuration from JSON file."""
    config_dir = get_config_dir()
    config_file = config_dir / f"{project_name}.json"

    if not config_file.exists():
        # Fall back to default config
        config_file = config_dir / "default.json"
        if not config_file.exists():
            raise FileNotFoundError(
                f"Project config '{project_name}' not found and no default.json exists.\n"
                f"Please create a config file at: {config_dir}"
            )

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def setup_environment(config: dict) -> None:
    """Set environment variables from project config."""
    os.environ['HIERO_PROJECT_NAME'] = config.get('project_name', 'Untitled')
    os.environ['HIERO_PROJECT_ROOT'] = config.get('project_root', '')

    media_paths = config.get('media_paths', {})
    os.environ['HIERO_IMPORT_DIR'] = media_paths.get('import_dir', '')
    os.environ['HIERO_EXPORT_DIR'] = media_paths.get('export_dir', '')
    os.environ['HIERO_AUDIO_DIR'] = media_paths.get('audio_dir', '')

    settings = config.get('settings', {})
    os.environ['HIERO_FPS'] = str(settings.get('fps', 24.0))
    os.environ['HIERO_RESOLUTION'] = json.dumps(settings.get('resolution', [1920, 1080]))
    os.environ['HIERO_COLOR_SPACE'] = settings.get('color_space', 'ACES')

    # Set NUKE_PATH for Hiero to find our tools (HIERO_PLUGIN_PATH is deprecated)
    # Add our tool's Python/Startup folder to NUKE_PATH
    tool_root = Path(__file__).parent.parent
    startup_path = tool_root / 'Python' / 'Startup'

    # Get existing NUKE_PATH and append our paths
    existing_path = os.environ.get('NUKE_PATH', '')
    paths_to_add = [str(tool_root), str(startup_path)]

    if existing_path:
        new_path = os.pathsep.join([existing_path] + paths_to_add)
    else:
        new_path = os.pathsep.join(paths_to_add)

    os.environ['NUKE_PATH'] = new_path
    os.environ['HIERO_REVIEW_PATH'] = str(tool_root)  # Custom var for our tool

    print(f"NUKE_PATH set to: {new_path}")


def get_nuke_executable() -> str:
    """Find the Nuke executable path."""
    # Check environment variable first
    nuke_path = os.environ.get('NUKE_PATH', '')

    if sys.platform == 'win32':
        # Windows paths
        search_paths = [
            nuke_path,
            r'C:\Program Files\Nuke16.0v4',
            r'C:\Program Files\Nuke15.1v5',
            r'C:\Program Files\Nuke15.0v4',
        ]
        # Find Nuke executable (e.g., Nuke16.0.exe)
        exe_patterns = ['Nuke*.exe']
    else:
        # Linux/Mac paths
        search_paths = [
            nuke_path,
            '/usr/local/Nuke16.0v4',
            '/usr/local/Nuke15.1v5',
            '/opt/Nuke16.0v4',
        ]
        exe_patterns = ['Nuke*']

    for path in search_paths:
        if path:
            path_obj = Path(path)
            if path_obj.exists():
                for pattern in exe_patterns:
                    matches = list(path_obj.glob(pattern))
                    # Filter to find main Nuke executable (not NukeX, etc.)
                    for match in matches:
                        name = match.stem
                        # Match Nuke16.0, Nuke15.1, etc. (not NukeX, NukeAssist)
                        if match.is_file() and name.startswith('Nuke') and name[4:5].isdigit():
                            return str(match)

    raise FileNotFoundError(
        "Could not find Nuke executable.\n"
        "Please set NUKE_PATH environment variable to your Nuke installation directory.\n"
        "Example: set NUKE_PATH=C:\\Program Files\\Nuke16.0v4"
    )


def launch_hiero(config: dict, mode: str = 'hiero') -> None:
    """Launch Hiero (via Nuke --hiero).

    Note: Hiero loads Python scripts automatically from NUKE_PATH directories.
    Scripts in Python/Startup/ folders (init.py, menu.py) are auto-loaded.
    """
    nuke_exe = get_nuke_executable()

    # Build command: Nuke16.0.exe --hiero
    # No --python flag needed - Hiero auto-loads from NUKE_PATH
    cmd = [nuke_exe, f'--{mode}']

    print(f"Launching Hiero: {' '.join(cmd)}")
    subprocess.Popen(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Launch Hiero with project configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--project', '-p',
        default='default',
        help='Project name to load (default: "default")'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available project configurations'
    )
    parser.add_argument(
        '--player',
        action='store_true',
        help='Launch in Player mode instead of Hiero mode'
    )

    args = parser.parse_args()

    if args.list:
        projects = list_available_projects()
        if projects:
            print("Available projects:")
            for p in projects:
                print(f"  - {p}")
        else:
            print(f"No project configs found in: {get_config_dir()}")
        return

    # Determine launch mode
    mode = 'player' if args.player else 'hiero'

    try:
        print(f"Loading project config: {args.project}")
        config = load_project_config(args.project)

        print(f"Setting up environment for: {config.get('project_name', args.project)}")
        setup_environment(config)

        launch_hiero(config, mode=mode)
        print(f"{'Player' if args.player else 'Hiero'} launched successfully!")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

