# from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
# from PyQt6.QtCore import Qt, pyqtSignal, QSize
# from utils.colors import SURFACE, ACCENT, HIGHLIGHT, TEXT_SEC
# import qtawesome as qta


# class Sidebar(QWidget):
#     navigate = pyqtSignal(int)

#     ITEMS = [
#         ("fa5s.home",        "Home",        0, "#00d4aa"),
#         ("fa5s.chart-bar",   "Dashboard",   1, "#e94560"),
#         ("fa5s.crosshairs",  "Calibration", 2, "#f39c12"),
#         ("fa5s.cog",         "Settings",    3, "#3498db"),
#         ("fa5s.info-circle", "About",       4, "#9b59b6"),
#     ]

#     def __init__(self):
#         super().__init__()
#         self.setFixedWidth(65)
#         self.active_index = 0
#         self.buttons = []
#         self._build()
#         self._update_styles()

#     def _build(self):
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)
#         layout.setAlignment(Qt.AlignmentFlag.AlignTop)

#         for icon_name, tooltip, index, color in self.ITEMS:
#             btn = QPushButton()
#             btn.setFixedSize(65, 58)
#             btn.setIconSize(QSize(22, 22))
#             btn.setToolTip(tooltip)
#             btn.setCursor(Qt.CursorShape.PointingHandCursor)
#             btn.clicked.connect(lambda checked, i=index: self._on_click(i))
#             self.buttons.append((btn, icon_name, color))
#             layout.addWidget(btn)

#         layout.addStretch()

#         self.setStyleSheet(f"""
#             QWidget {{
#                 background-color: {SURFACE};
#                 border-right: 1px solid {ACCENT};
#             }}
#         """)

#     def _on_click(self, index):
#         self.active_index = index
#         self._update_styles()
#         self.navigate.emit(index)

#     def _update_styles(self):
#         for i, (btn, icon_name, color) in enumerate(self.buttons):
#             if i == self.active_index:
#                 btn.setIcon(qta.icon(icon_name, color=color))
#                 btn.setStyleSheet(f"""
#                     QPushButton {{
#                         background-color: {ACCENT};
#                         border: none;
#                         border-left: 3px solid {color};
#                     }}
#                 """)
#             else:
#                 btn.setIcon(qta.icon(icon_name, color=TEXT_SEC))
#                 btn.setStyleSheet(f"""
#                     QPushButton {{
#                         background-color: transparent;
#                         border: none;
#                     }}
#                     QPushButton:hover {{
#                         background-color: {ACCENT};
#                         border-left: 3px solid {color};
#                     }}
#                 """)
#                 btn.enterEvent = lambda e, b=btn, n=icon_name, c=color: (
#                     b.setIcon(qta.icon(n, color=c))
#                 )
#                 btn.leaveEvent = lambda e, b=btn, n=icon_name: (
#                     b.setIcon(qta.icon(n, color=TEXT_SEC))
#                 )

#     def set_active(self, index):
#         self.active_index = index
#         self._update_styles()

# ui/components/sidebar.py — complete replacement
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from utils.colors import SURFACE, ACCENT, HIGHLIGHT, TEXT_SEC
import qtawesome as qta


class Sidebar(QWidget):
    navigate = pyqtSignal(int)

    ITEMS = [
        ("fa5s.home",         "Home",          0, "#00d4aa"),
        ("fa5s.chart-bar",    "Dashboard",     1, "#e94560"),
        ("fa5s.crosshairs",   "Calibration",   2, "#f39c12"),
        ("fa5s.cog",          "Settings",      3, "#3498db"),
        ("fa5s.info-circle",  "About",         4, "#9b59b6"),
        ("fa5s.bullseye",     "Test Accuracy", 5, "#e74c3c"),
    ]

    def __init__(self):
        super().__init__()
        self.setFixedWidth(65)
        self.active_index = 0
        self.buttons      = []
        self._build()
        self._update_styles()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for icon_name, tooltip, index, color in self.ITEMS:
            btn = QPushButton()
            btn.setFixedSize(65, 58)
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda checked, i=index: self._on_click(i))
            self.buttons.append((btn, icon_name, color))
            layout.addWidget(btn)

        layout.addStretch()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-right: 1px solid {ACCENT};
            }}
        """)

    def _on_click(self, index):
        self.active_index = index
        self._update_styles()
        self.navigate.emit(index)

    def _update_styles(self):
        for i, (btn, icon_name, color) in enumerate(self.buttons):
            if i == self.active_index:
                btn.setIcon(qta.icon(icon_name, color=color))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {ACCENT};
                        border: none;
                        border-left: 3px solid {color};
                    }}
                """)
            else:
                btn.setIcon(qta.icon(icon_name, color=TEXT_SEC))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border: none;
                    }}
                    QPushButton:hover {{
                        background-color: {ACCENT};
                        border-left: 3px solid {color};
                    }}
                """)
                btn.enterEvent = lambda e, b=btn, n=icon_name, c=color: \
                    b.setIcon(qta.icon(n, color=c))
                btn.leaveEvent = lambda e, b=btn, n=icon_name: \
                    b.setIcon(qta.icon(n, color=TEXT_SEC))

    def set_active(self, index):
        self.active_index = index
        self._update_styles()