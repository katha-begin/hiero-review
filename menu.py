"""
Hiero Review Tool - Menu Registration
=====================================
This script is auto-loaded by Hiero from NUKE_PATH.
Based on reference: uses hiero.ui.menuBar() directly.
"""
import sys
import os
from pathlib import Path

print("[HieroReview] menu.py loading...")


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


# Get tool root directory (where this menu.py file is located)
TOOL_ROOT = normalize_path(Path(__file__).parent.resolve())
print(f"[HieroReview] Tool root: {TOOL_ROOT}")

# Add tool root to Python path so 'src' module can be imported
tool_root_str = str(TOOL_ROOT)
if tool_root_str not in sys.path:
    sys.path.insert(0, tool_root_str)
    print(f"[HieroReview] Added to sys.path: {tool_root_str}")

# Global references to prevent garbage collection
_review_dialog = None
_review_controller = None


def show_review_tool():
    """Show the Review Tool dialog."""
    global _review_dialog, _review_controller

    print("[HieroReview] show_review_tool() called")

    try:
        from src.ui import ReviewToolDialog
        from src.ui.controller import ReviewToolController
        import hiero.ui

        if _review_dialog is None:
            parent = hiero.ui.mainWindow()
            _review_dialog = ReviewToolDialog(parent)
            # Create controller to wire up the dialog
            _review_controller = ReviewToolController(_review_dialog)
            print("[HieroReview] Created ReviewToolDialog with Controller")

        _review_dialog.show()
        _review_dialog.raise_()
        _review_dialog.activateWindow()
        print("[HieroReview] Dialog shown")

    except Exception as e:
        print(f"[HieroReview] Error showing dialog: {e}")
        import traceback
        traceback.print_exc()


def register_review_tool():
    """Register the review tool in Hiero menu - following reference pattern."""
    print("[HieroReview] register_review_tool() called")

    try:
        import hiero.ui

        # Get menu bar directly from hiero.ui (per reference)
        menu_bar = hiero.ui.menuBar()

        # Add Pipeline menu
        pipeline_menu = menu_bar.addMenu("Pipeline")

        # Add action
        action = pipeline_menu.addAction("Shot Review Tool")
        action.setShortcut("Ctrl+Shift+R")
        action.triggered.connect(show_review_tool)

        print("[HieroReview] Review tool registered in menu: Pipeline > Shot Review Tool")
        return True

    except Exception as e:
        print(f"[HieroReview] Failed to register menu: {e}")
        import traceback
        traceback.print_exc()
        return False


# Try to register when this module loads
try:
    import hiero.core
    import hiero.ui
    print("[HieroReview] hiero.core and hiero.ui imported successfully")

    # Register the menu
    register_review_tool()

except ImportError as e:
    print(f"[HieroReview] Not running in Hiero: {e}")
except Exception as e:
    print(f"[HieroReview] Unexpected error during setup: {e}")
    import traceback
    traceback.print_exc()

print("[HieroReview] menu.py finished loading")

