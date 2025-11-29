"""
Hiero Review Tool - Init Script
===============================
This script is auto-loaded by Hiero/Nuke from NUKE_PATH.
It sets up the environment for the Review Tool.
"""
import sys
import os
from pathlib import Path

print("[HieroReview] init.py loading...")


def normalize_path(path: Path) -> Path:
    """Normalize path - convert UNC paths to drive letters on Windows."""
    if sys.platform != 'win32':
        return path

    path_str = str(path)

    # Map of UNC share names to drive letters
    unc_to_drive = {
        'ppr_dev_t': 'T:',
        'ppr_dev_s': 'S:',
        'ppr_dev_p': 'P:',
    }

    # Check if it's a UNC path (starts with \\ or //)
    if path_str.startswith('\\\\') or path_str.startswith('//'):
        parts = path_str.replace('/', '\\').lstrip('\\').split('\\')
        if len(parts) >= 2:
            share = parts[1].lower()
            rest = '\\'.join(parts[2:]) if len(parts) > 2 else ''

            if share in unc_to_drive:
                drive = unc_to_drive[share]
                new_path = f"{drive}\\{rest}" if rest else drive
                print(f"[HieroReview] Converted UNC: {path_str} -> {new_path}")
                return Path(new_path)

    return path


# Get tool root directory (where this init.py file is located)
TOOL_ROOT = normalize_path(Path(__file__).parent.resolve())

# Add tool root to Python path so 'src' module can be imported
tool_root_str = str(TOOL_ROOT)
if tool_root_str not in sys.path:
    sys.path.insert(0, tool_root_str)
    print(f"[HieroReview] Added to sys.path: {tool_root_str}")

# Set environment variable for other scripts to find the tool
os.environ['HIERO_REVIEW_PATH'] = tool_root_str

print(f"[HieroReview] Tool initialized at: {TOOL_ROOT}")
print("[HieroReview] init.py finished loading")

