# ui_model/accuracy_test.py
# Shows dots one by one, predicts gaze at each, computes angular error
# Run this from main_window.py or as a standalone screen

import math
import cv2
import numpy as np
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                              QPushButton)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui  import QPainter, QColor, QBrush, QPen, QFont


class AccuracyTestScreen(QWidget):
    """
    Shows N dots, user looks at each, model predicts gaze.
    Computes angular error between predicted and true gaze direction.
    Reports per-dot error and overall MAE in degrees.

    Use this to:
      - Verify model is working before/after calibration
      - Compare pre-calibration vs post-calibration MAE
      - Demo the system accuracy in a controlled way
    """
    test_done = pyqtSignal(list)  # list of (dot_pos, pred_pitch, pred_yaw, error_deg)

    HOLD_MS   = 2000   # ms per dot — longer than calibration for accuracy
    BLINK_MS  = 300
    DOT_RADIUS = 20

    def __init__(self, face_detector, cap, estimator,
                 screen_w, screen_h,
                 dist_cm=60, screen_w_cm=34, screen_h_cm=19,
                 n_dots=9):
        super().__init__()
        self.face_detector = face_detector
        self.cap           = cap
        self.estimator     = estimator
        self.screen_w      = screen_w
        self.screen_h      = screen_h
        self.dist_cm       = dist_cm
        self.screen_w_cm   = screen_w_cm
        self.screen_h_cm   = screen_h_cm

        self.dot_x         = 0
        self.dot_y         = 0
        self.current_idx   = 0
        self.dot_visible   = True
        self.grid_positions = []
        self.results        = []   # (true_pitch, true_yaw, pred_pitch, pred_yaw, error)

        self.setWindowTitle("Gaze Accuracy Test")
        self.setStyleSheet("background-color: #0d1117;")

        self.info_label = QLabel("Look at each dot and hold still", self)
        self.info_label.setStyleSheet(
            "color:#eee; font-size:18px; font-family:Arial;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet(
            "color:#e94560; font-size:14px; font-family:Arial;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._capture_and_advance)

        self.showFullScreen()
        QTimer.singleShot(500, self._start)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self.info_label.setGeometry(w//2 - 300, 15, 600, 36)
        self.error_label.setGeometry(w//2 - 300, 55, 600, 30)

    def _start(self):
        w, h   = self.width(), self.height()
        margin = 120
        xs     = [margin, w//2, w - margin]
        ys     = [margin, h//2, h - margin]
        self.grid_positions = [(x, y) for y in ys for x in xs]
        self._show_next_dot()

    def _dot_to_gaze(self, dot_x, dot_y):
        """Convert dot pixel position to true (pitch, yaw) in radians."""
        x_cm  = (dot_x - self.screen_w/2) * (self.screen_w_cm / self.screen_w)
        y_cm  = (dot_y - self.screen_h/2) * (self.screen_h_cm / self.screen_h)
        pitch = -math.atan2(y_cm, self.dist_cm)
        yaw   =  math.atan2(x_cm, self.dist_cm)
        return pitch, yaw

    def _angular_error(self, p1, y1, p2, y2):
        """Angular error in degrees between two (pitch, yaw) pairs."""
        def to_vec(p, y):
            return np.array([
                math.cos(p) * math.sin(y),
                math.sin(p),
                math.cos(p) * math.cos(y)
            ])
        v1 = to_vec(p1, y1)
        v2 = to_vec(p2, y2)
        dot = float(np.clip(np.dot(v1, v2), -1.0, 1.0))
        return math.degrees(math.acos(dot))

    def _show_next_dot(self):
        if self.current_idx >= len(self.grid_positions):
            self._show_results()
            return
        self.dot_x, self.dot_y = self.grid_positions[self.current_idx]
        self.dot_visible = True
        n    = len(self.grid_positions)
        self.info_label.setText(
            f"Look at dot {self.current_idx+1}/{n} — hold still")
        self.update()
        self.timer.start(self.HOLD_MS)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0d1117"))

        # Draw previous dot errors as faded dots
        for i, res in enumerate(self.results):
            tx, ty = self.grid_positions[i]
            err    = res[4]
            # Color: green < 5°, yellow 5-10°, red > 10°
            if err < 5:
                col = QColor("#4caf50")
            elif err < 10:
                col = QColor("#ff9800")
            else:
                col = QColor("#e94560")
            col.setAlpha(120)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(col))
            painter.drawEllipse(tx-8, ty-8, 16, 16)

            # Error label
            painter.setPen(QColor("#ffffff"))
            f = QFont("Arial", 9)
            painter.setFont(f)
            painter.drawText(tx+10, ty+4, f"{err:.1f}°")

        # Current dot
        if self.dot_visible and self.grid_positions:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = self.DOT_RADIUS + 8
            painter.drawEllipse(self.dot_x-r, self.dot_y-r, 2*r, 2*r)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(
                self.dot_x - self.DOT_RADIUS,
                self.dot_y - self.DOT_RADIUS,
                2*self.DOT_RADIUS, 2*self.DOT_RADIUS)
            painter.setBrush(QBrush(QColor("#0d1117")))
            painter.drawEllipse(self.dot_x-5, self.dot_y-5, 10, 10)

        painter.end()



    # def _capture_and_advance(self):
    #     self.dot_visible = False
    #     self.update()

    #     pred_xs, pred_ys = [], []
    #     for _ in range(5):  # more frames for stability
    #         ret, frame = self.cap.read()
    #         if not ret:
    #             continue
    #         try:
    #             x, y = self.estimator.predict_raw(frame)
    #             pred_xs.append(x)
    #             pred_ys.append(y)
    #         except Exception:
    #             continue

    #     true_pitch, true_yaw = self._dot_to_gaze(self.dot_x, self.dot_y)

    #     if pred_xs:
    #         # Convert predicted screen coords back to approximate angles for error
    #         # pred (0-1) → angle using same ranges as predict_raw
    #         PITCH_MIN, PITCH_MAX = -0.52, -0.02
    #         YAW_MIN,   YAW_MAX   = -0.55,  0.55

    #         avg_x = float(np.mean(pred_xs))
    #         avg_y = float(np.mean(pred_ys))

    #         # Invert the mapping to get back approximate pitch/yaw
    #         pred_yaw   = -(avg_x * (YAW_MAX - YAW_MIN) + YAW_MIN)
    #         pred_pitch = -(avg_y * (PITCH_MIN - PITCH_MAX) + PITCH_MAX)

    #         error = self._angular_error(true_pitch, true_yaw, pred_pitch, pred_yaw)
    #         self.results.append((true_pitch, true_yaw, pred_pitch, pred_yaw, error))
    #         self.error_label.setText(f"Dot {self.current_idx+1} error: {error:.2f}°")
    #     else:
    #         self.error_label.setText(f"Dot {self.current_idx+1}: No face detected")

    #     self.current_idx += 1
    #     QTimer.singleShot(self.BLINK_MS, self._show_next_dot)
    
    
    def _capture_and_advance(self):
        self.dot_visible = False
        self.update()

        pred_xs, pred_ys = [], []
        for _ in range(10):
            ret, frame = self.cap.read()
            if not ret:
                continue
            try:
                x, y = self.estimator.predict_raw(frame)
                pred_xs.append(x)
                pred_ys.append(y)
            except Exception as e:
                print(f"[accuracy] predict_raw error: {e}")
                continue

        # True dot position normalized 0-1
        true_x = self.dot_x / self.screen_w
        true_y = self.dot_y / self.screen_h

        if pred_xs:
            avg_x = float(np.mean(pred_xs))
            avg_y = float(np.mean(pred_ys))

            # Screen space error → approximate degrees
            # 1.0 normalized ≈ ~30° at typical viewing distance
            err_x = (avg_x - true_x) * 30.0
            err_y = (avg_y - true_y) * 30.0
            error = math.sqrt(err_x**2 + err_y**2)

            print(f"[dot {self.current_idx}] "
                f"true=({true_x:.2f},{true_y:.2f}) "
                f"pred=({avg_x:.2f},{avg_y:.2f}) "
                f"off=({err_x:+.1f}°x, {err_y:+.1f}°y) "
                f"total={error:.1f}°")

            self.results.append((true_x, true_y, avg_x, avg_y, error))
            self.error_label.setText(
                f"Dot {self.current_idx+1}: {error:.1f}° "
                f"(x:{err_x:+.1f}° y:{err_y:+.1f}°)")
        else:
            print(f"[dot {self.current_idx}] NO FACE DETECTED")
            self.error_label.setText(f"Dot {self.current_idx+1}: No face detected")
            self.results.append((true_x, true_y, true_x, true_y, 0.0))

        self.current_idx += 1
        QTimer.singleShot(self.BLINK_MS, self._show_next_dot)


    def _show_results(self):
        self.timer.stop()
        self.dot_visible = False
        self.update()

        if not self.results:
            self.info_label.setText("No results — no face detected")
            QTimer.singleShot(3000, self._emit_and_close)
            return

        errors = [r[4] for r in self.results]
        mae = float(np.mean(errors))

        print(f"\n{'='*50}")
        print(f"ACCURACY TEST RESULTS")
        print(f"{'='*50}")
        print(f"MAE: {mae:.1f}°")
        print(f"{'='*50}")
        for i, r in enumerate(self.results):
            true_x, true_y, pred_x, pred_y, err = r
            err_x = (pred_x - true_x) * 30.0
            err_y = (pred_y - true_y) * 30.0
            print(f"  Dot {i+1}: pred=({pred_x:.2f},{pred_y:.2f}) "
                f"true=({true_x:.2f},{true_y:.2f}) "
                f"off=({err_x:+.1f}°x, {err_y:+.1f}°y) "
                f"err={err:.1f}°")
        print(f"{'='*50}\n")

        if mae < 5:
            quality = "Excellent"
        elif mae < 8:
            quality = "Good"
        elif mae < 12:
            quality = "Fair"
        else:
            quality = "Poor"

        self.info_label.setText(
            f"MAE: {mae:.1f}° — {quality} | Click anywhere to close")
        self.error_label.setText(
            f"Look at the console for per-dot breakdown")

        QTimer.singleShot(5000, self._emit_and_close)

    
    def _emit_and_close(self):
        # Disconnect signal before emitting to prevent repeat
        try:
            self.test_done.disconnect()
        except Exception:
            pass
        self.test_done.emit(self.results)
        self.close()
        

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)