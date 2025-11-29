"""
Main Dialog UI Module
======================
Main Qt-based dialog window for the Hiero Review Tool.
"""
from typing import Optional, Callable, List

# Try to import Qt - support both PySide2 (older Hiero) and PySide6 (newer Nuke 16+)
_QT_AVAILABLE = False

try:
    from PySide2.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QListWidget,
        QListWidgetItem, QButtonGroup, QRadioButton, QCheckBox,
        QProgressBar, QTextEdit, QGroupBox, QSplitter, QFileDialog,
        QMessageBox, QApplication, QWidget,
    )
    from PySide2.QtCore import Qt, Signal, QThread
    from PySide2.QtGui import QFont
    _QT_AVAILABLE = True
    print("[ReviewToolDialog] Using PySide2")
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
            QLabel, QLineEdit, QPushButton, QComboBox, QListWidget,
            QListWidgetItem, QButtonGroup, QRadioButton, QCheckBox,
            QProgressBar, QTextEdit, QGroupBox, QSplitter, QFileDialog,
            QMessageBox, QApplication, QWidget,
        )
        from PySide6.QtCore import Qt, Signal, QThread
        from PySide6.QtGui import QFont
        _QT_AVAILABLE = True
        print("[ReviewToolDialog] Using PySide6")
    except ImportError:
        print("[ReviewToolDialog] No Qt available - using stubs")
        # Define minimal stubs for testing without Qt
        class QDialog:
            pass
        class QWidget:
            pass
        class Signal:
            def __init__(self, *args): pass
        class Qt:
            AlignTop = 0


class ReviewToolDialog(QDialog):
    """
    Main dialog for the Hiero Review Tool.
    
    Provides UI for:
    - Project/episode/sequence selection
    - Department and version controls
    - Timeline building actions
    - Progress and status display
    """
    
    # Signals
    build_requested = Signal(dict)  # Emits build configuration
    update_requested = Signal(str)  # Emits target version
    cancel_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Hiero Review Tool")
        self.setMinimumSize(600, 700)
        self.resize(700, 800)
        
        self._setup_ui()
        self._connect_signals()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Project Selection Group
        main_layout.addWidget(self._create_project_group())
        
        # Selection Group (Episode/Sequence)
        main_layout.addWidget(self._create_selection_group())
        
        # Options Group (Department/Version/Media)
        main_layout.addWidget(self._create_options_group())
        
        # Action Buttons
        main_layout.addLayout(self._create_action_buttons())
        
        # Progress and Status
        main_layout.addWidget(self._create_progress_group())
        
        # Status Log
        main_layout.addWidget(self._create_log_group())
    
    def _create_project_group(self) -> QGroupBox:
        """Create project selection group."""
        group = QGroupBox("Project")
        layout = QGridLayout(group)
        
        # Project Config dropdown
        layout.addWidget(QLabel("Config:"), 0, 0)
        self.project_combo = QComboBox()
        self.project_combo.setToolTip("Select project configuration")
        layout.addWidget(self.project_combo, 0, 1)
        
        self.refresh_projects_btn = QPushButton("↻")
        self.refresh_projects_btn.setFixedWidth(30)
        self.refresh_projects_btn.setToolTip("Refresh project list")
        layout.addWidget(self.refresh_projects_btn, 0, 2)
        
        # Root Path
        layout.addWidget(QLabel("Root:"), 1, 0)
        self.root_path_edit = QLineEdit()
        self.root_path_edit.setPlaceholderText("Project root directory (e.g., V:/SWA/all/scene)")
        # Allow editing so user can type path directly
        layout.addWidget(self.root_path_edit, 1, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setToolTip("Override project root")
        layout.addWidget(self.browse_btn, 1, 2)
        
        return group
    
    def _create_selection_group(self) -> QGroupBox:
        """Create episode/sequence selection group."""
        group = QGroupBox("Selection")
        layout = QGridLayout(group)
        
        # Episode
        layout.addWidget(QLabel("Episode:"), 0, 0)
        self.episode_combo = QComboBox()
        self.episode_combo.setToolTip("Select episode")
        layout.addWidget(self.episode_combo, 0, 1, 1, 2)
        
        # Sequences
        layout.addWidget(QLabel("Sequences:"), 1, 0, Qt.AlignTop)
        self.sequence_list = QListWidget()
        self.sequence_list.setSelectionMode(QListWidget.MultiSelection)
        self.sequence_list.setMaximumHeight(150)
        self.sequence_list.setToolTip("Select sequences to include")
        layout.addWidget(self.sequence_list, 1, 1, 1, 2)
        
        # Select All / Deselect All
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout, 2, 1, 1, 2)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create options group (department, version, media type)."""
        group = QGroupBox("Options")
        layout = QGridLayout(group)
        
        # Department
        layout.addWidget(QLabel("Department:"), 0, 0)
        self.dept_combo = QComboBox()
        self.dept_combo.addItems(["comp", "light", "anim", "fx"])
        self.dept_combo.setToolTip("Select department")
        layout.addWidget(self.dept_combo, 0, 1)
        
        # Version
        layout.addWidget(QLabel("Version:"), 1, 0)
        version_layout = QHBoxLayout()

        self.version_prev_btn = QPushButton("◀")
        self.version_prev_btn.setFixedWidth(30)
        self.version_prev_btn.setToolTip("Previous version")
        version_layout.addWidget(self.version_prev_btn)

        self.version_combo = QComboBox()
        self.version_combo.addItem("Latest")
        self.version_combo.setToolTip("Select version")
        version_layout.addWidget(self.version_combo)

        self.version_next_btn = QPushButton("▶")
        self.version_next_btn.setFixedWidth(30)
        self.version_next_btn.setToolTip("Next version")
        version_layout.addWidget(self.version_next_btn)

        self.version_latest_btn = QPushButton("Latest")
        self.version_latest_btn.setToolTip("Jump to latest version")
        version_layout.addWidget(self.version_latest_btn)

        layout.addLayout(version_layout, 1, 1)

        # Media Type
        layout.addWidget(QLabel("Media:"), 2, 0)
        media_layout = QHBoxLayout()
        self.media_group = QButtonGroup(self)

        self.mov_radio = QRadioButton("MOV")
        self.mov_radio.setChecked(True)
        self.mov_radio.setToolTip("Use MOV files")
        self.media_group.addButton(self.mov_radio)
        media_layout.addWidget(self.mov_radio)

        self.seq_radio = QRadioButton("Sequence")
        self.seq_radio.setToolTip("Use image sequences (EXR/PNG)")
        self.media_group.addButton(self.seq_radio)
        media_layout.addWidget(self.seq_radio)

        media_layout.addStretch()
        layout.addLayout(media_layout, 2, 1)

        # Include Audio
        self.include_audio_cb = QCheckBox("Include Audio")
        self.include_audio_cb.setChecked(True)
        self.include_audio_cb.setToolTip("Sync audio tracks if available")
        layout.addWidget(self.include_audio_cb, 3, 1)

        return group

    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()

        self.build_btn = QPushButton("Build Timeline")
        self.build_btn.setMinimumHeight(40)
        self.build_btn.setToolTip("Build timeline from selected shots")
        layout.addWidget(self.build_btn)

        self.update_btn = QPushButton("Update Versions")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.setToolTip("Update all shots to selected version")
        layout.addWidget(self.update_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip("Cancel current operation")
        layout.addWidget(self.cancel_btn)

        return layout

    def _create_progress_group(self) -> QGroupBox:
        """Create progress display group."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout(group)

        self.progress_label = QLabel("Ready")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        return group

    def _create_log_group(self) -> QGroupBox:
        """Create status log group."""
        group = QGroupBox("Status Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_log_btn)
        layout.addLayout(btn_layout)

        return group

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self.browse_btn.clicked.connect(self._on_browse)
        self.root_path_edit.returnPressed.connect(self._on_root_path_enter)
        self.select_all_btn.clicked.connect(self._select_all_sequences)
        self.deselect_all_btn.clicked.connect(self._deselect_all_sequences)
        self.clear_log_btn.clicked.connect(self._clear_log)

        self.build_btn.clicked.connect(self._on_build)
        self.update_btn.clicked.connect(self._on_update)
        self.cancel_btn.clicked.connect(self._on_cancel)

    def _apply_style(self) -> None:
        """Apply Hiero-like dark theme stylesheet."""
        self.setStyleSheet("""
            QDialog { background-color: #3c3c3c; color: #e0e0e0; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                background-color: #505050;
                border: 1px solid #666;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #606060; }
            QPushButton:pressed { background-color: #404040; }
            QPushButton:disabled { background-color: #3a3a3a; color: #666; }
            QComboBox, QLineEdit, QListWidget, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555;
                padding: 3px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk { background-color: #4a90d9; }
        """)

    # ========================================================================
    # Slot methods
    # ========================================================================

    def _on_browse(self) -> None:
        """Handle browse button click."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Project Root", self.root_path_edit.text()
        )
        if path:
            self.root_path_edit.setText(path)
            self.log_message(f"Root changed to: {path}")

    def _on_root_path_enter(self) -> None:
        """Handle Enter key in root path field."""
        self.log_message(f"Root path entered: {self.root_path_edit.text()}")

    def _select_all_sequences(self) -> None:
        """Select all sequences in list."""
        for i in range(self.sequence_list.count()):
            self.sequence_list.item(i).setSelected(True)

    def _deselect_all_sequences(self) -> None:
        """Deselect all sequences in list."""
        self.sequence_list.clearSelection()

    def _clear_log(self) -> None:
        """Clear the status log."""
        self.log_text.clear()

    def _on_build(self) -> None:
        """Handle build button click."""
        config = self.get_build_config()
        if not config.get('sequences'):
            QMessageBox.warning(self, "Warning", "Please select at least one sequence.")
            return
        self.build_requested.emit(config)

    def _on_update(self) -> None:
        """Handle update button click."""
        version = self.version_combo.currentText()
        self.update_requested.emit(version)

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.cancel_requested.emit()

    # ========================================================================
    # Public API
    # ========================================================================

    def get_build_config(self) -> dict:
        """Get current build configuration from UI state."""
        return {
            'project': self.project_combo.currentText(),
            'root_path': self.root_path_edit.text(),
            'episode': self.episode_combo.currentText(),
            'sequences': [item.text() for item in self.sequence_list.selectedItems()],
            'department': self.dept_combo.currentText(),
            'version': self.version_combo.currentText(),
            'media_type': 'mov' if self.mov_radio.isChecked() else 'sequence',
            'include_audio': self.include_audio_cb.isChecked(),
        }

    def set_projects(self, projects: List[str]) -> None:
        """Populate project dropdown."""
        self.project_combo.clear()
        self.project_combo.addItems(projects)

    def set_episodes(self, episodes: List[str]) -> None:
        """Populate episode dropdown."""
        self.episode_combo.clear()
        self.episode_combo.addItems(episodes)

    def set_sequences(self, sequences: List[str]) -> None:
        """Populate sequence list."""
        self.sequence_list.clear()
        for seq in sequences:
            item = QListWidgetItem(seq)
            self.sequence_list.addItem(item)

    def set_versions(self, versions: List[str]) -> None:
        """Populate version dropdown."""
        self.version_combo.clear()
        self.version_combo.addItem("Latest")
        self.version_combo.addItems(versions)

    def set_progress(self, message: str, current: int, total: int) -> None:
        """Update progress display."""
        self.progress_label.setText(message)
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate

    def log_message(self, message: str, level: str = "info") -> None:
        """Add message to status log."""
        colors = {"info": "#e0e0e0", "warning": "#ffd700", "error": "#ff6b6b"}
        color = colors.get(level, colors["info"])
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f'<span style="color:{color}">[{timestamp}] {message}</span>')

    def set_busy(self, busy: bool) -> None:
        """Set UI busy state."""
        self.build_btn.setEnabled(not busy)
        self.update_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        if busy:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)


# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dialog = ReviewToolDialog()
    dialog.set_projects(["default", "SWA"])
    dialog.set_episodes(["Ep01", "Ep02", "Ep03"])
    dialog.set_sequences(["sq0010", "sq0020", "sq0030"])
    dialog.log_message("Dialog ready", "info")
    dialog.show()
    sys.exit(app.exec_())

