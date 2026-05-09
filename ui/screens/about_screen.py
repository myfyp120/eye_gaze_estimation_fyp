from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
import qtawesome as qta

from utils.colors import (BG, SURFACE, PANEL, ACCENT, HIGHLIGHT, TEAL, TEXT_PRIMARY, TEXT_SEC)


# ── Avatar Widget (custom painted — no Qt stylesheet issues) ──
class AvatarWidget(QWidget):
    def __init__(self, letter, color, size=56):
        super().__init__()
        self._letter = letter
        self._color  = color
        self._size   = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background circle
        bg_color = QColor(self._color)
        bg_color.setAlpha(50)
        painter.setPen(QColor(self._color))
        painter.setBrush(bg_color)
        painter.drawEllipse(2, 2, self._size - 4, self._size - 4)

        # Letter
        painter.setPen(QColor(self._color))
        font = painter.font()
        font.setPointSize(int(self._size * 0.35))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, self._size, self._size, Qt.AlignmentFlag.AlignCenter, self._letter)
        painter.end()


# ── Person Card ───────────────────────────────────────────
class PersonCard(QWidget):
    def __init__(self, name, role, color):
        super().__init__()
        self.setMinimumWidth(200)
        self.setStyleSheet(f"""
            PersonCard {{
                background-color: {PANEL};
                border-radius: 12px;
                border: 1px solid {color}44;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar = AvatarWidget(name[0].upper(), color, size=56)

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 15px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        role_lbl = QLabel(role)
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 11px;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        color_bar = QWidget()
        color_bar.setFixedSize(32, 3)
        color_bar.setStyleSheet(f"""
            background-color: {color};
            border-radius: 2px;
            border: none;
        """)

        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_lbl)
        layout.addWidget(role_lbl)
        layout.addWidget(color_bar, alignment=Qt.AlignmentFlag.AlignCenter)


# ── Tech Badge ────────────────────────────────────────────
class TechBadge(QWidget):
    def __init__(self, icon_name, label, color):
        super().__init__()
        self.setStyleSheet(f"""
            TechBadge {{
                background-color: {PANEL};
                border-radius: 8px;
                border: 1px solid {color}44;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setPixmap(
            qta.icon(icon_name, color=color).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        text_lbl = QLabel(label)
        text_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)


# ── Section Label (centered) ──────────────────────────────
def section_label(text, icon_name, icon_color=None):
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.setSpacing(12)

    # Left divider
    left_div = QWidget()
    left_div.setFixedHeight(1)
    left_div.setStyleSheet(f"background-color: {ACCENT}; border: none;")

    # Icon + text center
    center = QHBoxLayout()
    center.setSpacing(8)

    icon_lbl = QLabel()
    icon_lbl.setPixmap(
        qta.icon(icon_name, color=icon_color or TEXT_SEC)
        .pixmap(QSize(12, 12))
    )
    icon_lbl.setStyleSheet("background: transparent;")

    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {TEXT_SEC};
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 2px;
        background: transparent;
    """)

    center.addWidget(icon_lbl)
    center.addWidget(lbl)

    # Right divider
    right_div = QWidget()
    right_div.setFixedHeight(1)
    right_div.setStyleSheet(f"background-color: {ACCENT}; border: none;")

    layout.addWidget(left_div, 1)
    layout.addLayout(center)
    layout.addWidget(right_div, 1)

    return container


# ── About Screen ──────────────────────────────────────────
class AboutScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()

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

        page_name = QLabel("ABOUT")
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
        header_layout.addWidget(page_name)
        outer.addWidget(header)

        # ── SCROLL ────────────────────────────────────
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
        cl = QVBoxLayout(content)
        cl.setContentsMargins(48, 36, 48, 36)
        cl.setSpacing(28)

        # ── HERO ──────────────────────────────────────
        hero = QWidget()
        hero.setStyleSheet(f"""
            background-color: {SURFACE};
            border-radius: 16px;
            border: 1px solid {ACCENT};
        """)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(48, 40, 48, 40)
        hero_layout.setSpacing(0)

        # Top row — icon + tag line
        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        top_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        eye_icon = QLabel()
        eye_icon.setPixmap(
            qta.icon("fa5s.eye", color=HIGHLIGHT).pixmap(QSize(36, 36))
        )
        eye_icon.setStyleSheet("background: transparent; border: none;")

        tag_col = QVBoxLayout()
        tag_col.setSpacing(3)
        tag_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        tag_lbl = QLabel("GAZE-BASED INTERACTION SYSTEM")
        tag_lbl.setStyleSheet(f"""
            color: {HIGHLIGHT};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)

        badge_lbl = QLabel("v1.0.0  ·  Final Year Project  ·  2026")
        badge_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 10px;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        tag_col.addWidget(tag_lbl)
        tag_col.addWidget(badge_lbl)

        top_row.addWidget(eye_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row.addLayout(tag_col)
        top_row.addStretch()

        # Title
        title_lbl = QLabel("Through the Iris")
        title_lbl.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        # Teal underline accent
        underline = QWidget()
        underline.setFixedSize(60, 3)
        underline.setStyleSheet(f"""
            background-color: {TEAL};
            border-radius: 2px;
            border: none;
        """)

        # Divider
        hdiv = QWidget()
        hdiv.setFixedHeight(1)
        hdiv.setStyleSheet(f"background-color: {ACCENT}88; border: none;")

        # Description row — two columns
        desc_row = QHBoxLayout()
        desc_row.setSpacing(48)
        desc_row.setContentsMargins(0, 20, 0, 0)

        desc1 = QLabel(
            "A real-time gaze estimation system enabling "
            "hands-free computer interaction through "
            "eye movements alone."
        )
        desc1.setWordWrap(True)
        desc1.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 14px;
            background: transparent;
            border: none;
        """)

        desc2 = QLabel(
            "Our project aims to provide hands-free, accessible "
            "interaction, especially for users with limited mobility, "
            "and enable intelligent screen control using gaze alone."
        )
        desc2.setWordWrap(True)
        desc2.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 13px;
            background: transparent;
            border: none;
        """)

        desc_row.addWidget(desc1, 1)
        desc_row.addWidget(desc2, 1)

        hero_layout.addLayout(top_row)
        hero_layout.addSpacing(16)
        hero_layout.addWidget(title_lbl)
        hero_layout.addSpacing(8)
        hero_layout.addWidget(underline)
        hero_layout.addSpacing(12)
        hero_layout.addWidget(hdiv)
        hero_layout.addLayout(desc_row)

        cl.addWidget(hero)

        # ── UNIVERSITY ────────────────────────────────
        uni = QWidget()
        uni.setStyleSheet(f"""
            background-color: {PANEL};
            border-radius: 10px;
            border: 1px solid {TEAL}33;
        """)
        uni_layout = QHBoxLayout(uni)
        uni_layout.setContentsMargins(24, 16, 24, 16)
        uni_layout.setSpacing(16)

        uni_icon = QLabel()
        uni_icon.setPixmap(
            qta.icon("fa5s.university", color=TEAL).pixmap(QSize(26, 26))
        )
        uni_icon.setStyleSheet("background: transparent; border: none;")

        uni_text = QVBoxLayout()
        uni_text.setSpacing(3)

        uni_name = QLabel("Government College University Lahore")
        uni_name.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        uni_dept = QLabel("Bachelor of Computer Science  ·  Final Year Project 2026")
        uni_dept.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 12px;
            background: transparent;
            border: none;
        """)

        uni_text.addWidget(uni_name)
        uni_text.addWidget(uni_dept)
        uni_layout.addWidget(uni_icon)
        uni_layout.addLayout(uni_text)
        uni_layout.addStretch()
        cl.addWidget(uni)

        # ── TEAM ──────────────────────────────────────
        cl.addWidget(section_label("TEAM", "fa5s.users"))

        team_row = QHBoxLayout()
        team_row.setSpacing(16)
        team_row.addWidget(PersonCard("Yumna Hassan", "Developer / Researcher", TEAL))
        team_row.addWidget(PersonCard("Aqsa Munir",   "Developer / Researcher", HIGHLIGHT))
        cl.addLayout(team_row)

        # ── TECH STACK ────────────────────────────────
        cl.addWidget(section_label("TECH STACK", "fa5s.layer-group"))

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(TechBadge("fa5s.brain",     "ResNet-50",     "#e94560"))
        row1.addWidget(TechBadge("fa5s.eye",        "ETH-XGaze",    "#00d4aa"))
        row1.addWidget(TechBadge("fa5s.dot-circle", "MPIIFaceGaze", "#f39c12"))
        row1.addStretch()

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(TechBadge("fa5s.desktop",   "PyQt6",         "#3498db"))
        row2.addWidget(TechBadge("fa5s.code",      "VS Code",       "#9b59b6"))
        row2.addWidget(TechBadge("fa5s.cloud",     "Google Colab",  "#4fc3f7"))
        row2.addStretch()

        cl.addLayout(row1)
        cl.addLayout(row2)

        # ── REPOSITORY ────────────────────────────────
        cl.addWidget(section_label("REPOSITORY", "fa5s.code-branch"))

        gh = QWidget()
        gh.setStyleSheet(f"""
            background-color: {PANEL};
            border-radius: 10px;
            border: 1px solid {ACCENT}55;
        """)
        gh_layout = QHBoxLayout(gh)
        gh_layout.setContentsMargins(20, 14, 20, 14)
        gh_layout.setSpacing(12)

        gh_icon = QLabel()
        gh_icon.setPixmap(
            qta.icon("fa5b.github", color=TEXT_PRIMARY).pixmap(QSize(22, 22))
        )
        gh_icon.setStyleSheet("background: transparent; border: none;")

        gh_link = QLabel("github.com/yumna-hassan/through-the-iris")
        gh_link.setStyleSheet(f"""
            color: {TEAL};
            font-size: 13px;
            background: transparent;
            border: none;
        """)

        gh_layout.addWidget(gh_icon)
        gh_layout.addWidget(gh_link)
        gh_layout.addStretch()
        cl.addWidget(gh)
        cl.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)