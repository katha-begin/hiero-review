"""
Progress and Status Display Module
====================================
Progress tracking and status message display for long-running operations.
"""
from typing import Optional, Callable
from datetime import datetime
from enum import Enum

try:
    from PySide2.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QProgressBar, QTextEdit, QPushButton, QGroupBox,
    )
    from PySide2.QtCore import Qt, Signal, QTimer
    from PySide2.QtGui import QFont, QTextCursor
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            QProgressBar, QTextEdit, QPushButton, QGroupBox,
        )
        from PySide6.QtCore import Qt, Signal, QTimer
        from PySide6.QtGui import QFont, QTextCursor
    except ImportError:
        class QWidget:
            pass
        class Signal:
            def __init__(self, *args): pass


class MessageLevel(Enum):
    """Message severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


# Color mapping for message levels
LEVEL_COLORS = {
    MessageLevel.INFO: "#e0e0e0",
    MessageLevel.WARNING: "#ffd700",
    MessageLevel.ERROR: "#ff6b6b",
    MessageLevel.SUCCESS: "#90EE90",
}


class ProgressWidget(QWidget):
    """
    Progress bar with label and percentage display.
    """
    cancelled = Signal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._start_time: Optional[datetime] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Operation label
        self.operation_label = QLabel("Ready")
        layout.addWidget(self.operation_label)
        
        # Progress bar with percentage
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar, 1)
        
        self.time_label = QLabel("")
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.time_label)
        
        layout.addLayout(progress_layout)
    
    def set_indeterminate(self, message: str = "Working...") -> None:
        """Set indeterminate (spinning) progress."""
        self.operation_label.setText(message)
        self.progress_bar.setRange(0, 0)
        self.time_label.setText("")
        self._start_time = datetime.now()
    
    def set_progress(self, current: int, total: int, message: str = "") -> None:
        """Set determinate progress."""
        if message:
            self.operation_label.setText(message)
        
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        
        # Calculate ETA
        if self._start_time and current > 0:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            estimated_total = elapsed * total / current
            remaining = estimated_total - elapsed
            
            if remaining > 60:
                self.time_label.setText(f"~{int(remaining/60)}m remaining")
            else:
                self.time_label.setText(f"~{int(remaining)}s remaining")
        else:
            self.time_label.setText("")
    
    def set_complete(self, message: str = "Complete") -> None:
        """Set progress to complete state."""
        self.operation_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if self._start_time:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            self.time_label.setText(f"{elapsed:.1f}s")
        self._start_time = None
    
    def reset(self) -> None:
        """Reset progress to initial state."""
        self.operation_label.setText("Ready")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.time_label.setText("")
        self._start_time = None
    
    def start_timing(self) -> None:
        """Start timing for progress calculation."""
        self._start_time = datetime.now()


class StatusLogWidget(QWidget):
    """
    Color-coded status log with timestamps.
    """
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._max_lines = 500
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit { 
                background-color: #1e1e1e; 
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

    def log(self, message: str, level: MessageLevel = MessageLevel.INFO) -> None:
        """Add a log message."""
        color = LEVEL_COLORS.get(level, LEVEL_COLORS[MessageLevel.INFO])
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format message with HTML
        html = f'<span style="color:#888">[{timestamp}]</span> '
        html += f'<span style="color:{color}">{message}</span><br>'

        # Append and scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.insertHtml(html)
        self.log_text.ensureCursorVisible()

        # Trim old lines if needed
        if self.log_text.document().lineCount() > self._max_lines:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.removeSelectedText()

    def info(self, message: str) -> None:
        """Log info message."""
        self.log(message, MessageLevel.INFO)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.log(message, MessageLevel.WARNING)

    def error(self, message: str) -> None:
        """Log error message."""
        self.log(message, MessageLevel.ERROR)

    def success(self, message: str) -> None:
        """Log success message."""
        self.log(message, MessageLevel.SUCCESS)

    def clear(self) -> None:
        """Clear the log."""
        self.log_text.clear()

    def set_max_lines(self, max_lines: int) -> None:
        """Set maximum number of log lines to keep."""
        self._max_lines = max_lines


class ProgressPanel(QGroupBox):
    """
    Combined progress and status panel.
    """
    cancelled = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__("Progress", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Progress widget
        self.progress = ProgressWidget()
        layout.addWidget(self.progress)

        # Cancel button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(lambda: self.cancelled.emit())
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Status log
        self.log = StatusLogWidget()
        layout.addWidget(self.log)

    def set_busy(self, busy: bool) -> None:
        """Set busy state."""
        self.cancel_btn.setEnabled(busy)
        if not busy:
            self.progress.reset()

    def start_operation(self, message: str) -> None:
        """Start a new operation."""
        self.progress.start_timing()
        self.progress.set_indeterminate(message)
        self.log.info(f"Started: {message}")
        self.cancel_btn.setEnabled(True)

    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update operation progress."""
        self.progress.set_progress(current, total, message)

    def complete_operation(self, message: str = "Complete") -> None:
        """Mark operation as complete."""
        self.progress.set_complete(message)
        self.log.success(message)
        self.cancel_btn.setEnabled(False)

    def fail_operation(self, message: str) -> None:
        """Mark operation as failed."""
        self.progress.reset()
        self.log.error(f"Failed: {message}")
        self.cancel_btn.setEnabled(False)


def create_progress_callback(panel: ProgressPanel) -> Callable:
    """Create a callback function for progress updates."""
    def callback(message: str, current: int, total: int):
        if total > 0:
            panel.update_progress(current, total, message)
        else:
            panel.progress.set_indeterminate(message)
    return callback

