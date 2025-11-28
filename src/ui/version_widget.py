"""
Version Control Widget Module
==============================
Version navigation controls for incrementing, decrementing, and selecting versions.
"""
from typing import List, Optional
from pathlib import Path
from datetime import datetime

try:
    from PySide2.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QPushButton, QGroupBox, QFrame, QSizePolicy,
    )
    from PySide2.QtCore import Qt, Signal
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
            QPushButton, QGroupBox, QFrame, QSizePolicy,
        )
        from PySide6.QtCore import Qt, Signal
    except ImportError:
        class QWidget:
            pass
        class Signal:
            def __init__(self, *args): pass

from ..core import VersionManager


class VersionControlWidget(QWidget):
    """
    Version navigation widget with prev/next/latest controls.
    """
    version_changed = Signal(str)  # Emits new version string
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._versions: List[str] = []
        self._current_index: int = -1
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Previous button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(30)
        self.prev_btn.setToolTip("Previous version")
        layout.addWidget(self.prev_btn)
        
        # Version dropdown
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(100)
        self.version_combo.setToolTip("Select version")
        layout.addWidget(self.version_combo, 1)
        
        # Next button
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(30)
        self.next_btn.setToolTip("Next version")
        layout.addWidget(self.next_btn)
        
        # Latest button
        self.latest_btn = QPushButton("Latest")
        self.latest_btn.setToolTip("Jump to latest version")
        layout.addWidget(self.latest_btn)
        
        # Version count label
        self.count_label = QLabel("0/0")
        self.count_label.setMinimumWidth(50)
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)
    
    def _connect_signals(self):
        self.prev_btn.clicked.connect(self._go_previous)
        self.next_btn.clicked.connect(self._go_next)
        self.latest_btn.clicked.connect(self._go_latest)
        self.version_combo.currentIndexChanged.connect(self._on_combo_changed)
    
    def set_versions(self, versions: List[str]) -> None:
        """Set available versions."""
        self._versions = VersionManager.sort_versions(versions)
        self._current_index = len(self._versions) - 1 if self._versions else -1
        
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItems(self._versions)
        if self._current_index >= 0:
            self.version_combo.setCurrentIndex(self._current_index)
        self.version_combo.blockSignals(False)
        
        self._update_ui()
    
    def _update_ui(self):
        """Update button states and count label."""
        has_versions = len(self._versions) > 0
        has_previous = self._current_index > 0
        has_next = self._current_index < len(self._versions) - 1
        
        self.prev_btn.setEnabled(has_previous)
        self.next_btn.setEnabled(has_next)
        self.latest_btn.setEnabled(has_versions and has_next)
        
        if has_versions:
            self.count_label.setText(f"{self._current_index + 1}/{len(self._versions)}")
        else:
            self.count_label.setText("0/0")
    
    def _go_previous(self):
        """Go to previous version."""
        if self._current_index > 0:
            self._current_index -= 1
            self.version_combo.setCurrentIndex(self._current_index)
    
    def _go_next(self):
        """Go to next version."""
        if self._current_index < len(self._versions) - 1:
            self._current_index += 1
            self.version_combo.setCurrentIndex(self._current_index)
    
    def _go_latest(self):
        """Jump to latest version."""
        if self._versions:
            self._current_index = len(self._versions) - 1
            self.version_combo.setCurrentIndex(self._current_index)
    
    def _on_combo_changed(self, index: int):
        """Handle combo box selection change."""
        self._current_index = index
        self._update_ui()
        if 0 <= index < len(self._versions):
            self.version_changed.emit(self._versions[index])
    
    def current_version(self) -> Optional[str]:
        """Get current selected version."""
        if 0 <= self._current_index < len(self._versions):
            return self._versions[self._current_index]
        return None
    
    def set_current_version(self, version: str) -> None:
        """Set current version by name."""
        if version in self._versions:
            idx = self._versions.index(version)
            self.version_combo.setCurrentIndex(idx)


class VersionInfoWidget(QWidget):
    """
    Display detailed version information.
    """
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Version label
        self.version_label = QLabel("No version selected")
        self.version_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.version_label)

        # Info labels
        self.date_label = QLabel("Date: -")
        layout.addWidget(self.date_label)

        self.size_label = QLabel("Size: -")
        layout.addWidget(self.size_label)

        self.artist_label = QLabel("Artist: -")
        layout.addWidget(self.artist_label)

        self.path_label = QLabel("Path: -")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #888;")
        layout.addWidget(self.path_label)

    def set_version_info(
        self, version: str, path: Optional[str] = None,
        artist: Optional[str] = None
    ) -> None:
        """Set version information display."""
        self.version_label.setText(f"Version: {version}")

        if path:
            p = Path(path)
            self.path_label.setText(f"Path: {path}")

            # Get file info
            if p.exists():
                stat = p.stat()
                size_mb = stat.st_size / (1024 * 1024)
                mod_time = datetime.fromtimestamp(stat.st_mtime)

                self.date_label.setText(f"Date: {mod_time.strftime('%Y-%m-%d %H:%M')}")
                self.size_label.setText(f"Size: {size_mb:.2f} MB")
            else:
                self.date_label.setText("Date: -")
                self.size_label.setText("Size: -")
        else:
            self.path_label.setText("Path: -")
            self.date_label.setText("Date: -")
            self.size_label.setText("Size: -")

        self.artist_label.setText(f"Artist: {artist or '-'}")

    def clear(self) -> None:
        """Clear version info display."""
        self.version_label.setText("No version selected")
        self.date_label.setText("Date: -")
        self.size_label.setText("Size: -")
        self.artist_label.setText("Artist: -")
        self.path_label.setText("Path: -")


class VersionPanel(QGroupBox):
    """
    Complete version panel with controls and info.
    """
    version_changed = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__("Version", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Version controls
        self.controls = VersionControlWidget()
        self.controls.version_changed.connect(self._on_version_changed)
        layout.addWidget(self.controls)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #555;")
        layout.addWidget(line)

        # Version info
        self.info = VersionInfoWidget()
        layout.addWidget(self.info)

    def _on_version_changed(self, version: str):
        self.version_changed.emit(version)

    def set_versions(self, versions: List[str]) -> None:
        """Set available versions."""
        self.controls.set_versions(versions)
        if versions:
            self.info.set_version_info(versions[-1])
        else:
            self.info.clear()

    def set_version_info(self, version: str, path: str = None, artist: str = None) -> None:
        """Update info panel for current version."""
        self.info.set_version_info(version, path, artist)

    def current_version(self) -> Optional[str]:
        """Get current selected version."""
        return self.controls.current_version()

