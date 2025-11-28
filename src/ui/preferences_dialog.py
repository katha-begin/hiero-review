"""
Preferences Dialog Module
==========================
User preferences and settings dialog.
"""
from typing import Optional, Dict, Any

try:
    from PySide2.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
        QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
        QPushButton, QComboBox, QGroupBox, QFormLayout, QFileDialog,
        QMessageBox,
    )
    from PySide2.QtCore import Qt, Signal
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
            QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
            QPushButton, QComboBox, QGroupBox, QFormLayout, QFileDialog,
            QMessageBox,
        )
        from PySide6.QtCore import Qt, Signal
    except ImportError:
        class QDialog:
            pass
        class Signal:
            def __init__(self, *args): pass

from ..config import ConfigManager, get_config_manager


class PreferencesDialog(QDialog):
    """
    Preferences dialog for customizing tool behavior.
    """
    settings_changed = Signal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        
        self._config = get_config_manager()
        self._setup_ui()
        self._load_settings()
        self._apply_style()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_performance_tab(), "Performance")
        self.tabs.addTab(self._create_display_tab(), "Display")
        self.tabs.addTab(self._create_advanced_tab(), "Advanced")
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.reset_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create General settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Default Project group
        project_group = QGroupBox("Default Project")
        form = QFormLayout(project_group)
        
        # Default root path
        root_layout = QHBoxLayout()
        self.default_root_edit = QLineEdit()
        self.default_root_edit.setPlaceholderText("Default project root...")
        root_layout.addWidget(self.default_root_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_root)
        root_layout.addWidget(browse_btn)
        form.addRow("Root Path:", root_layout)
        
        # Default department
        self.default_dept_combo = QComboBox()
        self.default_dept_combo.addItems(["comp", "light", "anim", "fx"])
        form.addRow("Department:", self.default_dept_combo)
        
        # Default media type
        self.default_media_combo = QComboBox()
        self.default_media_combo.addItems(["MOV", "Image Sequence"])
        form.addRow("Media Type:", self.default_media_combo)
        
        layout.addWidget(project_group)
        
        # Recent projects group
        recent_group = QGroupBox("Recent Projects")
        recent_layout = QVBoxLayout(recent_group)
        
        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setRange(1, 20)
        self.max_recent_spin.setValue(5)
        recent_layout.addWidget(QLabel("Max recent projects:"))
        recent_layout.addWidget(self.max_recent_spin)
        
        layout.addWidget(recent_group)
        layout.addStretch()
        
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """Create Performance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cache group
        cache_group = QGroupBox("Cache Settings")
        form = QFormLayout(cache_group)
        
        self.cache_enabled_cb = QCheckBox("Enable caching")
        self.cache_enabled_cb.setChecked(True)
        form.addRow("", self.cache_enabled_cb)
        
        self.memory_cache_spin = QSpinBox()
        self.memory_cache_spin.setRange(10, 600)
        self.memory_cache_spin.setValue(60)
        self.memory_cache_spin.setSuffix(" seconds")
        form.addRow("Memory cache TTL:", self.memory_cache_spin)
        
        self.disk_cache_spin = QSpinBox()
        self.disk_cache_spin.setRange(60, 86400)
        self.disk_cache_spin.setValue(3600)
        self.disk_cache_spin.setSuffix(" seconds")
        form.addRow("Disk cache TTL:", self.disk_cache_spin)
        
        layout.addWidget(cache_group)

        # Threading group
        thread_group = QGroupBox("Threading")
        thread_form = QFormLayout(thread_group)

        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        thread_form.addRow("Max parallel operations:", self.max_workers_spin)

        self.scan_timeout_spin = QSpinBox()
        self.scan_timeout_spin.setRange(10, 300)
        self.scan_timeout_spin.setValue(60)
        self.scan_timeout_spin.setSuffix(" seconds")
        thread_form.addRow("Scan timeout:", self.scan_timeout_spin)

        layout.addWidget(thread_group)
        layout.addStretch()

        return widget

    def _create_display_tab(self) -> QWidget:
        """Create Display settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Timeline group
        timeline_group = QGroupBox("Timeline Defaults")
        form = QFormLayout(timeline_group)

        self.default_fps_spin = QDoubleSpinBox()
        self.default_fps_spin.setRange(1.0, 120.0)
        self.default_fps_spin.setValue(24.0)
        self.default_fps_spin.setDecimals(3)
        form.addRow("Default FPS:", self.default_fps_spin)

        self.timeline_naming_edit = QLineEdit()
        self.timeline_naming_edit.setText("{episode}_{sequence}_review")
        self.timeline_naming_edit.setToolTip("Variables: {episode}, {sequence}, {date}")
        form.addRow("Timeline naming:", self.timeline_naming_edit)

        layout.addWidget(timeline_group)

        # Tags group
        tags_group = QGroupBox("Tag Colors")
        tags_form = QFormLayout(tags_group)

        self.tag_latest_combo = QComboBox()
        self.tag_latest_combo.addItems(["Green", "Blue", "Yellow", "Red", "Cyan"])
        tags_form.addRow("Latest version:", self.tag_latest_combo)

        self.tag_old_combo = QComboBox()
        self.tag_old_combo.addItems(["Yellow", "Orange", "Red", "Gray"])
        tags_form.addRow("Old version:", self.tag_old_combo)

        layout.addWidget(tags_group)
        layout.addStretch()

        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create Advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Regex patterns group
        regex_group = QGroupBox("Custom Regex Patterns")
        form = QFormLayout(regex_group)

        self.episode_pattern_edit = QLineEdit()
        self.episode_pattern_edit.setText(r"Ep\d{2}")
        form.addRow("Episode:", self.episode_pattern_edit)

        self.sequence_pattern_edit = QLineEdit()
        self.sequence_pattern_edit.setText(r"sq\d{4}")
        form.addRow("Sequence:", self.sequence_pattern_edit)

        self.shot_pattern_edit = QLineEdit()
        self.shot_pattern_edit.setText(r"SH\d{4}")
        form.addRow("Shot:", self.shot_pattern_edit)

        self.version_pattern_edit = QLineEdit()
        self.version_pattern_edit.setText(r"v\d{3,4}")
        form.addRow("Version:", self.version_pattern_edit)

        layout.addWidget(regex_group)

        # Debug group
        debug_group = QGroupBox("Debug")
        debug_layout = QVBoxLayout(debug_group)

        self.debug_mode_cb = QCheckBox("Enable debug mode")
        debug_layout.addWidget(self.debug_mode_cb)

        self.verbose_logging_cb = QCheckBox("Verbose logging")
        debug_layout.addWidget(self.verbose_logging_cb)

        layout.addWidget(debug_group)
        layout.addStretch()

        return widget

    def _browse_root(self):
        """Browse for default root path."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Project Root", self.default_root_edit.text()
        )
        if path:
            self.default_root_edit.setText(path)

    def _load_settings(self):
        """Load settings from config manager."""
        self.default_root_edit.setText(self._config.get("default_root", ""))
        self.default_dept_combo.setCurrentText(self._config.get("default_department", "comp"))
        self.default_media_combo.setCurrentIndex(
            0 if self._config.get("default_media_type", "mov") == "mov" else 1
        )
        self.cache_enabled_cb.setChecked(self._config.is_cache_enabled())
        self.max_workers_spin.setValue(self._config.get("max_workers", 4))
        self.default_fps_spin.setValue(self._config.get("default_fps", 24.0))
        self.debug_mode_cb.setChecked(self._config.get("debug_mode", False))

    def _apply_settings(self):
        """Apply current settings to config."""
        self._config.set("default_root", self.default_root_edit.text())
        self._config.set("default_department", self.default_dept_combo.currentText())
        self._config.set("default_media_type",
                        "mov" if self.default_media_combo.currentIndex() == 0 else "sequence")
        self._config.set("cache_enabled", self.cache_enabled_cb.isChecked())
        self._config.set("max_workers", self.max_workers_spin.value())
        self._config.set("default_fps", self.default_fps_spin.value())
        self._config.set("debug_mode", self.debug_mode_cb.isChecked())

        self._config.set("patterns", {
            "episode": self.episode_pattern_edit.text(),
            "sequence": self.sequence_pattern_edit.text(),
            "shot": self.shot_pattern_edit.text(),
            "version": self.version_pattern_edit.text(),
        })

        self._config.save_config()
        self.settings_changed.emit()

    def _save_and_close(self):
        """Save settings and close dialog."""
        self._apply_settings()
        self.accept()

    def _reset_defaults(self):
        """Reset all settings to defaults."""
        result = QMessageBox.question(
            self, "Reset Defaults",
            "Reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        if result == QMessageBox.Yes:
            self._config.reset_to_defaults()
            self._load_settings()

    def _apply_style(self):
        """Apply dark theme stylesheet."""
        self.setStyleSheet("""
            QDialog { background-color: #3c3c3c; color: #e0e0e0; }
            QGroupBox {
                font-weight: bold; border: 1px solid #555;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2d2d2d; border: 1px solid #555; padding: 3px;
            }
            QPushButton {
                background-color: #505050; border: 1px solid #666;
                padding: 5px 15px; border-radius: 3px;
            }
            QPushButton:hover { background-color: #606060; }
            QTabWidget::pane { border: 1px solid #555; }
            QTabBar::tab {
                background-color: #3c3c3c; padding: 8px 15px;
                border: 1px solid #555; border-bottom: none;
            }
            QTabBar::tab:selected { background-color: #4c4c4c; }
        """)

