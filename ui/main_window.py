# ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                              QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
import numpy as np
import cv2

from utils.colors import BG
from ui.components.sidebar import Sidebar
from ui.screens.home_screen import HomeScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.about_screen import AboutScreen
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.calibration_screen import CalibrationScreen
from ui_model.accuracy_test import AccuracyTestScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Through the Iris")
        self.setMinimumSize(1000, 650)
        self._calib_cap  = None
        self._test_cap   = None
        self._test_screen = None
        self._build_ui()
        self._init_gaze()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self.navigate_to)

        self.stack = QStackedWidget()

        self.home_screen        = HomeScreen()
        self.dashboard_screen   = DashboardScreen()
        self.calibration_screen = CalibrationScreen()
        self.settings_screen    = SettingsScreen()
        self.about_screen       = AboutScreen()

        self.home_screen.on_session_start = self.dashboard_screen.start_session
        self.home_screen.on_session_stop  = self.dashboard_screen.stop_session
        self.home_screen.on_gaze_update   = self._on_gaze_update

        self.calibration_screen.calibration_done.connect(
            self._on_ui_calibration_done)

        self.settings_screen.on_save = self._apply_settings

        self.stack.addWidget(self.home_screen)        # 0
        self.stack.addWidget(self.dashboard_screen)   # 1
        self.stack.addWidget(self.calibration_screen) # 2
        self.stack.addWidget(self.settings_screen)    # 3
        self.stack.addWidget(self.about_screen)       # 4

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        self.setStyleSheet(f"background-color: {BG};")

    def _init_gaze(self):
        import threading

        screen        = self.screen().geometry()
        self.screen_w = screen.width()
        self.screen_h = screen.height()

        # Calibration screen uses the same estimator as HomeScreen
        # cap is None until user navigates to calibration
        self.calibration_screen.set_estimator(
            self.home_screen.estimator, None)

        # Warm up normalizer in background so first frame isn't slow
        def _warmup():
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            try:
                self.home_screen.estimator.predict(dummy)
                print("[Startup] ✅ Normalizer warmed up")
            except Exception:
                pass
        threading.Thread(target=_warmup, daemon=True).start()

    # ── Navigation ────────────────────────────────────────────────────

    def navigate_to(self, index):
        if index == 5:
            self.start_accuracy_test()
            return

        if index == 2:
            # Going to calibration — stop home camera, open calib cap
            self.stack.setCurrentIndex(2)
            self.sidebar.set_active(2)
            self.home_screen.stop_camera()
            QTimer.singleShot(500, self._open_calib_cap)
            return

        # Any other screen — release calib cap if open
        if self._calib_cap is not None:
            if self._calib_cap.isOpened():
                self._calib_cap.release()
            self._calib_cap = None

        self.stack.setCurrentIndex(index)

    def _open_calib_cap(self):
        self._calib_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self._calib_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._calib_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        for _ in range(10):
            self._calib_cap.read()
            
        self.calibration_screen.set_estimator(
            self.home_screen.estimator, self._calib_cap)
        print("[MainWindow] Calibration camera ready")

    # ── Calibration callbacks ─────────────────────────────────────────

    def _on_ui_calibration_done(self, result):
        
        mgr = self.calibration_screen.get_manager()
        print(f"[calib coeffs] ax={mgr._ax:.3f} bx={mgr._bx:.3f}")
        print(f"[calib coeffs] ay={mgr._ay:.3f} by={mgr._by:.3f}")
        print(f"[calib ranges] x: {mgr._raw_x_min:.3f} → {mgr._raw_x_max:.3f}")
        print(f"[calib ranges] y: {mgr._raw_y_min:.3f} → {mgr._raw_y_max:.3f}")
        # Release calib cap
        if self._calib_cap is not None:
            if self._calib_cap.isOpened():
                self._calib_cap.release()
            self._calib_cap = None

        # Wire calibration correction into estimator if successful
        if result.success:
            self.home_screen.estimator._calibrator = \
                self.calibration_screen.get_manager()
            print(f"[Calibration] ✅ Correction active — accuracy: {result.accuracy:.1f}%")
        else:
            print(f"[Calibration] ⚠️ Poor result — accuracy: {result.accuracy:.1f}%")

        self.stack.setCurrentIndex(0)
        self.sidebar.set_active(0)
        QTimer.singleShot(500, self.home_screen.start_camera)

    # ── Accuracy test ─────────────────────────────────────────────────

    def start_accuracy_test(self):
        if self._test_screen is not None and self._test_screen.isVisible():
            return
        self.home_screen.stop_camera()
        QTimer.singleShot(400, self._open_test_screen)

    def _open_test_screen(self):
        self._test_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self._test_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._test_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self._test_screen = AccuracyTestScreen(
            face_detector=self.home_screen.estimator.face_detector,
            cap=self._test_cap,
            estimator=self.home_screen.estimator,
            screen_w=self.screen_w,
            screen_h=self.screen_h)

        self._test_screen.test_done.connect(self._on_test_done)

    def _on_test_done(self, results):
        try:
            self._test_screen.test_done.disconnect()
        except Exception:
            pass

        if self._test_cap is not None:
            if self._test_cap.isOpened():
                self._test_cap.release()
            self._test_cap = None

        self._test_screen = None

        if results:
            mae = float(np.mean([r[4] for r in results]))
            self.home_screen.model_card._text_lbl.setText(
                f"Last test: {mae:.1f}° MAE")

        QTimer.singleShot(400, self.home_screen.start_camera)

    # ── Gaze + settings callbacks ─────────────────────────────────────

    def _on_gaze_update(self, gaze_x, gaze_y, fps):
        self.dashboard_screen.update_gaze(gaze_x, gaze_y)
        self.dashboard_screen.update_fps(fps)
        dur = self.home_screen.duration_card.value_lbl.text()
        if ":" in dur:
            parts = dur.split(":")
            try:
                self.dashboard_screen.update_duration(
                    int(parts[0]), int(parts[1]))
            except ValueError:
                pass

    def _apply_settings(self):
        s = self.settings_screen.get_trail_settings()
        self.home_screen.apply_trail_settings(
            trail_visible=s["trail_visible"],
            trail_length=s["trail_length"])
        f = self.settings_screen.get_fps_settings()
        self.home_screen.apply_fps_settings(
            fps_enabled=f["fps_enabled"],
            fps_cap=f["fps_cap"])

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.home_screen.stop_camera()
        self.dashboard_screen.stop_session()
        if self._calib_cap is not None and self._calib_cap.isOpened():
            self._calib_cap.release()
        if self._test_cap is not None and self._test_cap.isOpened():
            self._test_cap.release()
        event.accept()