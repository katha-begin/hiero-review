"""
Hiero Review Tool - Auto Startup Script
========================================
This script is automatically loaded by Hiero from the Startup folder.
Place this folder in your ~/.nuke/Python/ directory.

Structure:
~/.nuke/Python/Startup/init.py  (this file)
~/.nuke/Python/hiero_review/    (the tool source)
"""
import sys
import os
from pathlib import Path

print("[HieroReview] ========================================")
print("[HieroReview] Initializing Hiero Review Tool...")
print("[HieroReview] ========================================")

# Find the hiero_review source directory
# It should be in the same Python folder or in HIERO_PLUGIN_PATH
possible_paths = [
    Path(__file__).parent.parent / "hiero_review" / "src",  # ~/.nuke/Python/hiero_review/src
    Path(__file__).parent.parent.parent / "src",            # Relative to project root
    Path(os.environ.get("HIERO_REVIEW_PATH", "")) / "src",  # From environment variable
]

# Also check HIERO_PLUGIN_PATH
plugin_path = os.environ.get("HIERO_PLUGIN_PATH", "")
if plugin_path:
    for p in plugin_path.split(os.pathsep):
        possible_paths.append(Path(p) / "src")
        possible_paths.append(Path(p))

# Find valid source path
src_path = None
for path in possible_paths:
    if path.exists() and (path / "ui").exists():
        src_path = path.parent  # We want parent so 'from src.ui import' works
        break

if src_path:
    # Add to Python path
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)
    print(f"[HieroReview] Added to path: {src_path_str}")
else:
    print("[HieroReview] Warning: Could not find hiero_review source directory")
    print("[HieroReview] Set HIERO_REVIEW_PATH environment variable to the tool location")

# Try to register the menu
try:
    import hiero.core
    import hiero.ui
    
    def on_startup():
        """Called when Hiero UI is ready."""
        try:
            from src.ui import register_menu, register_context_menu
            
            if register_menu():
                print("[HieroReview] Menu registered successfully")
            else:
                print("[HieroReview] Menu registration returned False")
            
            # Register context menu
            register_context_menu()
            print("[HieroReview] Context menu registered")
            
        except ImportError as e:
            print(f"[HieroReview] Import error: {e}")
        except Exception as e:
            print(f"[HieroReview] Error during registration: {e}")
    
    # Register for startup event
    hiero.core.events.registerInterest(
        hiero.core.events.EventType.kAfterNewProjectCreated,
        lambda event: on_startup()
    )
    
    # Also try immediate registration (in case project already exists)
    try:
        on_startup()
    except:
        pass
    
    print("[HieroReview] Startup script loaded")
    
except ImportError:
    print("[HieroReview] Running outside Hiero - skipping menu registration")

print("[HieroReview] ========================================")

