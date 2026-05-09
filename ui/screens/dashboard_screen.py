from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QTimer, QRect, QPointF
from PyQt6.QtGui import (QPainter, QColor, QPen, QLinearGradient, QRadialGradient, QPolygonF)
import qtawesome as qta

from utils.colors import (BG, SURFACE, PANEL, ACCENT, HIGHLIGHT, TEAL, TEXT_PRIMARY, TEXT_SEC)


# ── Stat Card ─────────────────────────────────────────────
class StatCard(QWidget):
    def __init__(self, title, value, icon_name, color):
        super().__init__()
        self._color = color
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding)
        self._setup(title, value, icon_name, color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PANEL))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        border = QColor(self._color)
        border.setAlpha(50)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 10, 10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._color))
        painter.drawRoundedRect(0, 0, 4, self.height(), 3, 3)
        painter.end()

    def _setup(self, title, value, icon_name, color):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icon_name, color=color).pixmap(QSize(13, 13))
        )
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 22px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        layout.addLayout(top)
        layout.addWidget(self.value_lbl)
        layout.addStretch()

    def set_value(self, value):
        self.value_lbl.setText(str(value))


# ── Gaze Heatmap Widget ───────────────────────────────────
class HeatmapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.points = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding)

    def add_point(self, x_ratio, y_ratio):
        self.points.append((x_ratio, y_ratio))
        if len(self.points) > 2000:
            self.points.pop(0)
        self.update()

    def clear(self):
        self.points = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PANEL))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        if not self.points:
            painter.setPen(QColor(TEXT_SEC))
            f = painter.font()
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(
                QRect(0, 0, self.width(), self.height()),
                Qt.AlignmentFlag.AlignCenter,
                "Start camera to generate heatmap"
            )
            painter.end()
            return

        # Scale radius relative to widget size
        radius = max(20, self.width() // 25)
        for x_r, y_r in self.points:
            x = int(x_r * self.width())
            y = int(y_r * self.height())
            grad = QRadialGradient(x, y, radius)
            c_inner = QColor(HIGHLIGHT)
            c_inner.setAlpha(18)
            c_outer = QColor(HIGHLIGHT)
            c_outer.setAlpha(0)
            grad.setColorAt(0, c_inner)
            grad.setColorAt(1, c_outer)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawEllipse(x - radius, y - radius,
                                radius * 2, radius * 2)

        border = QColor(ACCENT)
        border.setAlpha(120)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 10, 10)
        painter.end()


# ── Gaze Zone Map ─────────────────────────────────────────
class ZoneMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.zone_counts = [0] * 9
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding)
        self.zone_names = [
            "Top Left",   "Top Center",   "Top Right",
            "Mid Left",   "Center",       "Mid Right",
            "Bot Left",   "Bot Center",   "Bot Right",
        ]

    def add_point(self, x_ratio, y_ratio):
        col = min(int(x_ratio * 3), 2)
        row = min(int(y_ratio * 3), 2)
        self.zone_counts[row * 3 + col] += 1
        self.update()

    def clear(self):
        self.zone_counts = [0] * 9
        self.update()

    def dominant_zone(self):
        if max(self.zone_counts) == 0:
            return "N/A"
        return self.zone_names[self.zone_counts.index(max(self.zone_counts))]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PANEL))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        total     = sum(self.zone_counts) or 1
        max_count = max(self.zone_counts) or 1
        pad       = 12
        gap       = 5
        grid_w    = self.width()  - pad * 2
        grid_h    = self.height() - pad * 2
        cell_w    = grid_w // 3
        cell_h    = grid_h // 3

        # Scale font relative to cell size
        font_size = max(8, cell_h // 4)

        for i, count in enumerate(self.zone_counts):
            row = i // 3
            col = i  % 3
            x   = pad + col * cell_w
            y   = pad + row * cell_h
            intensity  = count / max_count
            cell_color = QColor(TEAL)
            cell_color.setAlpha(int(12 + intensity * 140))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(cell_color)
            painter.drawRoundedRect(x + gap, y + gap,
                                    cell_w - gap*2, cell_h - gap*2, 6, 6)
            pct        = int(count / total * 100)
            text_color = (QColor(TEXT_PRIMARY) if intensity > 0.5
                        else QColor(TEXT_SEC))
            painter.setPen(text_color)
            f = painter.font()
            f.setPointSize(font_size)
            f.setBold(intensity > 0.3)
            painter.setFont(f)
            painter.drawText(
                QRect(x + gap, y + gap, cell_w - gap*2, cell_h - gap*2),
                Qt.AlignmentFlag.AlignCenter,
                f"{pct}%"
            )

        border = QColor(ACCENT)
        border.setAlpha(120)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 10, 10)
        painter.end()


# ── Blink Rate Graph ──────────────────────────────────────
class BlinkGraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.blink_history = [0] * 60
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding)

    def update_history(self, history):
        self.blink_history = history[-60:]
        while len(self.blink_history) < 60:
            self.blink_history.insert(0, 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PANEL))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        pad_l   = 40
        pad_r   = 16
        pad_t   = 16
        pad_b   = 28
        graph_w = self.width()  - pad_l - pad_r
        graph_h = self.height() - pad_t - pad_b
        max_val = max(self.blink_history) if max(self.blink_history) > 0 else 1

        # Grid lines
        grid_color = QColor(ACCENT)
        grid_color.setAlpha(60)
        painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DashLine))
        for i in range(3):
            y = pad_t + int(graph_h * i / 2)
            painter.drawLine(pad_l, y, pad_l + graph_w, y)

        # Y axis labels
        painter.setPen(QColor(TEXT_SEC))
        f = painter.font()
        f.setPointSize(8)
        painter.setFont(f)
        for i in range(3):
            y   = pad_t + int(graph_h * i / 2)
            val = max_val - int(max_val * i / 2)
            painter.drawText(0, y - 6, pad_l - 4, 14,
                            Qt.AlignmentFlag.AlignRight, str(val))

        # X axis labels
        painter.drawText(pad_l, self.height() - 14,
                        60, 14, Qt.AlignmentFlag.AlignLeft, "-60s")
        painter.drawText(pad_l + graph_w - 24, self.height() - 14,
                        40, 14, Qt.AlignmentFlag.AlignRight, "now")

        n = len(self.blink_history)
        if n < 2:
            painter.end()
            return

        def pt(i):
            x = pad_l + int(i * graph_w / (n - 1))
            y = pad_t + graph_h - int(self.blink_history[i] / max_val * graph_h)
            return x, y

        fill_grad = QLinearGradient(0, pad_t, 0, pad_t + graph_h)
        c_top = QColor("#9b59b6")
        c_top.setAlpha(60)
        c_bot = QColor("#9b59b6")
        c_bot.setAlpha(0)
        fill_grad.setColorAt(0, c_top)
        fill_grad.setColorAt(1, c_bot)

        poly = QPolygonF()
        poly.append(QPointF(pad_l, pad_t + graph_h))
        for i in range(n):
            x, y = pt(i)
            poly.append(QPointF(x, y))
        poly.append(QPointF(pad_l + graph_w, pad_t + graph_h))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_grad)
        painter.drawPolygon(poly)

        painter.setPen(QPen(QColor("#9b59b6"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(1, n):
            x1, y1 = pt(i - 1)
            x2, y2 = pt(i)
            painter.drawLine(x1, y1, x2, y2)

        border = QColor(ACCENT)
        border.setAlpha(120)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 10, 10)
        painter.end()


# ── Dashboard Screen ──────────────────────────────────────
class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")

        self.blink_history   = [0] * 60
        self._blink_this_sec = 0
        self.total_blinks    = 0
        self.total_seconds   = 0
        self.fps_samples     = []

        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self._tick)

        self._build_ui()

    # ── Public API ────────────────────────────────────────
    def start_session(self):
        self.blink_history   = [0] * 60
        self._blink_this_sec = 0
        self.total_blinks    = 0
        self.total_seconds   = 0
        self.fps_samples     = []
        self.heatmap.clear()
        self.zone_map.clear()
        self._reset_cards()
        self.tick_timer.start(1000)

    def stop_session(self):
        self.tick_timer.stop()

    def update_gaze(self, x_ratio, y_ratio):
        self.heatmap.add_point(x_ratio, y_ratio)
        self.zone_map.add_point(x_ratio, y_ratio)
        self.dominant_card.set_value(self.zone_map.dominant_zone())

    def register_blink(self):
        self._blink_this_sec += 1
        self.total_blinks    += 1
        self.blinks_card.set_value(str(self.total_blinks))

    def update_fps(self, fps):
        self.fps_samples.append(fps)
        if len(self.fps_samples) > 100:
            self.fps_samples.pop(0)
        avg = sum(self.fps_samples) / len(self.fps_samples)
        self.fps_card.set_value(f"{avg:.1f}")

    def update_duration(self, mins, secs):
        self.duration_card.set_value(f"{mins:02}:{secs:02}")

    # ── Internal ──────────────────────────────────────────
    def _tick(self):
        self.blink_history.append(self._blink_this_sec)
        if len(self.blink_history) > 60:
            self.blink_history.pop(0)
        self._blink_this_sec = 0
        self.blink_graph.update_history(self.blink_history)

    def _reset_cards(self):
        self.duration_card.set_value("00:00")
        self.blinks_card.set_value("0")
        self.fps_card.set_value("--")
        self.dominant_card.set_value("N/A")

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── HEADER ────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(48)
        header.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)
        header.setStyleSheet(f"""
            background-color: {SURFACE};
            border-bottom: 1px solid {ACCENT};
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

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

        page_name = QLabel("DASHBOARD")
        page_name.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 11px;
            letter-spacing: 2px;
            background: transparent;
        """)

        hl.addWidget(app_icon)
        hl.addSpacing(8)
        hl.addWidget(app_name)
        hl.addStretch()
        hl.addWidget(page_name)
        outer.addWidget(header)

        # ── MAIN CONTENT (no scroll — fills window) ───
        content = QWidget()
        content.setStyleSheet(f"background-color: {BG};")
        content.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Expanding)
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(10)

        # ── STAT CARDS — fixed portion ─────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.duration_card = StatCard(
            "SESSION DURATION", "00:00", "fa5s.stopwatch", "#7e2d9e")
        self.blinks_card = StatCard(
            "TOTAL BLINKS", "0", "fa5s.eye", "#9b59b6")
        self.fps_card = StatCard(
            "AVG FPS", "--", "fa5s.tachometer-alt", "#3498db")
        self.dominant_card = StatCard(
            "DOMINANT ZONE", "N/A", "fa5s.crosshairs", TEAL)

        cards_row.addWidget(self.duration_card)
        cards_row.addWidget(self.blinks_card)
        cards_row.addWidget(self.fps_card)
        cards_row.addWidget(self.dominant_card)

        # Wrap cards in a fixed-height container
        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        cards_container.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed)
        cards_container.setFixedHeight(90)
        cards_container.setLayout(cards_row)
        cl.addWidget(cards_container)

        # ── HEATMAP + ZONE MAP — largest section ──
        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)

        heatmap_col = QVBoxLayout()
        heatmap_col.setSpacing(6)
        heatmap_col.addWidget(
            self._section_label("GAZE HEATMAP", "fa5s.fire", HIGHLIGHT))
        self.heatmap = HeatmapWidget()
        heatmap_col.addWidget(self.heatmap, 1)

        zone_col = QVBoxLayout()
        zone_col.setSpacing(6)
        zone_col.addWidget(
            self._section_label("GAZE ZONES", "fa5s.th", TEAL))
        self.zone_map = ZoneMapWidget()
        zone_col.addWidget(self.zone_map, 1)

        mid_row.addLayout(heatmap_col, 3)
        mid_row.addLayout(zone_col, 2)
        cl.addLayout(mid_row, 3)  # stretch factor 3 = biggest section

        # ── BLINK GRAPH — smaller section ─────────
        blink_col = QVBoxLayout()
        blink_col.setSpacing(6)
        blink_col.addWidget(self._section_label(
            "BLINK RATE  —  last 60 seconds", "fa5s.chart-line", "#9b59b6"))
        self.blink_graph = BlinkGraphWidget()
        blink_col.addWidget(self.blink_graph, 1)
        cl.addLayout(blink_col, 1)  # stretch factor 1 = smaller section

        outer.addWidget(content, 1)

    def _section_label(self, text, icon_name, color):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icon_name, color=color).pixmap(QSize(12, 12))
        )
        icon_lbl.setStyleSheet("background: transparent;")

        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {color};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)

        layout.addWidget(icon_lbl)
        layout.addWidget(lbl)
        layout.addStretch()
        return container