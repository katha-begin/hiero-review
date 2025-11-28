"""
Hiero Review Tool - Startup Script
===================================
This script is executed when Hiero starts via the custom launcher.
It initializes the project environment and registers the review tool menu.
"""
import os
import json

# Check if we're running inside Hiero
try:
    import hiero.core
    import hiero.ui
    HIERO_AVAILABLE = True
except ImportError:
    HIERO_AVAILABLE = False
    print("[HieroReview] Warning: Running outside of Hiero environment")


def get_project_settings() -> dict:
    """Get project settings from environment variables."""
    resolution_str = os.environ.get('HIERO_RESOLUTION', '[1920, 1080]')
    try:
        resolution = json.loads(resolution_str)
    except json.JSONDecodeError:
        resolution = [1920, 1080]
    
    return {
        'project_name': os.environ.get('HIERO_PROJECT_NAME', 'Untitled'),
        'project_root': os.environ.get('HIERO_PROJECT_ROOT', ''),
        'import_dir': os.environ.get('HIERO_IMPORT_DIR', ''),
        'export_dir': os.environ.get('HIERO_EXPORT_DIR', ''),
        'audio_dir': os.environ.get('HIERO_AUDIO_DIR', ''),
        'fps': float(os.environ.get('HIERO_FPS', '24.0')),
        'resolution': resolution,
        'color_space': os.environ.get('HIERO_COLOR_SPACE', 'ACES'),
    }


def initialize_project() -> None:
    """Initialize Hiero with project configuration from environment."""
    if not HIERO_AVAILABLE:
        return
    
    settings = get_project_settings()
    
    # Get or create project
    projects = hiero.core.projects()
    if not projects:
        project = hiero.core.newProject()
    else:
        project = projects[0]
    
    # Set project name
    project_name = f"{settings['project_name']}_Review"
    project.setName(project_name)
    
    print(f"[HieroReview] Initialized project: {project_name}")
    print(f"[HieroReview] Project root: {settings['project_root']}")
    print(f"[HieroReview] Import dir: {settings['import_dir']}")
    print(f"[HieroReview] Export dir: {settings['export_dir']}")
    print(f"[HieroReview] FPS: {settings['fps']}")


def register_review_tool() -> None:
    """Register the review tool in Hiero's menu bar."""
    if not HIERO_AVAILABLE:
        return

    try:
        # Import and register the review tool
        from src.ui import register_menu, show_review_tool_dialog

        if register_menu():
            print("[HieroReview] Menu registered: Pipeline > Shot Review Tool (Ctrl+Shift+R)")
        else:
            # Fallback: manual menu registration
            from PySide2.QtWidgets import QAction

            menu_bar = hiero.ui.mainWindow().menuBar()

            # Find or create Pipeline menu
            pipeline_menu = None
            for action in menu_bar.actions():
                if action.text() == "Pipeline":
                    pipeline_menu = action.menu()
                    break

            if pipeline_menu is None:
                pipeline_menu = menu_bar.addMenu("Pipeline")

            # Add Shot Review Tool action
            review_action = QAction("Shot Review Tool...", None)
            review_action.setShortcut("Ctrl+Shift+R")
            review_action.triggered.connect(show_review_tool_dialog)
            pipeline_menu.addAction(review_action)

            print("[HieroReview] Menu registered (fallback): Pipeline > Shot Review Tool")

    except Exception as e:
        print(f"[HieroReview] Failed to register menu: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main startup function."""
    print("[HieroReview] ========================================")
    print("[HieroReview] Hiero Review Tool - Startup")
    print("[HieroReview] ========================================")
    
    initialize_project()
    register_review_tool()
    
    print("[HieroReview] Startup complete")
    print("[HieroReview] ========================================")


# Execute on import (when Hiero loads this script)
if __name__ == '__main__' or HIERO_AVAILABLE:
    main()

