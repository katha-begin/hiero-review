"""
Menu Integration Module
========================
Integration of the Review Tool into Hiero's menu system.
"""
import os
from typing import Optional, Callable

# Try to import Hiero
try:
    import hiero.core
    import hiero.ui
    from hiero.ui import findMenuAction, insertMenuAction, registerAction
    HIERO_AVAILABLE = True
except ImportError:
    HIERO_AVAILABLE = False


# Global reference to keep dialog alive
_dialog_instance = None


def get_dialog():
    """Get or create the dialog instance."""
    global _dialog_instance
    
    if _dialog_instance is None:
        from .main_dialog import ReviewToolDialog
        # Use Hiero main window as parent if available
        parent = None
        if HIERO_AVAILABLE:
            parent = hiero.ui.mainWindow()
        _dialog_instance = ReviewToolDialog(parent)
    
    return _dialog_instance


def show_review_tool_dialog():
    """Show the Review Tool dialog."""
    dialog = get_dialog()
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def close_review_tool_dialog():
    """Close the Review Tool dialog."""
    global _dialog_instance
    if _dialog_instance:
        _dialog_instance.close()
        _dialog_instance = None


class ReviewToolAction:
    """
    Action class for Hiero menu integration.
    """
    def __init__(self):
        self._action = None
    
    def register(self) -> bool:
        """Register the action in Hiero's menu."""
        if not HIERO_AVAILABLE:
            print("[ReviewTool] Hiero not available, skipping menu registration")
            return False
        
        try:
            from PySide2.QtWidgets import QAction
            from PySide2.QtGui import QKeySequence
            
            # Create action
            self._action = QAction("Shot Review Tool...", None)
            self._action.setShortcut(QKeySequence("Ctrl+Shift+R"))
            self._action.setStatusTip("Open the Shot Review Tool for timeline creation")
            self._action.triggered.connect(show_review_tool_dialog)
            
            # Find the Python menu or create Pipeline menu
            menu_bar = hiero.ui.mainWindow().menuBar()
            
            # Try to find existing Python menu
            python_menu = None
            for action in menu_bar.actions():
                if action.text() == "Python":
                    python_menu = action.menu()
                    break
            
            # If not found, look for a Pipeline menu or create one
            if python_menu is None:
                for action in menu_bar.actions():
                    if "Pipeline" in action.text():
                        python_menu = action.menu()
                        break
            
            # Create Pipeline menu if neither exists
            if python_menu is None:
                python_menu = menu_bar.addMenu("Pipeline")
            
            # Add our action
            python_menu.addAction(self._action)
            
            print("[ReviewTool] Menu registered successfully")
            return True
            
        except Exception as e:
            print(f"[ReviewTool] Failed to register menu: {e}")
            return False
    
    def unregister(self) -> bool:
        """Unregister the action from Hiero's menu."""
        if self._action:
            self._action.setParent(None)
            self._action = None
            return True
        return False


# Global action instance
_action_instance: Optional[ReviewToolAction] = None


def register_menu() -> bool:
    """Register the Review Tool menu item."""
    global _action_instance
    
    if _action_instance is None:
        _action_instance = ReviewToolAction()
    
    return _action_instance.register()


def unregister_menu() -> bool:
    """Unregister the Review Tool menu item."""
    global _action_instance
    
    if _action_instance:
        result = _action_instance.unregister()
        _action_instance = None
        return result
    return False


def register_on_startup():
    """
    Register menu when Hiero is ready.
    Call this from startup.py or init.py.
    """
    if HIERO_AVAILABLE:
        # Use callback for when Hiero is ready
        hiero.core.events.registerInterest(
            hiero.core.events.EventType.kAfterNewProjectCreated,
            lambda event: register_menu()
        )
        # Also try immediate registration
        register_menu()
    else:
        print("[ReviewTool] Hiero not available")

