"""
Review Tool Controller
=======================
Controller that wires the UI to the business logic (file scanner, config, etc.)
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Qt imports with fallback
try:
    from PySide2.QtCore import QObject, Signal, Slot
except ImportError:
    try:
        from PySide6.QtCore import QObject, Signal, Slot
    except ImportError:
        class QObject:
            pass
        def Signal(*args):
            return None
        def Slot(*args):
            def decorator(func):
                return func
            return decorator

from .main_dialog import ReviewToolDialog
from ..core.file_scanner import ProjectScanner
from ..config.config_manager import ConfigManager
from ..config.project_config import list_available_projects, get_config_dir


def get_tool_root() -> Path:
    """Get the tool root directory."""
    # Go up from src/ui/controller.py to tool root
    return Path(__file__).parent.parent.parent.resolve()


class ReviewToolController(QObject):
    """
    Controller that connects ReviewToolDialog to business logic.

    Responsibilities:
    - Load project configurations
    - Scan file system for episodes/sequences/shots
    - Handle UI events and update the view
    """

    def __init__(self, dialog: ReviewToolDialog, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.dialog = dialog
        self.config_manager = ConfigManager()
        self.scanner: Optional[ProjectScanner] = None
        self.current_project_root: Optional[Path] = None
        self._project_configs: Dict[str, Dict[str, Any]] = {}

        self._connect_signals()
        self._initialize()
    
    def _connect_signals(self) -> None:
        """Connect dialog signals to controller slots."""
        # Project config changed
        self.dialog.project_combo.currentTextChanged.connect(self._on_project_changed)

        # Refresh projects button
        self.dialog.refresh_projects_btn.clicked.connect(self._load_projects)

        # Browse button - use existing connection but also trigger scan
        original_browse = self.dialog._on_browse
        def browse_and_scan():
            original_browse()
            self._on_root_changed()
        self.dialog.browse_btn.clicked.disconnect()
        self.dialog.browse_btn.clicked.connect(browse_and_scan)

        # Root path Enter key - trigger scan
        self.dialog.root_path_edit.returnPressed.connect(self._on_root_changed)

        # Episode changed
        self.dialog.episode_combo.currentTextChanged.connect(self._on_episode_changed)

        # Build button
        self.dialog.build_requested.connect(self._on_build_timeline)
    
    def _initialize(self) -> None:
        """Initialize the controller and load initial data."""
        self.dialog.log_message("Initializing Review Tool...", "info")
        self._load_projects()
    
    def _load_projects(self) -> None:
        """Load available project configurations from multiple locations."""
        self.dialog.log_message("Loading project configurations...", "info")

        try:
            projects = []
            self._project_configs = {}

            # 1. Load from tool's local config folder
            tool_config_dir = get_tool_root() / "config"
            if tool_config_dir.exists():
                for config_file in tool_config_dir.glob("*.json"):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        name = config_file.stem
                        self._project_configs[name] = data
                        projects.append(name)
                        self.dialog.log_message(f"  Loaded: {name} (from tool config)", "info")
                    except Exception as e:
                        self.dialog.log_message(f"  Error loading {config_file.name}: {e}", "warning")

            # 2. Load from ~/.nuke/hiero_review_projects/
            user_config_dir = get_config_dir()
            if user_config_dir.exists():
                for config_file in user_config_dir.glob("*.json"):
                    try:
                        name = config_file.stem
                        if name not in self._project_configs:  # Don't override local
                            with open(config_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            self._project_configs[name] = data
                            projects.append(name)
                            self.dialog.log_message(f"  Loaded: {name} (from user config)", "info")
                    except Exception as e:
                        self.dialog.log_message(f"  Error loading {config_file.name}: {e}", "warning")

            if not projects:
                projects = ["default"]
                self.dialog.log_message("No project configs found", "warning")

            self.dialog.set_projects(sorted(projects))
            self.dialog.log_message(f"Loaded {len(projects)} project(s)", "info")

            # Load last used project
            last_project = self.config_manager.get("last_project", "default")
            index = self.dialog.project_combo.findText(last_project)
            if index >= 0:
                self.dialog.project_combo.setCurrentIndex(index)

        except Exception as e:
            self.dialog.log_message(f"Error loading projects: {e}", "error")
            import traceback
            traceback.print_exc()
    
    def _on_project_changed(self, project_name: str) -> None:
        """Handle project selection change."""
        if not project_name:
            return

        self.dialog.log_message(f"Loading project: {project_name}", "info")

        try:
            # Load project config from our cached configs
            config = self._project_configs.get(project_name, {})

            if config:
                # Get root path - try different keys
                root_path = config.get("project_root", "")
                scene_path = config.get("media_paths", {}).get("import_dir", "")

                # For launcher config format
                if not root_path and not scene_path:
                    root_path = config.get("project", {}).get("root", "")

                # Use scene_path if available, otherwise project_root
                scan_path = scene_path or root_path

                self.dialog.log_message(f"  project_root: {root_path}", "info")
                self.dialog.log_message(f"  import_dir: {scene_path}", "info")
                self.dialog.log_message(f"  scan_path: {scan_path}", "info")

                if scan_path:
                    self.dialog.root_path_edit.setText(scan_path)
                    self._scan_root(scan_path)
                else:
                    self.dialog.log_message("No root path in config - use Browse to set", "warning")
            else:
                self.dialog.log_message(f"Config not found for: {project_name}", "warning")

            # Save as last used
            self.config_manager.set("last_project", project_name)
            self.config_manager.save_config()

        except Exception as e:
            self.dialog.log_message(f"Error loading project config: {e}", "error")
            import traceback
            traceback.print_exc()
    
    def _on_root_changed(self) -> None:
        """Handle root path change (from browse button)."""
        root_path = self.dialog.root_path_edit.text()
        if root_path:
            self._scan_root(root_path)
    
    def _scan_root(self, root_path: str) -> None:
        """Scan root directory for episodes."""
        self.dialog.log_message(f"Scanning: {root_path}", "info")
        
        if not os.path.isdir(root_path):
            self.dialog.log_message(f"Directory not found: {root_path}", "error")
            return
        
        try:
            self.current_project_root = Path(root_path)
            self.scanner = ProjectScanner(
                root_path,
                progress_callback=self._progress_callback
            )
            
            # Scan episodes
            episodes = self.scanner.scan_episodes()
            
            if episodes:
                self.dialog.set_episodes(episodes)
                self.dialog.log_message(f"Found {len(episodes)} episode(s): {', '.join(episodes)}", "info")
            else:
                self.dialog.set_episodes([])
                self.dialog.log_message("No episodes found (looking for Ep* folders)", "warning")
                
        except Exception as e:
            self.dialog.log_message(f"Error scanning: {e}", "error")
            import traceback
            traceback.print_exc()
    
    def _on_episode_changed(self, episode: str) -> None:
        """Handle episode selection change."""
        if not episode or not self.scanner:
            return
        
        self.dialog.log_message(f"Loading sequences for: {episode}", "info")
        
        try:
            sequences = self.scanner.scan_sequences(episode)
            
            if sequences:
                self.dialog.set_sequences(sequences)
                self.dialog.log_message(f"Found {len(sequences)} sequence(s)", "info")
            else:
                self.dialog.set_sequences([])
                self.dialog.log_message("No sequences found (looking for sq* folders)", "warning")
                
        except Exception as e:
            self.dialog.log_message(f"Error loading sequences: {e}", "error")
    
    def _progress_callback(self, message: str, current: int, total: int) -> None:
        """Progress callback for scanner."""
        self.dialog.set_progress(message, current, total)
    
    def _on_build_timeline(self, config: dict) -> None:
        """Handle build timeline request."""
        self.dialog.log_message("Building timeline...", "info")
        self.dialog.log_message(f"Config: {config}", "info")
        # TODO: Implement actual timeline building
        self.dialog.log_message("Timeline building not yet implemented", "warning")

