"""
Context Menu Module
====================
Right-click context menu for timeline track items.
"""
import os
import subprocess
import platform
from typing import List, Optional, Any

try:
    from PySide2.QtWidgets import QMenu, QAction, QMessageBox
    from PySide2.QtCore import QObject
except ImportError:
    try:
        from PySide6.QtWidgets import QMenu, QAction, QMessageBox
        from PySide6.QtCore import QObject
    except ImportError:
        class QMenu:
            pass
        class QAction:
            pass
        class QObject:
            pass

# Try to import Hiero
try:
    import hiero.core
    import hiero.ui
    HIERO_AVAILABLE = True
except ImportError:
    HIERO_AVAILABLE = False

from ..core import VersionManager, VersionUpdater, DepartmentSwitcher, ProjectScanner
from ..core.lighting_scanner import LightingScanner


class TrackItemContextMenu(QObject):
    """
    Context menu handler for timeline track items.

    Provides right-click options for:
    - Version switching
    - Department switching
    - Import lighting render
    - Show in explorer
    - Shot properties
    """

    def __init__(self, scanner: Optional[ProjectScanner] = None):
        super().__init__()
        self._scanner = scanner
        self._version_updater: Optional[VersionUpdater] = None
        self._dept_switcher: Optional[DepartmentSwitcher] = None
        self._lighting_scanner: Optional[LightingScanner] = None

        if scanner:
            self._version_updater = VersionUpdater(scanner)
            self._dept_switcher = DepartmentSwitcher(scanner)
            self._lighting_scanner = LightingScanner(scanner._project_root)
    
    def set_scanner(self, scanner: ProjectScanner) -> None:
        """Set the project scanner."""
        self._scanner = scanner
        self._version_updater = VersionUpdater(scanner)
        self._dept_switcher = DepartmentSwitcher(scanner)
        self._lighting_scanner = LightingScanner(scanner._project_root)
    
    def build_menu(self, track_items: List[Any]) -> QMenu:
        """
        Build context menu for selected track items.
        
        Args:
            track_items: List of selected Hiero track items
            
        Returns:
            QMenu with appropriate actions
        """
        menu = QMenu()
        
        if not track_items:
            action = menu.addAction("No items selected")
            action.setEnabled(False)
            return menu
        
        single_item = len(track_items) == 1
        item = track_items[0] if single_item else None
        
        # Version submenu
        version_menu = menu.addMenu("Switch Version")
        self._build_version_menu(version_menu, track_items)
        
        # Department submenu
        dept_menu = menu.addMenu("Switch Department")
        self._build_department_menu(dept_menu, track_items)
        
        menu.addSeparator()
        
        # Version navigation
        prev_action = menu.addAction("Previous Version")
        prev_action.triggered.connect(lambda: self._go_previous_version(track_items))
        
        next_action = menu.addAction("Next Version")
        next_action.triggered.connect(lambda: self._go_next_version(track_items))
        
        latest_action = menu.addAction("Latest Version")
        latest_action.triggered.connect(lambda: self._go_latest_version(track_items))
        
        menu.addSeparator()

        # Import lighting render (single item only)
        if single_item:
            lighting_action = menu.addAction("Import Lighting Render...")
            lighting_action.triggered.connect(lambda: self._show_lighting_import(item))

        menu.addSeparator()

        # Show in explorer
        if single_item:
            explorer_action = menu.addAction("Show in Explorer")
            explorer_action.triggered.connect(lambda: self._show_in_explorer(item))

        # Properties (single item only)
        if single_item:
            props_action = menu.addAction("Properties...")
            props_action.triggered.connect(lambda: self._show_properties(item))

        return menu
    
    def _build_version_menu(self, menu: QMenu, items: List[Any]) -> None:
        """Build version selection submenu."""
        # Get available versions for first item
        versions = self._get_available_versions(items[0])
        
        if not versions:
            action = menu.addAction("No versions available")
            action.setEnabled(False)
            return
        
        for version in versions[-10:]:  # Last 10 versions
            action = menu.addAction(version)
            action.triggered.connect(
                lambda checked, v=version: self._switch_version(items, v)
            )
    
    def _build_department_menu(self, menu: QMenu, items: List[Any]) -> None:
        """Build department selection submenu."""
        departments = ['comp', 'light', 'anim', 'fx']
        
        current_dept = None
        if self._dept_switcher:
            current_dept = self._dept_switcher.get_current_department(items[0])
        
        for dept in departments:
            action = menu.addAction(dept)
            action.setCheckable(True)
            action.setChecked(dept == current_dept)
            action.triggered.connect(
                lambda checked, d=dept: self._switch_department(items, d)
            )
    
    def _get_available_versions(self, item: Any) -> List[str]:
        """Get available versions for a track item."""
        # This would need to look up versions based on item's source path
        # For now, return placeholder
        return ['v001', 'v002', 'v003', 'v004', 'v005']
    
    def _switch_version(self, items: List[Any], version: str) -> None:
        """Switch selected items to specified version."""
        if not self._version_updater:
            return

        for item in items:
            self._version_updater.update_shot_version(item, version)

    def _switch_department(self, items: List[Any], department: str) -> None:
        """Switch selected items to specified department."""
        # Would need to rebuild source path with new department
        print(f"[ContextMenu] Switching {len(items)} items to {department}")

    def _go_previous_version(self, items: List[Any]) -> None:
        """Go to previous version for all items."""
        if not self._version_updater:
            return

        for item in items:
            current = self._version_updater.get_item_current_version(item)
            if current:
                prev_ver = VersionManager.decrement_version(current)
                if prev_ver:
                    self._version_updater.update_shot_version(item, prev_ver)

    def _go_next_version(self, items: List[Any]) -> None:
        """Go to next version for all items."""
        if not self._version_updater:
            return

        for item in items:
            current = self._version_updater.get_item_current_version(item)
            if current:
                next_ver = VersionManager.increment_version(current)
                self._version_updater.update_shot_version(item, next_ver)

    def _go_latest_version(self, items: List[Any]) -> None:
        """Go to latest version for all items."""
        if not self._version_updater:
            return

        for item in items:
            versions = self._get_available_versions(item)
            if versions:
                latest = VersionManager.get_latest_version(versions)
                self._version_updater.update_shot_version(item, latest)

    def _show_lighting_import(self, item: Any) -> None:
        """Show lighting import dialog for the selected item."""
        if not self._lighting_scanner:
            QMessageBox.warning(None, "Error", "Project scanner not initialized.")
            return

        try:
            # Get shot info from track item
            shot_info = self._lighting_scanner.get_shot_info_from_track_item(item)

            if not shot_info:
                QMessageBox.warning(
                    None, "Error",
                    "Could not determine shot information from selected item."
                )
                return

            # Scan lighting department for this shot
            scan_result = self._lighting_scanner.scan_shot_lighting(
                shot_info['episode'],
                shot_info['sequence'],
                shot_info['shot']
            )

            if not scan_result.has_data:
                QMessageBox.information(
                    None, "No Lighting Renders",
                    f"No lighting renders found for {scan_result.shot_name}."
                )
                return

            # Show import dialog
            from .lighting_import_dialog import LightingImportDialog

            parent = hiero.ui.mainWindow() if HIERO_AVAILABLE else None
            dialog = LightingImportDialog(scan_result, parent)

            # Connect signal to handle import
            dialog.import_requested.connect(
                lambda passes: self._do_lighting_import(item, passes, scan_result)
            )

            dialog.exec_()

        except Exception as e:
            print(f"[ContextMenu] Error showing lighting import: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(None, "Error", f"Failed to open lighting import: {e}")

    def _do_lighting_import(self, source_item: Any, render_passes: list, scan_result) -> None:
        """
        Import selected lighting render passes to timeline2.

        Args:
            source_item: Original track item (for timecode reference)
            render_passes: List of RenderPassInfo to import
            scan_result: LightingScanResult for shot name
        """
        from .lighting_importer import LightingImporter

        try:
            importer = LightingImporter()
            result = importer.import_to_timeline2(
                source_item=source_item,
                render_passes=render_passes,
                shot_name=scan_result.shot_name,
                department_name=scan_result.department
            )

            if result.success:
                QMessageBox.information(
                    None, "Import Complete",
                    f"Successfully imported {result.clips_added} lighting render(s) to timeline2."
                )
            else:
                QMessageBox.warning(
                    None, "Import Failed",
                    f"Import failed: {', '.join(result.errors)}"
                )

        except Exception as e:
            print(f"[ContextMenu] Error importing lighting: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(None, "Error", f"Failed to import lighting: {e}")

    def _show_in_explorer(self, item: Any) -> None:
        """Open file location in system file explorer."""
        try:
            if HIERO_AVAILABLE:
                source = item.source()
                path = source.mediaSource().fileinfos()[0].filename()
            else:
                path = item.clip._path if hasattr(item, 'clip') else ""

            if not path:
                return

            # Get directory
            import os
            directory = os.path.dirname(path)

            # Open in explorer based on platform
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', '/select,', path])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', path])
            else:  # Linux
                subprocess.run(['xdg-open', directory])

        except Exception as e:
            print(f"[ContextMenu] Failed to open explorer: {e}")

    def _show_properties(self, item: Any) -> None:
        """Show properties dialog for item."""
        try:
            if HIERO_AVAILABLE:
                source = item.source()
                path = source.mediaSource().fileinfos()[0].filename()
                name = source.name()
            else:
                path = item.clip._path if hasattr(item, 'clip') else ""
                name = "Mock Item"

            version = VersionManager.parse_version(path) if path else None

            msg = f"Name: {name}\n"
            msg += f"Path: {path}\n"
            msg += f"Version: v{version:03d}" if version else "Version: Unknown"

            QMessageBox.information(None, "Shot Properties", msg)

        except Exception as e:
            QMessageBox.warning(None, "Error", f"Could not get properties: {e}")


def register_context_menu(scanner: Optional[ProjectScanner] = None) -> None:
    """
    Register context menu handler with Hiero.
    """
    if not HIERO_AVAILABLE:
        print("[ContextMenu] Hiero not available")
        return

    handler = TrackItemContextMenu(scanner)

    # Register with Hiero's event system
    def on_context_menu(event):
        """Handle context menu event."""
        items = event.sender.selection()
        if items:
            menu = handler.build_menu(items)
            # Add to event's menu
            for action in menu.actions():
                event.menu.addAction(action)

    # Register for timeline context menu events
    hiero.core.events.registerInterest(
        hiero.core.events.EventType.kShowContextMenu,
        on_context_menu
    )

    print("[ContextMenu] Context menu registered")

