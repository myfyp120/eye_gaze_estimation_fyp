from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QScrollArea)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor
import qtawesome as qta

from utils.colors import (BG, SURFACE, PANEL, ACCENT, HIGHLIGHT, TEAL, TEXT_PRIMARY, TEXT_SEC)


class ToggleSwitch(QWidget):
    def __init__(self, checked=False, on_change=None):
        super().__init__()
        self.setFixedSize(52, 28)
        self._checked = checked
        self._on_change = on_change
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def is_checked(self):
        return self._checked

    def set_checked(self, val):
        self._checked = val
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        if self._on_change:
            self._on_change()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_color = QColor(TEAL) if self._checked else QColor(ACCENT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 4, 52, 20, 10, 10)
        thumb_x = 28 if self._checked else 4
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(thumb_x, 2, 24, 24)
        painter.end()


class SettingsCard(QWidget):
    def __init__(self, title, icon_name, icon_color):
        super().__init__()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 10px;
                border: 1px solid {ACCENT}55;
            }}
        """)
        self.inner_layout = QVBoxLayout(self)
        self.inner_layout.setContentsMargins(16, 14, 16, 14)
        self.inner_layout.setSpacing(14)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icon_name, color=icon_color).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {icon_color};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
        """)
        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()
        self.inner_layout.addLayout(header)

        div = QLabel()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {ACCENT};")
        self.inner_layout.addWidget(div)

    def add_row(self, widget):
        self.inner_layout.addWidget(widget)


def make_row(label, sublabel, control_widget):
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)

    lbl = QLabel(label)
    lbl.setStyleSheet(f"""
        color: {TEXT_PRIMARY};
        font-size: 13px;
        background: transparent;
    """)
    sub = QLabel(sublabel)
    sub.setStyleSheet(f"""
        color: {TEXT_SEC};
        font-size: 11px;
        background: transparent;
    """)
    text_col.addWidget(lbl)
    text_col.addWidget(sub)

    layout.addLayout(text_col)
    layout.addStretch()
    layout.addWidget(control_widget)
    return row


def make_slider(min_val, max_val, default, color):
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setValue(default)
    slider.setFixedWidth(140)
    slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            height: 4px;
            background: {ACCENT};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {color};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{
            background: {color};
            border-radius: 2px;
        }}
    """)
    return slider


class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        self._unsaved = False
        self._build_ui()

    def _mark_unsaved(self):
        self._unsaved = True
        self.unsaved_container.setVisible(True)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── HEADER ────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"""
            background-color: {SURFACE};
            border-bottom: 1px solid {ACCENT};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        app_icon = QLabel()
        app_icon.setPixmap(
            qta.icon("fa5s.eye", color=HIGHLIGHT).pixmap(QSize(16, 16))
        )
        app_icon.setStyleSheet("background: transparent;")

        app_name = QLabel("THROUGH THE IRIS")
        app_name.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 3px;
            background: transparent;
        """)

        unsaved_dot = QLabel()
        unsaved_dot.setPixmap(
            qta.icon("fa5s.circle", color="#f39c12").pixmap(QSize(8, 8))
        )
        unsaved_dot.setStyleSheet("background: transparent;")

        self.unsaved_lbl = QLabel("Unsaved changes")
        self.unsaved_lbl.setStyleSheet(f"""
            color: #f39c12;
            font-size: 11px;
            letter-spacing: 1px;
            background: transparent;
        """)

        self.unsaved_container = QWidget()
        self.unsaved_container.setStyleSheet("background: transparent;")
        unsaved_layout = QHBoxLayout(self.unsaved_container)
        unsaved_layout.setContentsMargins(0, 0, 0, 0)
        unsaved_layout.setSpacing(6)
        unsaved_layout.addWidget(unsaved_dot)
        unsaved_layout.addWidget(self.unsaved_lbl)
        self.unsaved_container.setVisible(False)

        page_name = QLabel("SETTINGS")
        page_name.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 11px;
            letter-spacing: 2px;
            background: transparent;
        """)

        header_layout.addWidget(app_icon)
        header_layout.addSpacing(8)
        header_layout.addWidget(app_name)
        header_layout.addStretch()
        header_layout.addWidget(self.unsaved_container)
        header_layout.addSpacing(16)
        header_layout.addWidget(page_name)
        outer.addWidget(header)

        # ── SCROLLABLE CONTENT ────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {SURFACE};
                width: 4px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {ACCENT};
                border-radius: 2px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background-color: {BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 24, 30, 24)
        content_layout.setSpacing(16)

        page_title = QLabel("Settings")
        page_title.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        """)
        page_sub = QLabel("Configure your gaze estimation system")
        page_sub.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 13px;
            background: transparent;
        """)
        content_layout.addWidget(page_title)
        content_layout.addWidget(page_sub)
        content_layout.addSpacing(8)

        # ── GAZE CONTROL CARD ─────────────────────────
        gaze_card = SettingsCard("GAZE CONTROL", "fa5s.crosshairs", "#00d4aa")

        self.gaze_toggle = ToggleSwitch(
            checked=False, on_change=self._mark_unsaved
        )
        gaze_card.add_row(make_row(
            "Enable Gaze Control",
            "Control mouse with your gaze",
            self.gaze_toggle
        ))

        self.smooth_slider = make_slider(0, 10, 5, TEAL)
        self.smooth_label  = QLabel("5")
        self.smooth_label.setFixedWidth(24)
        self.smooth_label.setStyleSheet(
            f"color: {TEAL}; background: transparent; font-size: 12px;"
        )
        self.smooth_slider.valueChanged.connect(
            lambda v: [self.smooth_label.setText(str(v)), self._mark_unsaved()]
        )

        smooth_control = QWidget()
        smooth_control.setStyleSheet("background: transparent;")
        smooth_layout = QHBoxLayout(smooth_control)
        smooth_layout.setContentsMargins(0, 0, 0, 0)
        smooth_layout.setSpacing(8)
        smooth_layout.addWidget(self.smooth_slider)
        smooth_layout.addWidget(self.smooth_label)

        gaze_card.add_row(make_row(
            "Gaze Smoothing",
            "0 = off, 10 = maximum smoothing",
            smooth_control
        ))

        self.dwell_slider = make_slider(5, 50, 15, "#f39c12")
        self.dwell_label  = QLabel("1.5s")
        self.dwell_label.setFixedWidth(36)
        self.dwell_label.setStyleSheet(
            f"color: #f39c12; background: transparent; font-size: 12px;"
        )
        self.dwell_slider.valueChanged.connect(
            lambda v: [self.dwell_label.setText(f"{v/10:.1f}s"), self._mark_unsaved()]
        )

        dwell_control = QWidget()
        dwell_control.setStyleSheet("background: transparent;")
        dwell_layout = QHBoxLayout(dwell_control)
        dwell_layout.setContentsMargins(0, 0, 0, 0)
        dwell_layout.setSpacing(8)
        dwell_layout.addWidget(self.dwell_slider)
        dwell_layout.addWidget(self.dwell_label)

        gaze_card.add_row(make_row(
            "Dwell Time",
            "How long to look at target to trigger click",
            dwell_control
        ))
        content_layout.addWidget(gaze_card)

        # ── BLINK CARD ────────────────────────────────
        blink_card = SettingsCard("BLINK DETECTION", "fa5s.eye", "#9b59b6")

        self.blink_toggle = ToggleSwitch(
            checked=True, on_change=self._mark_unsaved
        )
        blink_card.add_row(make_row(
            "Enable Blink Detection",
            "Detect blinks for triggering actions",
            self.blink_toggle
        ))

        self.blink_slider = make_slider(0, 10, 5, "#9b59b6")
        self.blink_label  = QLabel("5")
        self.blink_label.setFixedWidth(24)
        self.blink_label.setStyleSheet(
            f"color: #9b59b6; background: transparent; font-size: 12px;"
        )
        self.blink_slider.valueChanged.connect(
            lambda v: [self.blink_label.setText(str(v)), self._mark_unsaved()]
        )

        blink_control = QWidget()
        blink_control.setStyleSheet("background: transparent;")
        blink_layout = QHBoxLayout(blink_control)
        blink_layout.setContentsMargins(0, 0, 0, 0)
        blink_layout.setSpacing(8)
        blink_layout.addWidget(self.blink_slider)
        blink_layout.addWidget(self.blink_label)

        blink_card.add_row(make_row(
            "Blink Sensitivity",
            "0 = off, 10 = very sensitive",
            blink_control
        ))
        content_layout.addWidget(blink_card)

        # ── TRAIL CARD ────────────────────────────────
        trail_card = SettingsCard("GAZE TRAIL", "fa5s.bezier-curve", "#4fc3f7")

        self.trail_toggle = ToggleSwitch(
            checked=True, on_change=self._mark_unsaved
        )
        trail_card.add_row(make_row(
            "Show Gaze Trail",
            "Display trail of recent gaze positions",
            self.trail_toggle
        ))

        self.trail_slider = make_slider(5, 50, 25, "#4fc3f7")
        self.trail_label  = QLabel("25")
        self.trail_label.setFixedWidth(24)
        self.trail_label.setStyleSheet(
            f"color: #4fc3f7; background: transparent; font-size: 12px;"
        )
        self.trail_slider.valueChanged.connect(
            lambda v: [self.trail_label.setText(str(v)), self._mark_unsaved()]
        )

        trail_control = QWidget()
        trail_control.setStyleSheet("background: transparent;")
        trail_layout = QHBoxLayout(trail_control)
        trail_layout.setContentsMargins(0, 0, 0, 0)
        trail_layout.setSpacing(8)
        trail_layout.addWidget(self.trail_slider)
        trail_layout.addWidget(self.trail_label)

        trail_card.add_row(make_row(
            "Trail Length",
            "5 = short, 50 = long",
            trail_control
        ))

        content_layout.addWidget(trail_card)

        # ── FPS CARD ──────────────────────────────────
        fps_card = SettingsCard("FPS LIMIT", "fa5s.tachometer-alt", "#3498db")

        self.fps_toggle = ToggleSwitch(
            checked=False, on_change=self._on_fps_toggle
        )
        fps_card.add_row(make_row(
            "Enable FPS Limit",
            "Cap processing rate to save CPU",
            self.fps_toggle
        ))

        self.fps_slider = make_slider(5, 60, 30, "#3498db")
        self.fps_slider.setEnabled(False)
        self.fps_slider.setStyleSheet(self._fps_slider_style(enabled=False))

        self.fps_label = QLabel("30")
        self.fps_label.setFixedWidth(36)
        self.fps_label.setStyleSheet(
            f"color: {TEXT_SEC}; background: transparent; font-size: 12px;"
        )
        self.fps_slider.valueChanged.connect(
            lambda v: [self.fps_label.setText(f"{v} fps"), self._mark_unsaved()]
        )

        fps_control = QWidget()
        fps_control.setStyleSheet("background: transparent;")
        fps_layout = QHBoxLayout(fps_control)
        fps_layout.setContentsMargins(0, 0, 0, 0)
        fps_layout.setSpacing(8)
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_label)

        fps_card.add_row(make_row(
            "FPS Cap",
            "Only active when FPS limit is enabled",
            fps_control
        ))

        content_layout.addWidget(fps_card)

        # ── APPEARANCE CARD ───────────────────────────
        appear_card = SettingsCard("APPEARANCE", "fa5s.paint-brush", "#e94560")

        self.theme_toggle = ToggleSwitch(
            checked=True, on_change=self._mark_unsaved
        )
        appear_card.add_row(make_row(
            "Dark Theme",
            "Light mode coming soon",
            self.theme_toggle
        ))
        content_layout.addWidget(appear_card)

        # ── BUTTONS ───────────────────────────────────
        save_btn = QPushButton("  Save Settings")
        save_btn.setIcon(qta.icon("fa5s.save", color="#000000"))
        save_btn.setIconSize(QSize(14, 14))
        save_btn.setFixedHeight(44)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {TEAL};
                color: #000000;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background-color: #00f5c4;
            }}
        """)
        save_btn.clicked.connect(self._save_settings)

        reset_btn = QPushButton("  Reset Defaults")
        reset_btn.setIcon(qta.icon("fa5s.undo", color=TEXT_SEC))
        reset_btn.setIconSize(QSize(14, 14))
        reset_btn.setFixedHeight(44)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_SEC};
                border-radius: 8px;
                font-size: 13px;
                border: 1px solid {ACCENT};
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
        """)
        reset_btn.clicked.connect(self._reset_defaults)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(save_btn)

        content_layout.addSpacing(8)
        content_layout.addLayout(btn_row)
        content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _fps_slider_style(self, enabled):
        color = "#3498db" if enabled else TEXT_SEC
        return f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {ACCENT};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 2px;
            }}
        """

    def _on_fps_toggle(self):
        enabled = self.fps_toggle.is_checked()
        self.fps_slider.setEnabled(enabled)
        self.fps_slider.setStyleSheet(self._fps_slider_style(enabled=enabled))
        self.fps_label.setStyleSheet(
            f"color: {'#3498db' if enabled else TEXT_SEC}; "
            f"background: transparent; font-size: 12px;"
        )
        self._mark_unsaved()

    def _save_settings(self):
        self._unsaved = False
        self.unsaved_container.setVisible(False)
        print(f"Gaze control: {self.gaze_toggle.is_checked()}")
        print(f"Smoothing: {self.smooth_slider.value()}")
        print(f"Dwell time: {self.dwell_slider.value() / 10}s")
        print(f"Blink detection: {self.blink_toggle.is_checked()}")
        print(f"Blink sensitivity: {self.blink_slider.value()}")
        print(f"Trail visible: {self.trail_toggle.is_checked()}")
        print(f"Trail length: {self.trail_slider.value()}")
        print(f"FPS limit enabled: {self.fps_toggle.is_checked()}")
        print(f"FPS cap: {self.fps_slider.value()}")
        if hasattr(self, 'on_save') and self.on_save:
            self.on_save()

    def _reset_defaults(self):
        self.smooth_slider.setValue(5)
        self.dwell_slider.setValue(15)
        self.blink_slider.setValue(5)
        self.trail_slider.setValue(25)
        self.fps_slider.setValue(30)
        self.trail_toggle.set_checked(True)
        self.gaze_toggle.set_checked(False)
        self.blink_toggle.set_checked(True)
        self.theme_toggle.set_checked(True)
        self.fps_toggle.set_checked(False)
        self._on_fps_toggle()
        self._mark_unsaved()

    def get_trail_settings(self):
        return {
            "trail_visible": self.trail_toggle.is_checked(),
            "trail_length":  self.trail_slider.value(),
        }
    
    def get_fps_settings(self):
        return {
            "fps_enabled": self.fps_toggle.is_checked(),
            "fps_cap":     self.fps_slider.value(),
        }
    