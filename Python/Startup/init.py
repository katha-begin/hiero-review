"""
Hiero Review Tool - Auto Startup Script (Python/Startup/init.py)
=================================================================
This script is automatically loaded by Hiero from the Startup folder.
NOTE: The main init.py is at the tool root. This one is a fallback.
"""
import sys
import os
from pathlib import Path

print("[HieroReview/Startup] ========================================")
print("[HieroReview/Startup] Initializing from Python/Startup/init.py")
print("[HieroReview/Startup] ========================================")

# The tool root is two levels up from Python/Startup/
TOOL_ROOT = Path(__file__).parent.parent.parent.resolve()
print(f"[HieroReview/Startup] Tool root: {TOOL_ROOT}")

# Add tool root to Python path
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))
    print(f"[HieroReview/Startup] Added to sys.path: {TOOL_ROOT}")

# Set environment variable
os.environ['HIERO_REVIEW_PATH'] = str(TOOL_ROOT)

# Now import and run the main menu.py from tool root
try:
    # Import the root menu.py which handles everything
    import menu
    print("[HieroReview/Startup] Loaded root menu.py")
except ImportError as e:
    print(f"[HieroReview/Startup] Could not import root menu.py: {e}")
    # Fallback: try to register directly
    try:
        import hiero.core
        import hiero.ui
        from src.ui import register_menu, register_context_menu

        def on_startup():
            if register_menu():
                print("[HieroReview/Startup] Menu registered")
            register_context_menu()

        hiero.core.events.registerInterest(
            hiero.core.events.EventType.kAfterNewProjectCreated,
            lambda event: on_startup()
        )
        on_startup()
    except Exception as e2:
        print(f"[HieroReview/Startup] Fallback registration failed: {e2}")

print("[HieroReview/Startup] ========================================")

