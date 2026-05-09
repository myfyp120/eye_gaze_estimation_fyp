# ui_model/inference_thread.py
# Runs face detection + gaze inference in background
# Main thread never blocks on model inference
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import time


class InferenceThread(QThread):
    """
    Runs face detection + gaze prediction in a background thread.
    Main Qt thread stays responsive — never does inference directly.
    
    How it works:
      1. WebcamThread puts frames into this thread via update_frame()
      2. InferenceThread runs detection + inference on each frame
      3. Emits result_ready(x, y, fps) when done
      4. If a new frame arrives before inference finishes, it skips
         the old frame (always uses latest frame, no queue buildup)
    """
    result_ready = pyqtSignal(float, float, float)  # x, y, fps

    def __init__(self, estimator, parent=None):
        super().__init__(parent)
        self.estimator   = estimator
        self._frame      = None
        self._running    = False
        self._last_time  = time.time()

    def update_frame(self, frame):
        """Called from main thread — just stores latest frame."""
        self._frame = frame  # always overwrites — no queue

    def run(self):
        self._running = True
        while self._running:
            frame = self._frame
            if frame is None:
                self.msleep(10)
                continue

            self._frame = None  # clear so we don't reprocess same frame

            try:
                x, y = self.estimator.predict(frame)
                now   = time.time()
                fps   = 1.0 / max(0.001, now - self._last_time)
                self._last_time = now
                self.result_ready.emit(float(x), float(y), float(fps))
            except Exception as e:
                print(f"[InferenceThread] Error: {e}")

            self.msleep(5)  # small yield

    def stop(self):
        self._running = False
        self.wait(2000)