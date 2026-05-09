from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QScrollArea,
                            QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFontMetrics
import qtawesome as qta
import time

from camera.webcam_thread import WebcamThread
from ui_model.inference_thread import InferenceThread
from ui_model.model_interface import GazeEstimator
from utils.drawing import draw_gaze_point
from utils.colors import (BG, SURFACE, PANEL, ACCENT, HIGHLIGHT,
                        TEAL, TEXT_PRIMARY, TEXT_SEC, BUTTON_STYLE)
import cv2


# ── Background Pattern Widget ─────────────────────────────
class BgPatternWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

    def _tick(self):
        self.offset += 0.3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        dot_spacing = 28
        dot_color = QColor(TEAL)
        dot_color.setAlpha(18)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)

        offset_x = int(self.offset) % dot_spacing
        offset_y = int(self.offset * 0.5) % dot_spacing

        for x in range(-dot_spacing, self.width() + dot_spacing, dot_spacing):
            for y in range(-dot_spacing, self.height() + dot_spacing, dot_spacing):
                painter.drawEllipse(x + offset_x, y + offset_y, 2, 2)

        line_color = QColor(HIGHLIGHT)
        line_color.setAlpha(30)
        painter.setPen(QPen(line_color, 1))

        painter.drawLine(0, 0, 60, 0)
        painter.drawLine(0, 0, 0, 60)
        painter.drawLine(self.width(), 0, self.width() - 60, 0)
        painter.drawLine(self.width(), 0, self.width(), 60)
        painter.drawLine(0, self.height(), 60, self.height())
        painter.drawLine(0, self.height(), 0, self.height() - 60)
        painter.drawLine(self.width(), self.height(), self.width() - 60, self.height())
        painter.drawLine(self.width(), self.height(), self.width(), self.height() - 60)

        painter.end()


# ── Gaze Trail Overlay ────────────────────────────────────
class GazeTrailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.trail        = []
        self.max_trail    = 25
        self.visible_trail = True

    def set_trail_length(self, length):
        self.max_trail = length
        if len(self.trail) > self.max_trail:
            self.trail = self.trail[-self.max_trail:]
        self.update()

    def set_trail_visible(self, visible):
        self.visible_trail = visible
        if not visible:
            self.trail = []
        self.update()

    def add_point(self, x, y):
        if not self.visible_trail:
            return
        self.trail.append([x, y, 255])
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        for i, point in enumerate(self.trail):
            point[2] = int(255 * (i + 1) / len(self.trail))
        self.update()

    def clear(self):
        self.trail = []
        self.update()

    def paintEvent(self, event):
        if len(self.trail) < 2 or not self.visible_trail:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for i in range(1, len(self.trail)):
            x1, y1, a1 = self.trail[i - 1]
            x2, y2, a2 = self.trail[i]

            color = QColor(TEAL)
            color.setAlpha(a2 // 2)
            painter.setPen(QPen(color, 2))
            painter.drawLine(x1, y1, x2, y2)

            dot_color = QColor(HIGHLIGHT)
            dot_color.setAlpha(a2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dot_color)
            radius = max(2, int(4 * a2 / 255))
            painter.drawEllipse(x2 - radius, y2 - radius,
                                radius * 2, radius * 2)

        painter.end()


# ── Glowing Card ──────────────────────────────────────────
class GlowCard(QWidget):
    def __init__(self, title, value="--", color=None):
        super().__init__()
        self.glow_color = color or TEAL
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(55)
        self.setMaximumHeight(75)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 6)
        layout.setSpacing(1)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"""
            color: {self.glow_color};
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        """)

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        self._apply_style(False)

    def _apply_style(self, glowing):
        alpha = "ff" if glowing else "55"
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid {self.glow_color}{alpha};
            }}
        """)

    def update_value(self, value):
        self.value_lbl.setText(str(value))
        self._apply_style(True)
        QTimer.singleShot(150, lambda: self._apply_style(False))


# ── Home Screen ───────────────────────────────────────────
class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")

        self.webcam_thread    = WebcamThread()
        self.estimator        = GazeEstimator()
        self.last_time        = time.time()
        self.session_seconds  = 0
        self.fps_enabled      = False
        self._frame_interval  = 0.0
        self._last_frame_time = 0.0
        self.on_session_start = None
        self.on_session_stop  = None
        self.on_gaze_update   = None

        # Inference runs in background thread — never blocks UI
        self.inference_thread = InferenceThread(self.estimator)
        self.inference_thread.result_ready.connect(self._on_inference_result)

        # WebcamThread sends frames to inference thread, NOT to update_frame
        self.webcam_thread.frame_ready.connect(self._on_frame_ready)
        self.webcam_thread.camera_unavailable.connect(self.show_no_camera)

        self._latest_frame = None  # for display only

        self._build_ui()
        QTimer.singleShot(100, self._update_model_card)

    def apply_trail_settings(self, trail_visible, trail_length):
        self.gaze_trail.set_trail_visible(trail_visible)
        self.gaze_trail.set_trail_length(trail_length)

    def apply_fps_settings(self, fps_enabled, fps_cap):
        self.fps_enabled = fps_enabled
        self._frame_interval = 1.0 / fps_cap if fps_enabled else 0.0
        
    def _update_model_card(self):
        """Updates model status card to reflect actual load state."""
        if self.estimator.is_loaded:
            self.model_card._text_lbl.setText("Model: Loaded ✅")
            self.model_card.setStyleSheet(f"""
                QWidget {{
                    background-color: {PANEL};
                    border-radius: 8px;
                    border: 1px solid {TEAL}55;
                }}
            """)
        else:
            self.model_card._text_lbl.setText("Model: Demo Mode ⚠️")

    def set_fc_weights(self, weight, bias):
        """
        Called by MainWindow after few-shot calibration completes.
        Updates the FC layer weights so live feed benefits too.
        """
        self.estimator.set_fc_weights(weight, bias)
        self.model_card._text_lbl.setText("Model: Calibrated ✅")
        self.model_card.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid #4caf5055;
            }}
        """)    

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

        self.status_icon = QLabel()
        self.status_icon.setPixmap(
            qta.icon("fa5s.circle", color=TEAL).pixmap(QSize(8, 8))
        )
        self.status_icon.setStyleSheet("background: transparent;")

        self.header_status = QLabel("SYSTEM READY")
        self.header_status.setStyleSheet(f"""
            color: {TEAL};
            font-size: 11px;
            letter-spacing: 1px;
            background: transparent;
        """)

        clock_icon = QLabel()
        clock_icon.setPixmap(
            qta.icon("fa5s.clock", color=TEXT_SEC).pixmap(QSize(12, 12))
        )
        clock_icon.setStyleSheet("background: transparent;")

        self.header_time = QLabel("")
        self.header_time.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 11px;
            background: transparent;
        """)

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        header_layout.addWidget(app_icon)
        header_layout.addSpacing(8)
        header_layout.addWidget(app_name)
        header_layout.addStretch()
        header_layout.addWidget(self.status_icon)
        header_layout.addSpacing(4)
        header_layout.addWidget(self.header_status)
        header_layout.addSpacing(24)
        header_layout.addWidget(clock_icon)
        header_layout.addSpacing(4)
        header_layout.addWidget(self.header_time)

        outer.addWidget(header)

        # ── MAIN CONTENT ──────────────────────────────
        content = QWidget()
        main_layout = QHBoxLayout(content)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # ── LEFT — Camera feed ────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)

        feed_header_layout = QHBoxLayout()
        feed_icon = QLabel()
        feed_icon.setPixmap(
            qta.icon("fa5s.video", color=TEXT_SEC).pixmap(QSize(12, 12))
        )
        feed_icon.setStyleSheet("background: transparent;")
        feed_lbl = QLabel("LIVE FEED")
        feed_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
        """)
        feed_header_layout.addWidget(feed_icon)
        feed_header_layout.addSpacing(6)
        feed_header_layout.addWidget(feed_lbl)
        feed_header_layout.addStretch()

        # Video container — fully responsive, no fixed size
        self.video_container = QWidget()
        self.video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.video_container.setStyleSheet(f"""
            background-color: {PANEL};
            border: 1px solid {ACCENT};
            border-radius: 12px;
        """)

        self.bg_pattern = BgPatternWidget(self.video_container)

        self.video_label = QLabel("Camera feed will appear here",
                                self.video_container)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            background: transparent;
            color: #4a5568;
            font-size: 13px;
        """)

        self.gaze_trail = GazeTrailWidget(self.video_container)

        # Buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("  Start Camera")
        self.start_btn.setIcon(qta.icon("fa5s.play", color="#ffffff"))
        self.start_btn.setIconSize(QSize(13, 13))

        self.stop_btn = QPushButton("  Stop Camera")
        self.stop_btn.setIcon(qta.icon("fa5s.stop", color="#ffffff"))
        self.stop_btn.setIconSize(QSize(13, 13))
        self.stop_btn.setEnabled(False)

        for btn in [self.start_btn, self.stop_btn]:
            btn.setFixedHeight(40)
            btn.setStyleSheet(BUTTON_STYLE)
            btn_layout.addWidget(btn)

        self.start_btn.clicked.connect(self.start_camera)
        self.stop_btn.clicked.connect(self.stop_camera)

        left.addLayout(feed_header_layout)
        left.addWidget(self.video_container, 1)
        left.addLayout(btn_layout)

        # ── RIGHT — Scrollable info panel ─────────────
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
        right = QVBoxLayout(right_widget)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)
        right.setSpacing(6)
        right.setContentsMargins(0, 0, 6, 0)

        right_scroll = QScrollArea()
        right_scroll.setWidget(right_widget)
        right_scroll.setWidgetResizable(True)
        right_scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
        right_scroll.setMinimumWidth(180)
        right_scroll.setMaximumWidth(240)
        right_scroll.setStyleSheet(f"""
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

        # GAZE DATA section
        right.addWidget(self._section_header("GAZE DATA", "fa5s.eye"))
        self.model_card  = self._status_card(
            "Model: Not Loaded", "fa5s.brain",  "#c01c37")
        self.camera_card = self._status_card(
            "Camera: Off",       "fa5s.camera", TEXT_SEC)
        right.addWidget(self.model_card)
        right.addWidget(self.camera_card)
        right.addWidget(self._divider())

        # COORDINATES section
        right.addWidget(self._section_header("COORDINATES", "fa5s.crosshairs"))
        self.gaze_x_card = GlowCard("GAZE X", "--", TEAL)
        self.gaze_y_card = GlowCard("GAZE Y", "--", TEAL)
        self.fps_card    = GlowCard("FPS",    "--", "#3498db")
        right.addWidget(self.gaze_x_card)
        right.addWidget(self.gaze_y_card)
        right.addWidget(self.fps_card)
        right.addWidget(self._divider())

        # SESSION section
        right.addWidget(self._section_header("SESSION", "fa5s.stopwatch"))
        self.duration_card = GlowCard("DURATION", "00:00", "#7e2d9e")
        self.blinks_card   = GlowCard("BLINKS",   "0",     "#a1f407")
        right.addWidget(self.duration_card)
        right.addWidget(self.blinks_card)
        right.addStretch()

        main_layout.addLayout(left, 3)
        main_layout.addWidget(right_scroll, 1)

        outer.addWidget(content, 1)

        # Session timer
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._tick_session)

    def resizeEvent(self, event):
        w = self.video_container.width()
        h = self.video_container.height()
        self.bg_pattern.setGeometry(0, 0, w, h)
        self.video_label.setGeometry(0, 0, w, h)
        self.gaze_trail.setGeometry(0, 0, w, h)
        super().resizeEvent(event)

    def _section_header(self, text, icon_name=None):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(
                qta.icon(icon_name, color=TEXT_SEC).pixmap(QSize(10, 10))
            )
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)

        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
        """)
        layout.addWidget(lbl)
        layout.addStretch()
        return container

    def _divider(self):
        d = QLabel()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {ACCENT};")
        return d

    def _status_card(self, text, icon_name=None, icon_color=None):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid {ACCENT}55;
            }}
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(8)

        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(
                qta.icon(icon_name, color=icon_color or TEXT_SEC)
                .pixmap(QSize(14, 14))
            )
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"""
            color: #cccccc;
            font-size: 11px;
            background: transparent;
        """)
        layout.addWidget(text_lbl)
        layout.addStretch()

        widget._text_lbl = text_lbl
        return widget

    def _set_status(self, text, color):
        self.status_icon.setPixmap(
            qta.icon("fa5s.circle", color=color).pixmap(QSize(8, 8))
        )
        self.header_status.setText(text)
        self.header_status.setStyleSheet(f"""
            color: {color};
            font-size: 11px;
            letter-spacing: 1px;
            background: transparent;
        """)

    def _update_clock(self):
        self.header_time.setText(time.strftime("%H:%M:%S"))

    def _tick_session(self):
        self.session_seconds += 1
        mins = self.session_seconds // 60
        secs = self.session_seconds % 60
        self.duration_card.update_value(f"{mins:02}:{secs:02}")

    
    def _on_frame_ready(self, frame):
        """Receive webcam frame — send to inference, update display."""
        self._latest_frame = frame
        self.inference_thread.update_frame(frame)
        
        # Always display latest raw frame immediately for smooth video
        self._display_frame(frame)


    def _on_inference_result(self, gaze_x, gaze_y, fps):
        frame = self._latest_frame
        if frame is None:
            return

        # Flip only the x coordinate for display
        display_x = 1.0 - gaze_x

        try:
            display = draw_gaze_point(frame.copy(), display_x, gaze_y)
            self._display_frame(display)
        except Exception:
            pass

        self.gaze_x_card.update_value(f"{gaze_x:.3f}")
        self.gaze_y_card.update_value(f"{gaze_y:.3f}")
        self.fps_card.update_value(f"{fps:.1f}")

        w = self.video_label.width()
        h = self.video_label.height()
        if w > 0 and h > 0:
            self.gaze_trail.add_point(int(display_x * w), int(gaze_y * h))

        if self.on_gaze_update:
            self.on_gaze_update(gaze_x, gaze_y, fps)
    # def _on_inference_result(self, gaze_x, gaze_y, fps):
    #     """Inference complete — draw gaze dot on latest frame."""
    #     # FOR DEBUGGING
    #     # print(f"[DEBUG] gaze=({gaze_x:.3f}, {gaze_y:.3f}) fps={fps:.1f}")
    #     frame = self._latest_frame
    #     if frame is None:
    #         return

    #     from utils.drawing import draw_gaze_point
    #     try:
    #         display = draw_gaze_point(frame.copy(), gaze_x, gaze_y)
    #         self._display_frame(display)
    #     except Exception:
    #         pass

    #     # Update cards
    #     self.gaze_x_card.update_value(f"{gaze_x:.3f}")
    #     self.gaze_y_card.update_value(f"{gaze_y:.3f}")
    #     self.fps_card.update_value(f"{fps:.1f}")

    #     # Update trail
    #     w = self.video_label.width()
    #     h = self.video_label.height()
    #     if w > 0 and h > 0:
    #         self.gaze_trail.add_point(int(gaze_x * w), int(gaze_y * h))


    #     if self.on_gaze_update:
    #         self.on_gaze_update(gaze_x, gaze_y, fps)

    def _display_frame(self, frame):
        """Display a BGR numpy frame in video_label."""
        from PyQt6.QtGui import QImage, QPixmap
        h_f, w_f, ch = frame.shape
        bytes_per_line = ch * w_f
        qt_img = QImage(frame.data, w_f, h_f, bytes_per_line,
                        QImage.Format.Format_RGB888)  # BGR directly
        pixmap = QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(pixmap)


    def _update_model_card(self):
        if self.estimator.is_loaded:
            self.model_card._text_lbl.setText("Model: Loaded ✅")
            self.model_card.setStyleSheet(f"""
                QWidget {{
                    background-color: {PANEL};
                    border-radius: 8px;
                    border: 1px solid {TEAL}55;
                }}
            """)
        else:
            self.model_card._text_lbl.setText("Model: Demo Mode ⚠️")

    def set_fc_weights(self, weight, bias):
        self.estimator.set_fc_weights(weight, bias)
        self.model_card._text_lbl.setText("Model: Calibrated ✅")
        self.model_card.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid #4caf5055;
            }}
        """)

    def show_no_camera(self):
        self.video_label.clear()
        self.video_label.setText("Camera feed will appear here")
        self.gaze_trail.clear()
        self.gaze_x_card.update_value("--")
        self.gaze_y_card.update_value("--")
        self.fps_card.update_value("--")

    def start_camera(self):
        if not self.inference_thread.isRunning():
            self.inference_thread.start()
        self.webcam_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.camera_card._text_lbl.setText("Camera: On")
        self.camera_card.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid {TEAL}55;
            }}
        """)
        self._set_status("CAMERA ACTIVE", TEAL)
        self.session_seconds = 0
        self.session_timer.start(1000)
        if self.on_session_start:
            self.on_session_start()

    def stop_camera(self):
        self.webcam_thread.stop()
        self.inference_thread.stop()    # stop background inference
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.camera_card._text_lbl.setText("Camera: Off")
        self.camera_card.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid {ACCENT}55;
            }}
        """)
        self._set_status("SYSTEM READY", TEAL)
        self.video_label.setText("Camera feed will appear here")
        self.gaze_trail.clear()
        self.session_timer.stop()
        if self.on_session_stop:
            self.on_session_stop()

    def closeEvent(self, event):
        self.webcam_thread.stop()
        self.inference_thread.stop()
        event.accept()
