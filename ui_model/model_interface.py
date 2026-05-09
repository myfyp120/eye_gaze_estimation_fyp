# ui_model/model_interface.py
import os, sys, math, cv2
import numpy as np

ETH_REPO = r"C:/Users/aqsam/eye_gaze_estimation/repo/ETH-XGaze"
sys.path.insert(0, ETH_REPO)

import torch
import torchvision.transforms as T

try:
    from model import gaze_network
    _MODEL_AVAILABLE = True
except ImportError:
    _MODEL_AVAILABLE = False

from ui_model.face_detector  import FaceDetector
from ui_model.face_normalizer import FaceNormalizer


class GazeEstimator:

    def __init__(self):
        self.model_loaded = False
        self.model        = None
        self._last_x      = 0.5
        self._last_y      = 0.5
        self._calibrator  = None  # set by MainWindow after calibration

        try:
            self.face_detector = FaceDetector(min_confidence=0.6)
        except Exception as e:
            print(f"[GazeEstimator] FaceDetector failed: {e}")
            self.face_detector = None

        try:
            self.normalizer = FaceNormalizer()
        except Exception as e:
            print(f"[GazeEstimator] FaceNormalizer failed: {e} — accuracy degraded")
            self.normalizer = None

        self._load_model()

    def _load_model(self):
        ckpt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'checkpoint', 'exp_b_best.pth')

        if not _MODEL_AVAILABLE:
            print("[GazeEstimator] gaze_network unavailable — demo mode")
            return
        if not os.path.exists(ckpt_path) or os.path.isdir(ckpt_path):
            print("[GazeEstimator] Checkpoint not found — demo mode")
            return

        try:
            self.device = torch.device('cpu')
            ckpt        = torch.load(ckpt_path, map_location=self.device,
                                     weights_only=False)
            self.model  = gaze_network().to(self.device)
            self.model.load_state_dict(ckpt['model_state'])
            self.model.eval()

            self.transform = T.Compose([
                T.ToPILImage(),
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
            ])
            self.model_loaded = True
            print(f"[GazeEstimator] ✅ Loaded | "
                  f"MPII MAE={ckpt.get('mpii_val_mae','N/A')}")

        except Exception as e:
            print(f"[GazeEstimator] Load failed: {e} — demo mode")

    def _run_model(self, face_bgr_224):
        """Run model on a 224x224 BGR face crop. Returns (pitch, yaw) radians."""
        img    = face_bgr_224[:, :, [2, 1, 0]].copy()  # BGR → RGB
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            out = self.model(tensor).cpu().numpy()[0]
            # TEMPORARY TO DEBUG
        pitch, yaw = float(out[0]), float(out[1])
        return pitch, yaw

    def _get_face(self, frame):
        """Shared face detection + normalization. Returns 224x224 BGR or None."""
        fallback_crop = None
        if self.face_detector is not None:
            fallback_crop = self.face_detector.detect_and_crop(frame)

        if self.normalizer is not None and self.normalizer.available:
            result = self.normalizer.normalize(frame, fallback_crop=fallback_crop)
            print(f"[face] normalizer={'SUCCESS' if result is not None else 'FAILED'}")
            return result if result is not None else fallback_crop
        
        return fallback_crop

    def predict_raw(self, frame):
        """
        No EMA smoothing — use for calibration data collection.
        Calibration correction IS applied if available.
        Returns (x, y) normalized 0-1.
        """
        if not self.model_loaded:
            return self._last_x, self._last_y

        norm_face = self._get_face(frame)
        # print(f"[predict_raw] norm_face type: {type(norm_face)}, value: {norm_face if not hasattr(norm_face, 'shape') else norm_face.shape}")
        if norm_face is None:
            return self._last_x, self._last_y

        try:
            # print(f"[predict_raw] device={self.device}, model={self.model is not None}, transform={self.transform is not None}")
            pitch, yaw = self._run_model(norm_face)
            print(f"[raw] pitch={pitch:.3f} yaw={yaw:.3f}")
            
        except Exception as e:
            # print(f"[predict_raw] _run_model failed: {e}, face shape: {norm_face.shape}")
            return self._last_x, self._last_y

        # # ETH-XGaze output range: pitch [-0.5, 0.3], yaw [-0.7, 0.7] rad
        # PITCH_MIN, PITCH_MAX = -0.5,  0.3
        # YAW_MIN,   YAW_MAX   = -0.7,  0.7
        
        PITCH_MIN, PITCH_MAX = -0.52, -0.02   # from your data
        YAW_MIN,   YAW_MAX   = -0.55,  0.55   # from your data

        # x = (-yaw   - YAW_MIN) / (YAW_MAX - YAW_MIN)
        # y = (pitch - PITCH_MIN) / (PITCH_MAX - PITCH_MIN)
        
        x = (-yaw  - YAW_MIN) / (YAW_MAX - YAW_MIN)
        y = (pitch - PITCH_MAX) / (PITCH_MIN - PITCH_MAX)

        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        # Apply calibration correction if available
        if self._calibrator is not None:
            x, y = self._calibrator.correct(x, y)
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))

        return x, y

    def predict(self, frame):
        """
        Smoothed prediction for real-time display.
        Calls predict_raw then applies EMA.
        Returns (x, y) normalized 0-1.
        """
        x, y = self.predict_raw(frame)

        # predict_raw returns _last_x/_last_y when no face found
        # skip EMA update in that case to avoid drifting
        if x == self._last_x and y == self._last_y:
            return x, y

        alpha = 0.35  # lower = smoother, more lag
        x = alpha * x + (1 - alpha) * self._last_x
        y = alpha * y + (1 - alpha) * self._last_y

        self._last_x, self._last_y = x, y
        return x, y

    def predict_raw_angles(self, face_bgr_224):
        """Returns (pitch, yaw) radians directly — for accuracy testing."""
        if not self.model_loaded:
            return 0.0, 0.0
        return self._run_model(face_bgr_224)

    def set_fc_weights(self, weight, bias):
        if self.model is not None:
            self.model.gaze_fc[0].weight.data.copy_(weight)
            self.model.gaze_fc[0].bias.data.copy_(bias)
            print("[GazeEstimator] ✅ FC weights updated")

    @property
    def is_loaded(self):
        return self.model_loaded