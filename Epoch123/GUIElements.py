from PySide6.QtWidgets import QPushButton, QLineEdit, QSlider, QHBoxLayout, QLabel, QWidget, QSizePolicy, QComboBox
from PySide6.QtCore import Qt, Signal


class GuiWidget(QWidget):
    """
    A horizontal layout with a label and one or more GUI elements (e.g. input, combo, etc.).
    """
    def __init__(self, gui_elements=None, label_text=None, setFixedWidth=None):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        if label_text:
            self.label = QLabel(label_text)
            self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.label.setStyleSheet("color: white; font-size: 14px")
            self.layout.addWidget(self.label)

        if gui_elements is None:
            gui_elements = []
        for gui_element in gui_elements:
            self.layout.addWidget(gui_element)

        if setFixedWidth:
            self.setFixedWidth(setFixedWidth)

        # Adjust margins and spacing
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)


class Button(QPushButton):
    """
    A custom QPushButton with a specific style and optional callback.
    """
    def __init__(self, text, callback=None, setFixedWidth=None, setFixedHeight=None):
        super().__init__(text)
        self.styles = """
            QPushButton {
                background-color: #574B90;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 14px;
                margin: 2px 2px;
            }
            QPushButton:hover {
                background-color: #786FA6;
            }
        """
        self.setStyleSheet(self.styles)
        self.setCursor(Qt.PointingHandCursor)
        if setFixedWidth:
            self.setFixedWidth(setFixedWidth)
        if setFixedHeight:
            self.setFixedHeight(setFixedHeight)
        if callback:
            self.clicked.connect(callback)


class LineEdit(QLineEdit):
    """
    A custom QLineEdit with a specific style and optional fixed width and placeholder.
    """
    text_changed = Signal(str)  # Custom signal that emits the text

    def __init__(self, setFixedWidth=None, placeholder=None):
        super().__init__()
        styles = """QLineEdit { 
            border: 2px solid orange; 
            padding: 4px; 
        }"""
        self.setStyleSheet(styles)
        if setFixedWidth:
            self.setFixedWidth(setFixedWidth)
        if placeholder:
            self.setPlaceholderText(placeholder)
        # Forward the built-in signal to our custom signal
        self.textChanged.connect(self.text_changed.emit)


class Slider(QSlider):
    """
    A custom QSlider with a specific style and optional fixed width.
    """
    def __init__(self, orientation, min_val, max_val, interval, setFixedWidth=None):
        super().__init__(orientation)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 10px;
                background: #B0B0B0;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #574B90;
                border: 1px solid #999999;
                width: 18px;
                height: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        self.setMinimum(min_val)
        self.setMaximum(max_val)
        self.setTickInterval(interval)
        self.setCursor(Qt.PointingHandCursor)
        if setFixedWidth:
            self.setFixedWidth(setFixedWidth)


class CustomComboBox(QComboBox):
    """
    A custom QComboBox with specific styling.
    """
    def __init__(self, items=None):
        super().__init__()
        self.setStyleSheet("""
            QComboBox {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid gray;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        if items:
            self.add_items(items)

    def add_items(self, items):
        self.addItems(items)

    def set_on_change(self, callback):
        """Set the callback for when the selected index changes."""
        self.currentIndexChanged.connect(callback)
