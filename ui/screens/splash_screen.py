from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
import math
import random

from utils.colors import BG, HIGHLIGHT, TEAL, TEXT_SEC, TEXT_PRIMARY, ACCENT


# ── Particle System ───────────────────────────────────────
class Particle:
    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self.reset()

    def reset(self):
        self.x     = random.uniform(0, self.width)
        self.y     = random.uniform(0, self.height)
        self.vx    = random.uniform(-0.3, 0.3)
        self.vy    = random.uniform(-0.5, -0.1)
        self.size  = random.uniform(1.5, 3.5)
        self.alpha = random.randint(40, 120)
        self.color = random.choice([HIGHLIGHT, TEAL, "#ffffff"])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 0.4
        if self.y < 0 or self.alpha <= 0:
            self.reset()
            self.y = self.height


class ParticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.particles = []

        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(30)

    def _init_particles(self):
        self.particles = [
            Particle(self.width(), self.height())
            for _ in range(60)
        ]
        # Spread them out initially
        for p in self.particles:
            p.y = random.uniform(0, self.height())

    def showEvent(self, event):
        self._init_particles()

    def _update(self):
        for p in self.particles:
            p.update()
        self.update()

    def paintEvent(self, event):
        if not self.particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self.particles:
            color = QColor(p.color)
            color.setAlpha(int(p.alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(
                int(p.x - p.size),
                int(p.y - p.size),
                int(p.size * 2),
                int(p.size * 2)
            )
        painter.end()

# ── Decorative Crosshairs ─────────────────────────────────
class DecorWidget(QWidget):
    """Draws small static crosshair symbols scattered around the screen"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.crosshairs = []

        # Pulse animation
        self.pulse = 0.0
        self.pulse_dir = 1
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(50)

    def _init_crosshairs(self):
        """Generate random crosshair positions avoiding the center"""
        self.crosshairs = []
        cx = self.width()  // 2
        cy = self.height() // 2
        safe_r = 250  # avoid center where the eye and text are

        attempts = 0
        while len(self.crosshairs) < 18 and attempts < 200:
            x = random.randint(30, self.width()  - 30)
            y = random.randint(30, self.height() - 30)
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            if dist > safe_r:
                size    = random.choice([8, 10, 12, 14])
                alpha   = random.randint(25, 70)
                color   = random.choice([HIGHLIGHT, TEAL, TEXT_SEC])
                variant = random.choice(["full", "corner", "dot"])
                self.crosshairs.append((x, y, size, alpha, color, variant))
            attempts += 1

    def showEvent(self, event):
        self._init_crosshairs()

    def _update_pulse(self):
        self.pulse += 0.05 * self.pulse_dir
        if self.pulse >= 1.0:
            self.pulse_dir = -1
        elif self.pulse <= 0.0:
            self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        if not self.crosshairs:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for x, y, size, base_alpha, color, variant in self.crosshairs:
            # Pulse affects alpha slightly
            alpha = int(base_alpha + self.pulse * 20)
            alpha = max(0, min(255, alpha))

            c = QColor(color)
            c.setAlpha(alpha)
            pen = QPen(c, 1)
            painter.setPen(pen)

            half = size // 2
            gap  = size // 4  # gap in center of crosshair

            if variant == "full":
                # Full crosshair with center gap
                painter.drawLine(x - half, y, x - gap, y)   # left
                painter.drawLine(x + gap,  y, x + half, y)  # right
                painter.drawLine(x, y - half, x, y - gap)   # top
                painter.drawLine(x, y + gap,  x, y + half)  # bottom

                # Outer circle
                c2 = QColor(color)
                c2.setAlpha(alpha // 2)
                painter.setPen(QPen(c2, 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(x - half, y - half, size, size)

            elif variant == "corner":
                # Just 4 corner brackets
                b = size // 3  # bracket length
                painter.drawLine(x - half, y - half, x - half + b, y - half)  # top left h
                painter.drawLine(x - half, y - half, x - half,     y - half + b)  # top left v
                painter.drawLine(x + half, y - half, x + half - b, y - half)  # top right h
                painter.drawLine(x + half, y - half, x + half,     y - half + b)  # top right v
                painter.drawLine(x - half, y + half, x - half + b, y + half)  # bot left h
                painter.drawLine(x - half, y + half, x - half,     y + half - b)  # bot left v
                painter.drawLine(x + half, y + half, x + half - b, y + half)  # bot right h
                painter.drawLine(x + half, y + half, x + half,     y + half - b)  # bot right v

            elif variant == "dot":
                # Simple dot with two tiny tick marks
                painter.setBrush(QColor(color) if alpha > 30 else Qt.BrushStyle.NoBrush)
                painter.setPen(Qt.PenStyle.NoPen)
                dot_c = QColor(color)
                dot_c.setAlpha(alpha)
                painter.setBrush(dot_c)
                painter.drawEllipse(x - 2, y - 2, 4, 4)

                painter.setPen(QPen(c, 1))
                painter.drawLine(x - half, y, x - gap, y)
                painter.drawLine(x + gap,  y, x + half, y)

        painter.end()


# ── Eye Widget ────────────────────────────────────────────
class EyeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.blink_progress = 0.0
        self.iris_angle     = 0.0
        self.is_blinking    = False

        self.rotate_timer = QTimer()
        self.rotate_timer.timeout.connect(self._rotate_iris)
        self.rotate_timer.start(30)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._start_blink)
        self.blink_timer.start(3000)

        self.blink_anim_timer = QTimer()
        self.blink_anim_timer.timeout.connect(self._animate_blink)

        self.blink_closing = True
        self.blink_speed   = 0.15

    def _rotate_iris(self):
        self.iris_angle += 0.5
        if self.iris_angle >= 360:
            self.iris_angle = 0
        self.update()

    def _start_blink(self):
        if not self.is_blinking:
            self.is_blinking   = True
            self.blink_closing = True
            self.blink_anim_timer.start(16)

    def _animate_blink(self):
        if self.blink_closing:
            self.blink_progress += self.blink_speed
            if self.blink_progress >= 1.0:
                self.blink_progress = 1.0
                self.blink_closing  = False
        else:
            self.blink_progress -= self.blink_speed
            if self.blink_progress <= 0.0:
                self.blink_progress = 0.0
                self.is_blinking    = False
                self.blink_anim_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy   = 100, 100
        eye_w    = 140
        eye_h    = 70

        # Outer glow
        for i in range(3):
            glow_color = QColor(HIGHLIGHT)
            glow_color.setAlpha(20 - i * 6)
            painter.setPen(QPen(glow_color, 8 - i * 2))
            painter.drawEllipse(
                cx - eye_w // 2 - i * 4,
                cy - eye_h // 2 - i * 4,
                eye_w + i * 8,
                eye_h + i * 8
            )

        blink_offset = int(self.blink_progress * (eye_h // 2 + 5))

        # Eye background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BG))
        painter.drawEllipse(cx - eye_w // 2, cy - eye_h // 2, eye_w, eye_h)

        if self.blink_progress < 1.0:
            # Iris
            iris_r = 28
            painter.setBrush(QColor(ACCENT))
            painter.drawEllipse(cx - iris_r, cy - iris_r, iris_r * 2, iris_r * 2)

            # Iris pattern
            painter.setPen(QPen(QColor(TEAL), 1.5))
            for i in range(8):
                angle = math.radians(self.iris_angle + i * 45)
                x1 = cx + int(10 * math.cos(angle))
                y1 = cy + int(10 * math.sin(angle))
                x2 = cx + int(iris_r * math.cos(angle))
                y2 = cy + int(iris_r * math.sin(angle))
                painter.drawLine(x1, y1, x2, y2)

            # Pupil
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#000000"))
            painter.drawEllipse(cx - 10, cy - 10, 20, 20)

            # Highlight
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawEllipse(cx - 5, cy - 8, 6, 6)

        # Eyelids during blink
        if blink_offset > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(BG))
            painter.drawRect(
                cx - eye_w // 2 - 5,
                cy - eye_h // 2 - 5,
                eye_w + 10,
                eye_h // 2 + blink_offset
            )
            painter.drawRect(
                cx - eye_w // 2 - 5,
                cy,
                eye_w + 10,
                eye_h // 2 + blink_offset
            )

        # Eye outline
        painter.setPen(QPen(QColor(HIGHLIGHT), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - eye_w // 2, cy - eye_h // 2, eye_w, eye_h)

        # Pulse ring
        painter.setPen(QPen(QColor(TEAL), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - 50, cy - 50, 100, 100)


# ── Splash Screen ─────────────────────────────────────────
class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self._start_sequence()

    def _build_ui(self):
        # ── Particle layer (sits behind everything) ───
        self.particle_widget = ParticleWidget(self)
        self.particle_widget.setGeometry(0, 0, 900, 600)

        # ── Decorative crosshairs layer ───────────────
        self.decor_widget = DecorWidget(self)
        self.decor_widget.setGeometry(0, 0, 900, 600)

        # ── Main content layout ───────────────────────
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Eye graphic
        eye_container = QWidget()
        eye_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        eye_layout = QVBoxLayout(eye_container)
        eye_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eye_widget = EyeWidget()
        eye_layout.addWidget(
            self.eye_widget,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(eye_container)

        # Title
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 38px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 4px;
            background: transparent;
        """)
        layout.addWidget(self.title_label)

        # Tagline
        self.tagline_label = QLabel("")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tagline_label.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 14px;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 3px;
            background: transparent;
        """)
        layout.addWidget(self.tagline_label)

        # Loading bar
        self.loading_bar_bg = QWidget()
        self.loading_bar_bg.setFixedSize(300, 3)
        self.loading_bar_bg.setStyleSheet(
            f"background-color: {ACCENT}; border-radius: 2px;"
        )
        self.loading_bar = QWidget(self.loading_bar_bg)
        self.loading_bar.setFixedSize(0, 3)
        self.loading_bar.setStyleSheet(
            f"background-color: {HIGHLIGHT}; border-radius: 2px;"
        )

        bar_container = QWidget()
        bar_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        bar_layout = QVBoxLayout(bar_container)
        bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(self.loading_bar_bg)
        layout.addWidget(bar_container)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {TEAL};
            font-size: 11px;
            letter-spacing: 2px;
            background: transparent;
        """)
        layout.addWidget(self.status_label)

    def resizeEvent(self, event):
        # Keep particle widget covering the full window
        self.particle_widget.setGeometry(0, 0, self.width(), self.height())
        self.decor_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def _start_sequence(self):
        self.title_text    = "THROUGH THE IRIS"
        self.tagline_text  = "see the world through your eyes"
        self.title_index   = 0
        self.tagline_index = 0
        QTimer.singleShot(500, self._start_title_typing)

    def _start_title_typing(self):
        self.title_timer = QTimer()
        self.title_timer.timeout.connect(self._type_title)
        self.title_timer.start(80)

    def _type_title(self):
        if self.title_index <= len(self.title_text):
            self.title_label.setText(self.title_text[:self.title_index])
            self.title_index += 1
        else:
            self.title_timer.stop()
            QTimer.singleShot(300, self._start_tagline_typing)

    def _start_tagline_typing(self):
        self.tagline_timer = QTimer()
        self.tagline_timer.timeout.connect(self._type_tagline)
        self.tagline_timer.start(50)

    def _type_tagline(self):
        if self.tagline_index <= len(self.tagline_text):
            self.tagline_label.setText(self.tagline_text[:self.tagline_index])
            self.tagline_index += 1
        else:
            self.tagline_timer.stop()
            QTimer.singleShot(300, self._start_loading)

    def _start_loading(self):
        self.loading_steps = [
            ("INITIALIZING...",       0),
            ("LOADING MEDIAPIPE...",  80),
            ("LOADING MODEL...",      160),
            ("CALIBRATING CAMERA...", 230),
            ("READY",                 300),
        ]
        self.loading_index = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading)
        self.loading_timer.start(600)

    def _update_loading(self):
        if self.loading_index < len(self.loading_steps):
            text, width = self.loading_steps[self.loading_index]
            self.status_label.setText(text)
            self.loading_bar.setFixedWidth(width)
            self.loading_index += 1
        else:
            self.loading_timer.stop()
            QTimer.singleShot(600, self._fade_out)

    def _fade_out(self):
        self.fade_opacity = 1.0
        self.fade_timer   = QTimer()
        self.fade_timer.timeout.connect(self._do_fade)
        self.fade_timer.start(30)

    def _do_fade(self):
        self.fade_opacity -= 0.05
        if self.fade_opacity <= 0:
            self.fade_opacity = 0
            self.fade_timer.stop()
            self.finished.emit()
        else:
            self.setWindowOpacity(self.fade_opacity)