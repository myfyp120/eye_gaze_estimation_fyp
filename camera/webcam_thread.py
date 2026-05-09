import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

class WebcamThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    camera_unavailable = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False

    def _is_blank_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        std = np.std(gray)
        return std < 10

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.flip(frame, 1)
                if self._is_blank_frame(frame):
                    self.camera_unavailable.emit()
                else:
                    self.frame_ready.emit(frame)
            else:
                self.camera_unavailable.emit()

        cap.release()

    def stop(self):
        self.running = False
        self.wait()