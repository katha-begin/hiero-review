#!/usr/bin/env python
"""
Hiero Review Tool - Custom Launcher
====================================
Launches Hiero with pre-configured project settings.
All environment variables are set from config file before launch.

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


def normalize_path(path: Path) -> Path:
    """Normalize path - convert UNC paths to drive letters on Windows.

    On Windows, converts paths like:
        \\\\server\\ppr_dev_t\\... -> T:\\...
        \\\\10.100.131.250\\ppr_dev_t\\... -> T:\\...
    """
    if sys.platform != 'win32':
        return path

    path_str = str(path)

    # Map of UNC share names to drive letters
    # Add more mappings as needed
    unc_to_drive = {
        'ppr_dev_t': 'T:',
        'ppr_dev_s': 'S:',
        'ppr_dev_p': 'P:',
    }

    # Check if it's a UNC path (starts with \\ or //)
    if path_str.startswith('\\\\') or path_str.startswith('//'):
        # Split the path: \\server\share\rest\of\path
        parts = path_str.replace('/', '\\').lstrip('\\').split('\\')
        if len(parts) >= 2:
            server = parts[0]
            share = parts[1].lower()
            rest = '\\'.join(parts[2:]) if len(parts) > 2 else ''

            # Check if we have a drive mapping for this share
            if share in unc_to_drive:
                drive = unc_to_drive[share]
                new_path = f"{drive}\\{rest}" if rest else drive
                print(f"[Launcher] Converted UNC path: {path_str} -> {new_path}")
                return Path(new_path)

    return path


# Get tool root directory (parent of scripts folder)
TOOL_ROOT = normalize_path(Path(__file__).parent.parent.resolve())


def get_config_dir() -> Path:
    """Get the configuration directory path.

    First checks the tool's config folder, then falls back to user's .nuke folder.
    """
    # Check tool's local config folder first
    local_config = TOOL_ROOT / "config"
    if local_config.exists():
        return local_config

    # Fall back to user's .nuke folder
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
                f"Config directories checked:\n"
                f"  - {TOOL_ROOT / 'config'}\n"
                f"  - {Path.home() / '.nuke' / 'hiero_review_projects'}"
            )

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def setup_environment(config: dict) -> None:
    """Set ALL environment variables from project config before launching Hiero.

    This sets:
    - Project-specific variables (HIERO_PROJECT_NAME, HIERO_PROJECT_ROOT, etc.)
    - NUKE_PATH for Hiero to find our tool
    - Any custom environment variables from config
    - Extra Python paths
    """
    print("\n=== Setting up environment ===")

    # 1. Project-specific environment variables
    os.environ['HIERO_PROJECT_NAME'] = config.get('project_name', 'Untitled')
    os.environ['HIERO_PROJECT_ROOT'] = config.get('project_root', '')
    print(f"  HIERO_PROJECT_NAME = {os.environ['HIERO_PROJECT_NAME']}")
    print(f"  HIERO_PROJECT_ROOT = {os.environ['HIERO_PROJECT_ROOT']}")

    media_paths = config.get('media_paths', {})
    os.environ['HIERO_IMPORT_DIR'] = media_paths.get('import_dir', '')
    os.environ['HIERO_EXPORT_DIR'] = media_paths.get('export_dir', '')
    os.environ['HIERO_AUDIO_DIR'] = media_paths.get('audio_dir', '')

    settings = config.get('settings', {})
    os.environ['HIERO_FPS'] = str(settings.get('fps', 24.0))
    os.environ['HIERO_RESOLUTION'] = json.dumps(settings.get('resolution', [1920, 1080]))
    os.environ['HIERO_COLOR_SPACE'] = settings.get('color_space', 'ACES')

    # 2. Set HIERO_REVIEW_PATH (location of this tool)
    os.environ['HIERO_REVIEW_PATH'] = str(TOOL_ROOT)
    print(f"  HIERO_REVIEW_PATH = {TOOL_ROOT}")

    # 3. Build NUKE_PATH for Hiero to find our tool
    startup_path = TOOL_ROOT / 'Python' / 'Startup'

    # Start with our tool paths
    nuke_paths = [str(TOOL_ROOT), str(startup_path)]

    # Add extra paths from config
    launcher_config = config.get('launcher', {})
    extra_nuke_paths = launcher_config.get('extra_nuke_paths', [])
    for path in extra_nuke_paths:
        expanded = os.path.expandvars(os.path.expanduser(path))
        if expanded and expanded not in nuke_paths:
            nuke_paths.append(expanded)

    # Set NUKE_PATH (don't use existing system NUKE_PATH - start fresh)
    os.environ['NUKE_PATH'] = os.pathsep.join(nuke_paths)
    print(f"  NUKE_PATH = {os.environ['NUKE_PATH']}")

    # 4. Add extra Python paths
    extra_python_paths = launcher_config.get('extra_python_paths', [])
    for path in extra_python_paths:
        expanded = os.path.expandvars(os.path.expanduser(path))
        if expanded and expanded not in sys.path:
            sys.path.insert(0, expanded)
            print(f"  Added to PYTHONPATH: {expanded}")

    # 5. Set any custom environment variables from config
    custom_env = launcher_config.get('environment', {})
    for key, value in custom_env.items():
        expanded_value = os.path.expandvars(os.path.expanduser(str(value)))
        os.environ[key] = expanded_value
        print(f"  {key} = {expanded_value}")

    print("=== Environment setup complete ===\n")


def get_nuke_executable(config: dict) -> str:
    """Find the Nuke executable path.

    Priority:
    1. launcher.nuke_executable from config file
    2. Auto-detect from common installation paths
    """
    # Check config first
    launcher_config = config.get('launcher', {})
    config_exe = launcher_config.get('nuke_executable', '')

    if config_exe:
        expanded = os.path.expandvars(os.path.expanduser(config_exe))
        if Path(expanded).exists():
            return expanded
        print(f"Warning: Configured nuke_executable not found: {expanded}")

    # Auto-detect from common paths
    if sys.platform == 'win32':
        search_paths = [
            r'C:\Program Files\Nuke16.0v4',
            r'C:\Program Files\Nuke15.1v5',
            r'C:\Program Files\Nuke15.0v4',
        ]
        exe_patterns = ['Nuke*.exe']
    else:
        search_paths = [
            '/usr/local/Nuke16.0v4',
            '/usr/local/Nuke15.1v5',
            '/opt/Nuke16.0v4',
        ]
        exe_patterns = ['Nuke*']

    for path in search_paths:
        path_obj = Path(path)
        if path_obj.exists():
            for pattern in exe_patterns:
                matches = list(path_obj.glob(pattern))
                for match in matches:
                    name = match.stem
                    # Match Nuke16.0, Nuke15.1, etc. (not NukeX, NukeAssist)
                    if match.is_file() and name.startswith('Nuke') and name[4:5].isdigit():
                        return str(match)

    raise FileNotFoundError(
        "Could not find Nuke executable.\n"
        "Please set 'launcher.nuke_executable' in your project config file.\n"
        f"Config file location: {get_config_dir()}/default.json\n\n"
        "Example config:\n"
        '  "launcher": {\n'
        '    "nuke_executable": "C:/Program Files/Nuke16.0v4/Nuke16.0.exe"\n'
        '  }'
    )


def launch_hiero(config: dict, mode: str = 'hiero') -> None:
    """Launch Hiero (via Nuke --hiero).

    Note: Hiero loads Python scripts automatically from NUKE_PATH directories.
    Scripts in Python/Startup/ folders (init.py, menu.py) are auto-loaded.
    """
    nuke_exe = get_nuke_executable(config)

    # Build command: Nuke16.0.exe --hiero
    # No --python flag needed - Hiero auto-loads from NUKE_PATH
    cmd = [nuke_exe, f'--{mode}']

    print(f"\n=== Launching Hiero ===")
    print(f"Executable: {nuke_exe}")
    print(f"Mode: {mode}")
    print(f"Command: {' '.join(cmd)}")
    print("========================\n")

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

