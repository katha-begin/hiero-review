"""
Hiero Review Tool - Menu Registration
=====================================
This script registers the Review Tool menu in Hiero.
"""
import sys
import os
from pathlib import Path

# Ensure source path is available
tool_root = Path(__file__).parent.parent.parent
if str(tool_root) not in sys.path:
    sys.path.insert(0, str(tool_root))

try:
    import hiero.core
    import hiero.ui
    from PySide2.QtWidgets import QAction, QMenu
    
    # Global dialog reference
    _review_dialog = None
    
    def show_review_tool():
        """Show the Review Tool dialog."""
        global _review_dialog
        
        try:
            from src.ui import ReviewToolDialog
            
            if _review_dialog is None:
                _review_dialog = ReviewToolDialog(hiero.ui.mainWindow())
            
            _review_dialog.show()
            _review_dialog.raise_()
            _review_dialog.activateWindow()
            
        except ImportError as e:
            from PySide2.QtWidgets import QMessageBox
            QMessageBox.warning(
                hiero.ui.mainWindow(),
                "Review Tool Error",
                f"Could not load Review Tool:\n{e}\n\nCheck that HIERO_PLUGIN_PATH is set correctly."
            )
    
    def add_review_menu():
        """Add the Review Tool to Hiero's menu."""
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
        
        # Check if already added
        for action in pipeline_menu.actions():
            if "Review Tool" in action.text():
                return  # Already registered
        
        # Add separator and action
        pipeline_menu.addSeparator()
        
        review_action = QAction("Shot Review Tool...", pipeline_menu)
        review_action.setShortcut("Ctrl+Shift+R")
        review_action.setStatusTip("Open the Shot Review Tool for timeline creation")
        review_action.triggered.connect(show_review_tool)
        pipeline_menu.addAction(review_action)
        
        print("[HieroReview] Menu added: Pipeline > Shot Review Tool (Ctrl+Shift+R)")
    
    # Register when Hiero is ready
    hiero.core.events.registerInterest(
        hiero.core.events.EventType.kAfterNewProjectCreated,
        lambda event: add_review_menu()
    )
    
    # Try immediate registration
    try:
        if hiero.ui.mainWindow():
            add_review_menu()
    except:
        pass

except ImportError as e:
    print(f"[HieroReview] Not running in Hiero: {e}")

