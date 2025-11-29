"""
Hiero Review Tool - Menu Registration
=====================================
This script is auto-loaded by Hiero from NUKE_PATH.
Place this file in a directory listed in NUKE_PATH.
"""
import sys
import os
from pathlib import Path

print("[HieroReview] menu.py loading...")

# Get tool root directory (where this menu.py file is located)
TOOL_ROOT = Path(__file__).parent.resolve()
print(f"[HieroReview] Tool root: {TOOL_ROOT}")

# Add tool root to Python path so 'src' module can be imported
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))
    print(f"[HieroReview] Added to sys.path: {TOOL_ROOT}")

try:
    import hiero.core
    import hiero.ui

    # Try to import Qt - Nuke/Hiero may use PySide2 or PySide6
    try:
        from PySide2.QtWidgets import QAction, QMenu
        print("[HieroReview] Using PySide2")
    except ImportError:
        try:
            from PySide6.QtWidgets import QAction, QMenu
            from PySide6.QtGui import QAction as QAction6
            # In PySide6, QAction moved to QtGui
            try:
                from PySide6.QtGui import QAction
            except ImportError:
                pass
            print("[HieroReview] Using PySide6")
        except ImportError:
            # Last resort: try to get Qt from Nuke
            try:
                from nukescripts import panels
                from PySide2.QtWidgets import QAction, QMenu
            except ImportError:
                raise ImportError("Could not import PySide2 or PySide6")

    print("[HieroReview] Hiero modules imported successfully")
    
    # Global dialog reference to prevent garbage collection
    _review_dialog = None
    
    def show_review_tool():
        """Show the Review Tool dialog."""
        global _review_dialog
        
        print("[HieroReview] show_review_tool() called")
        
        try:
            from src.ui import ReviewToolDialog
            
            if _review_dialog is None:
                parent = hiero.ui.mainWindow()
                _review_dialog = ReviewToolDialog(parent)
                print("[HieroReview] Created new ReviewToolDialog")
            
            _review_dialog.show()
            _review_dialog.raise_()
            _review_dialog.activateWindow()
            print("[HieroReview] Dialog shown")
            
        except ImportError as e:
            print(f"[HieroReview] Import error: {e}")
            import traceback
            traceback.print_exc()

            try:
                from PySide2.QtWidgets import QMessageBox
            except ImportError:
                from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                hiero.ui.mainWindow(),
                "Review Tool Error",
                f"Could not load Review Tool:\n{e}\n\n"
                f"Tool root: {TOOL_ROOT}\n"
                f"sys.path includes tool root: {str(TOOL_ROOT) in sys.path}"
            )
        except Exception as e:
            print(f"[HieroReview] Error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_review_menu():
        """Add the Review Tool to Hiero's menu."""
        print("[HieroReview] add_review_menu() called")
        
        try:
            menu_bar = hiero.ui.mainWindow().menuBar()
            
            # Find or create Pipeline menu
            pipeline_menu = None
            for action in menu_bar.actions():
                if action.text() == "Pipeline":
                    pipeline_menu = action.menu()
                    break
            
            if pipeline_menu is None:
                # Insert before Help menu
                help_action = None
                for action in menu_bar.actions():
                    if action.text() == "Help":
                        help_action = action
                        break
                
                pipeline_menu = QMenu("Pipeline", menu_bar)
                if help_action:
                    menu_bar.insertMenu(help_action, pipeline_menu)
                else:
                    menu_bar.addMenu(pipeline_menu)
                print("[HieroReview] Created Pipeline menu")
            
            # Check if already added
            for action in pipeline_menu.actions():
                if "Review Tool" in action.text():
                    print("[HieroReview] Menu already registered")
                    return
            
            # Add separator and action
            pipeline_menu.addSeparator()
            
            review_action = QAction("Shot Review Tool...", pipeline_menu)
            review_action.setShortcut("Ctrl+Shift+R")
            review_action.setStatusTip("Open the Shot Review Tool for timeline creation")
            review_action.triggered.connect(show_review_tool)
            pipeline_menu.addAction(review_action)
            
            print("[HieroReview] Menu added: Pipeline > Shot Review Tool (Ctrl+Shift+R)")
            
        except Exception as e:
            print(f"[HieroReview] Error adding menu: {e}")
            import traceback
            traceback.print_exc()
    
    # Register for startup event
    def on_startup(event):
        print(f"[HieroReview] Startup event received: {event}")
        add_review_menu()
    
    hiero.core.events.registerInterest(
        hiero.core.events.EventType.kAfterNewProjectCreated,
        on_startup
    )
    print("[HieroReview] Registered kAfterNewProjectCreated event")
    
    # Also try immediate registration
    try:
        main_window = hiero.ui.mainWindow()
        if main_window:
            print("[HieroReview] Main window exists, registering menu immediately")
            add_review_menu()
        else:
            print("[HieroReview] Main window not ready yet, will wait for event")
    except Exception as e:
        print(f"[HieroReview] Could not register immediately: {e}")

except ImportError as e:
    print(f"[HieroReview] Not running in Hiero: {e}")
except Exception as e:
    print(f"[HieroReview] Unexpected error during setup: {e}")
    import traceback
    traceback.print_exc()

print("[HieroReview] menu.py finished loading")

