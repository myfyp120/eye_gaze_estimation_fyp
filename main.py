import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.screens.splash_screen import SplashScreen
from ui.main_window import MainWindow

def main():
    # Must be set before QApplication is created
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Show splash first
    splash = SplashScreen()
    splash.setWindowTitle("Through the Iris")
    splash.setMinimumSize(1000, 650)

    main_window = MainWindow()

    def on_splash_done():
        splash.close()
        main_window.show()

    splash.finished.connect(on_splash_done)
    splash.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    
    
    # pip install -r requirements.txt   (Use this to install all libraries needed)
