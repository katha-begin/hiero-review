"""
Lighting Import Dialog
=======================
Dialog for selecting lighting render versions, layers, and passes to import.
"""
from typing import Optional, List, Dict, Any, Callable

try:
    from PySide2.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
        QTreeWidget, QTreeWidgetItem, QPushButton, QGroupBox,
        QCheckBox, QDialogButtonBox, QHeaderView, QMessageBox
    )
    from PySide2.QtCore import Qt, Signal
except ImportError:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QTreeWidget, QTreeWidgetItem, QPushButton, QGroupBox,
        QCheckBox, QDialogButtonBox, QHeaderView, QMessageBox
    )
    from PySide6.QtCore import Qt, Signal

from ..core.lighting_scanner import (
    LightingScanner, LightingScanResult, VersionInfo, LayerInfo, RenderPassInfo
)


class LightingImportDialog(QDialog):
    """
    Dialog for selecting lighting renders to import to timeline2.
    
    Shows:
    - Version selector (dropdown, latest by default)
    - Tree view of layers and render passes
    - Frame range info
    - Import button
    """
    
    import_requested = Signal(list)  # Emits list of selected RenderPassInfo
    
    def __init__(
        self, 
        scan_result: LightingScanResult,
        parent: Optional[Any] = None
    ):
        super().__init__(parent)
        self._scan_result = scan_result
        self._selected_passes: List[RenderPassInfo] = []
        
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(f"Import Lighting Render - {self._scan_result.shot_name}")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Shot info header
        info_label = QLabel(f"<b>Shot:</b> {self._scan_result.shot_name}")
        layout.addWidget(info_label)
        
        # Version selector
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self._version_combo = QComboBox()
        self._version_combo.currentTextChanged.connect(self._on_version_changed)
        version_layout.addWidget(self._version_combo, 1)
        layout.addLayout(version_layout)
        
        # Layer/Pass tree
        tree_group = QGroupBox("Layers and Render Passes")
        tree_layout = QVBoxLayout(tree_group)
        
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name", "Frames", "Frame Range"])
        self._tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self._tree.itemChanged.connect(self._on_item_changed)
        
        # Set column widths
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        tree_layout.addWidget(self._tree)
        layout.addWidget(tree_group)
        
        # Selection info
        self._selection_label = QLabel("Selected: 0 render pass(es)")
        layout.addWidget(self._selection_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        self._import_btn = QPushButton("Import to Timeline2")
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._on_import)
        button_box.addButton(self._import_btn, QDialogButtonBox.AcceptRole)
        button_box.addButton(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_data(self):
        """Populate version combo and tree."""
        if not self._scan_result.has_data:
            self._version_combo.addItem("No lighting versions found")
            self._version_combo.setEnabled(False)
            return
        
        # Populate versions (latest first in display, but select latest)
        versions = [v.version for v in self._scan_result.versions]
        versions_display = list(reversed(versions))  # Show latest at top
        
        for v in versions_display:
            self._version_combo.addItem(v)
        
        # Select latest version by default
        if self._scan_result.latest_version:
            idx = self._version_combo.findText(self._scan_result.latest_version)
            if idx >= 0:
                self._version_combo.setCurrentIndex(idx)
    
    def _on_version_changed(self, version_name: str):
        """Handle version selection change."""
        self._tree.clear()
        self._selected_passes = []
        self._update_selection_label()
        
        # Find version info
        version_info = None
        for v in self._scan_result.versions:
            if v.version == version_name:
                version_info = v
                break
        
        if not version_info:
            return
        
        # Populate tree with layers and render passes
        for layer in version_info.layers:
            layer_item = QTreeWidgetItem([layer.name, "", ""])
            layer_item.setFlags(layer_item.flags() | Qt.ItemIsUserCheckable)
            layer_item.setCheckState(0, Qt.Unchecked)
            layer_item.setData(0, Qt.UserRole, layer)
            
            for render_pass in layer.render_passes:
                frame_range = f"{render_pass.start_frame}-{render_pass.end_frame}"
                pass_item = QTreeWidgetItem([
                    render_pass.name,
                    str(render_pass.frame_count),
                    frame_range
                ])
                pass_item.setFlags(pass_item.flags() | Qt.ItemIsUserCheckable)
                pass_item.setCheckState(0, Qt.Unchecked)
                pass_item.setData(0, Qt.UserRole, render_pass)
                layer_item.addChild(pass_item)
            
            self._tree.addTopLevelItem(layer_item)
        
        self._tree.expandAll()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox state change."""
        if column != 0:
            return

        is_checked = item.checkState(0) == Qt.Checked
        data = item.data(0, Qt.UserRole)

        # If this is a layer item, toggle all children
        if isinstance(data, LayerInfo):
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, Qt.Checked if is_checked else Qt.Unchecked)

        # Update selected passes list
        self._update_selected_passes()

    def _update_selected_passes(self):
        """Update the list of selected render passes."""
        self._selected_passes = []

        for i in range(self._tree.topLevelItemCount()):
            layer_item = self._tree.topLevelItem(i)
            for j in range(layer_item.childCount()):
                pass_item = layer_item.child(j)
                if pass_item.checkState(0) == Qt.Checked:
                    data = pass_item.data(0, Qt.UserRole)
                    if isinstance(data, RenderPassInfo):
                        self._selected_passes.append(data)

        self._update_selection_label()

    def _update_selection_label(self):
        """Update the selection count label."""
        count = len(self._selected_passes)
        self._selection_label.setText(f"Selected: {count} render pass(es)")
        self._import_btn.setEnabled(count > 0)

    def _on_import(self):
        """Handle import button click."""
        if not self._selected_passes:
            return

        self.import_requested.emit(self._selected_passes)
        self.accept()

    def get_selected_passes(self) -> List[RenderPassInfo]:
        """Get the list of selected render passes."""
        return self._selected_passes

    def get_selected_version(self) -> str:
        """Get the currently selected version."""
        return self._version_combo.currentText()

