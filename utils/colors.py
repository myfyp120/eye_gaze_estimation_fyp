BG           = "#0d0d1a"
SURFACE      = "#1a1a2e"
PANEL        = "#16213e"
ACCENT       = "#0f3460"
HIGHLIGHT    = "#e94560"
TEAL         = "#00d4aa"
TEXT_PRIMARY = "#ffffff"
TEXT_SEC     = "#8892a4"
TEXT_DIM     = "#4a5568"

WINDOW_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {BG};
        color: {TEXT_PRIMARY};
        font-family: 'Segoe UI', sans-serif;
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
"""

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: {TEXT_PRIMARY};
        border-radius: 6px;
        font-size: 13px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background-color: #1a5276;
    }}
    QPushButton:disabled {{
        background-color: {SURFACE};
        color: {TEXT_DIM};
    }}
"""

CARD_STYLE = f"""
    QLabel {{
        background-color: {PANEL};
        color: #cccccc;
        font-size: 13px;
        padding: 10px;
        border-radius: 6px;
    }}
"""

SIDEBAR_STYLE = f"""
    QWidget {{
        background-color: {SURFACE};
        border-right: 1px solid {ACCENT};
    }}
"""