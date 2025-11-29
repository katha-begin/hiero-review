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
from ..core.timeline_builder import TimelineBuilder, TimelineConfig
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

        # Project config changed - connect AFTER other signals
        # so the UI is ready when project changes
        self.dialog.project_combo.currentTextChanged.connect(self._on_project_changed)

    def _initialize(self) -> None:
        """Initialize the controller and load initial data."""
        self.dialog.log_message("Initializing Review Tool...", "info")
        self._load_projects()

        # Trigger initial project load if a project is selected
        current_project = self.dialog.project_combo.currentText()
        if current_project:
            self._on_project_changed(current_project)
    
    def _load_projects(self) -> None:
        """Load available project configurations from multiple locations."""
        self.dialog.log_message("Loading project configurations...", "info")

        try:
            projects = []
            self._project_configs = {}

            # 1. Load from tool's local config folder
            tool_config_dir = get_tool_root() / "config"
            self.dialog.log_message(f"Checking tool config: {tool_config_dir}", "info")
            if tool_config_dir.exists():
                for config_file in tool_config_dir.glob("*.json"):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        name = config_file.stem
                        self._project_configs[name] = data
                        projects.append(name)
                        self.dialog.log_message(f"  Loaded: {name}", "info")
                    except Exception as e:
                        self.dialog.log_message(f"  Error loading {config_file.name}: {e}", "warning")
            else:
                self.dialog.log_message(f"  Config dir not found: {tool_config_dir}", "warning")

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
                            self.dialog.log_message(f"  Loaded: {name} (user)", "info")
                    except Exception as e:
                        self.dialog.log_message(f"  Error loading {config_file.name}: {e}", "warning")

            if not projects:
                projects = ["default"]
                self.dialog.log_message("No project configs found", "warning")

            # Block signals while setting projects to avoid triggering _on_project_changed
            self.dialog.project_combo.blockSignals(True)
            self.dialog.set_projects(sorted(projects))

            # Select last used project or first one
            last_project = self.config_manager.get("last_project", "")
            index = self.dialog.project_combo.findText(last_project)
            if index >= 0:
                self.dialog.project_combo.setCurrentIndex(index)

            self.dialog.project_combo.blockSignals(False)
            self.dialog.log_message(f"Loaded {len(projects)} project(s)", "info")

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
        from ..core.timeline_builder import TimelineBuilder, TimelineConfig
        from ..core.hiero_wrapper import HieroProject

        self.dialog.log_message("=" * 50, "info")
        self.dialog.log_message("Starting Timeline Build", "info")
        self.dialog.log_message("=" * 50, "info")

        # Validate required fields
        if not config.get('episode'):
            self.dialog.log_message("Error: No episode selected", "error")
            return
        if not config.get('sequences'):
            self.dialog.log_message("Error: No sequences selected", "error")
            return
        if not self.scanner:
            self.dialog.log_message("Error: No project scanned - set root path first", "error")
            return

        self.dialog.set_busy(True)

        try:
            # Log configuration
            self.dialog.log_message(f"Episode: {config['episode']}", "info")
            self.dialog.log_message(f"Sequences: {', '.join(config['sequences'])}", "info")
            self.dialog.log_message(f"Department: {config['department']}", "info")
            self.dialog.log_message(f"Version: {config['version']}", "info")
            self.dialog.log_message(f"Media Type: {config['media_type']}", "info")

            # Get project config for fps
            project_name = config.get('project', 'default')
            project_config = self._project_configs.get(project_name, {})
            fps = project_config.get('settings', {}).get('fps', 24.0)

            # Create timeline name
            timeline_name = f"{config['episode']}_Review"

            # Build TimelineConfig
            timeline_config = TimelineConfig(
                name=timeline_name,
                episode=config['episode'],
                sequences=config['sequences'],
                department=config['department'],
                version=config['version'],
                media_type=config['media_type'],
                fps=fps,
                include_audio=config.get('include_audio', True)
            )

            # Create TimelineBuilder with progress callback
            builder = TimelineBuilder(
                scanner=self.scanner,
                progress_callback=self._progress_callback
            )

            self.dialog.log_message("Scanning shots...", "info")

            # Build the timeline
            result = builder.build_timeline(timeline_config)

            if result.success:
                self.dialog.log_message("=" * 50, "info")
                self.dialog.log_message(f"SUCCESS: Timeline '{timeline_name}' created!", "info")
                self.dialog.log_message(f"Shots added: {result.shots_added}", "info")
                if result.shots_skipped:
                    self.dialog.log_message(f"Shots skipped: {len(result.shots_skipped)}", "warning")
                    for skip in result.shots_skipped[:5]:  # Show first 5
                        self.dialog.log_message(f"  - {skip}", "warning")
                    if len(result.shots_skipped) > 5:
                        self.dialog.log_message(f"  ... and {len(result.shots_skipped) - 5} more", "warning")
            else:
                self.dialog.log_message("=" * 50, "error")
                self.dialog.log_message("FAILED to build timeline", "error")
                for error in result.errors:
                    self.dialog.log_message(f"  - {error}", "error")

        except Exception as e:
            self.dialog.log_message(f"Error building timeline: {e}", "error")
            import traceback
            traceback.print_exc()

        finally:
            self.dialog.set_busy(False)

