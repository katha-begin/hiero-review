"""
Selector Widget Module
=======================
Episode and sequence selection controls with dynamic population.
"""
from typing import List, Optional, Callable, Set

try:
    from PySide2.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QListWidget, QListWidgetItem, QPushButton, QLineEdit,
        QGroupBox, QCheckBox, QProgressBar,
    )
    from PySide2.QtCore import Qt, Signal, QThread
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
            QListWidget, QListWidgetItem, QPushButton, QLineEdit,
            QGroupBox, QCheckBox, QProgressBar,
        )
        from PySide6.QtCore import Qt, Signal, QThread
    except ImportError:
        class QWidget:
            pass
        class Signal:
            def __init__(self, *args): pass

from ..core import ProjectScanner


class ScanWorker(QThread):
    """Background worker for scanning operations."""
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, scanner: ProjectScanner, scan_type: str, **kwargs):
        super().__init__()
        self._scanner = scanner
        self._scan_type = scan_type
        self._kwargs = kwargs
    
    def run(self):
        try:
            if self._scan_type == "episodes":
                result = self._scanner.scan_episodes()
            elif self._scan_type == "sequences":
                result = self._scanner.scan_sequences(self._kwargs.get('episode', ''))
            elif self._scan_type == "shots":
                result = self._scanner.scan_shots(
                    self._kwargs.get('episode', ''),
                    self._kwargs.get('sequence', '')
                )
            else:
                result = []
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class EpisodeSelector(QWidget):
    """
    Episode selection dropdown with dynamic population.
    """
    episode_changed = Signal(str)
    
    def __init__(self, scanner: Optional[ProjectScanner] = None, parent: QWidget = None):
        super().__init__(parent)
        self._scanner = scanner
        self._worker: Optional[ScanWorker] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Episode:"))
        
        self.combo = QComboBox()
        self.combo.setMinimumWidth(150)
        self.combo.currentTextChanged.connect(self._on_episode_changed)
        layout.addWidget(self.combo, 1)
        
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedWidth(30)
        self.refresh_btn.setToolTip("Refresh episodes")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        
        self.loading_label = QLabel("⏳")
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
    
    def set_scanner(self, scanner: ProjectScanner) -> None:
        """Set the project scanner."""
        self._scanner = scanner
    
    def refresh(self) -> None:
        """Refresh episode list from scanner."""
        if not self._scanner:
            return
        
        self.loading_label.setVisible(True)
        self.combo.setEnabled(False)
        
        self._worker = ScanWorker(self._scanner, "episodes")
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()
    
    def _on_scan_finished(self, episodes: List[str]) -> None:
        self.loading_label.setVisible(False)
        self.combo.setEnabled(True)
        
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItems(episodes)
        
        # Restore selection if possible
        idx = self.combo.findText(current)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
    
    def _on_scan_error(self, error: str) -> None:
        self.loading_label.setVisible(False)
        self.combo.setEnabled(True)
    
    def _on_episode_changed(self, episode: str) -> None:
        self.episode_changed.emit(episode)
    
    def current_episode(self) -> str:
        return self.combo.currentText()
    
    def set_episodes(self, episodes: List[str]) -> None:
        """Manually set episodes list."""
        self.combo.clear()
        self.combo.addItems(episodes)


class SequenceSelector(QWidget):
    """
    Multi-select sequence list with search/filter.
    """
    selection_changed = Signal(list)
    
    def __init__(self, scanner: Optional[ProjectScanner] = None, parent: QWidget = None):
        super().__init__(parent)
        self._scanner = scanner
        self._episode = ""
        self._all_sequences: List[str] = []
        self._worker: Optional[ScanWorker] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search/filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Type to filter...")
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_edit)
        layout.addLayout(filter_layout)

        # Sequence list with checkboxes
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        # Select All / Deselect All buttons
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        self.loading_label = QLabel("⏳ Loading...")
        self.loading_label.setVisible(False)
        btn_layout.addWidget(self.loading_label)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def set_scanner(self, scanner: ProjectScanner) -> None:
        """Set the project scanner."""
        self._scanner = scanner

    def set_episode(self, episode: str) -> None:
        """Set current episode and refresh sequences."""
        self._episode = episode
        self.refresh()

    def refresh(self) -> None:
        """Refresh sequence list from scanner."""
        if not self._scanner or not self._episode:
            return

        self.loading_label.setVisible(True)
        self.list_widget.setEnabled(False)

        self._worker = ScanWorker(self._scanner, "sequences", episode=self._episode)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()

    def _on_scan_finished(self, sequences: List[str]) -> None:
        self.loading_label.setVisible(False)
        self.list_widget.setEnabled(True)

        self._all_sequences = sequences
        self._populate_list(sequences)

    def _on_scan_error(self, error: str) -> None:
        self.loading_label.setVisible(False)
        self.list_widget.setEnabled(True)

    def _populate_list(self, sequences: List[str]) -> None:
        """Populate the list widget."""
        self.list_widget.clear()
        for seq in sequences:
            item = QListWidgetItem(seq)
            self.list_widget.addItem(item)

    def _apply_filter(self, text: str) -> None:
        """Filter sequences by text."""
        text = text.lower()
        filtered = [s for s in self._all_sequences if text in s.lower()]
        self._populate_list(filtered)

    def _on_selection_changed(self) -> None:
        selected = self.selected_sequences()
        self.selection_changed.emit(selected)

    def select_all(self) -> None:
        """Select all visible sequences."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)

    def deselect_all(self) -> None:
        """Deselect all sequences."""
        self.list_widget.clearSelection()

    def selected_sequences(self) -> List[str]:
        """Get list of selected sequence names."""
        return [item.text() for item in self.list_widget.selectedItems()]

    def set_sequences(self, sequences: List[str]) -> None:
        """Manually set sequences list."""
        self._all_sequences = sequences
        self._populate_list(sequences)


class ShotSelector(QWidget):
    """
    Shot browser widget showing shots for selected sequences.
    """
    shot_selected = Signal(str, str, str)  # episode, sequence, shot

    def __init__(self, scanner: Optional[ProjectScanner] = None, parent: QWidget = None):
        super().__init__(parent)
        self._scanner = scanner
        self._episode = ""
        self._sequences: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        info_layout = QHBoxLayout()
        self.count_label = QLabel("0 shots")
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

    def set_scanner(self, scanner: ProjectScanner) -> None:
        self._scanner = scanner

    def set_episode(self, episode: str) -> None:
        self._episode = episode

    def set_sequences(self, sequences: List[str]) -> None:
        """Set sequences and load shots."""
        self._sequences = sequences
        self._load_shots()

    def _load_shots(self) -> None:
        """Load shots from all selected sequences."""
        if not self._scanner or not self._episode:
            return

        self.list_widget.clear()
        total = 0

        for seq in self._sequences:
            shots = self._scanner.scan_shots(self._episode, seq)
            for shot in shots:
                item = QListWidgetItem(f"{seq}/{shot}")
                item.setData(Qt.UserRole, (self._episode, seq, shot))
                self.list_widget.addItem(item)
                total += 1

        self.count_label.setText(f"{total} shots")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if data:
            self.shot_selected.emit(*data)

