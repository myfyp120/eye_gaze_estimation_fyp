# ui_model/face_detector.py
# Uses OpenCV DNN SSD ResNet10 — no mediapipe needed
# Works on ALL Python versions including 3.14
# ─────────────────────────────────────────────────────────────
import cv2
import numpy as np
import os
import urllib.request


# Paths to model files — relative to this file's location
_HERE        = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR  = os.path.join(os.path.dirname(_HERE), 'models')
_PROTO_PATH  = os.path.join(_MODELS_DIR, 'deploy.prototxt')
_MODEL_PATH  = os.path.join(_MODELS_DIR, 'face_detector.caffemodel')

# Download URLs
_PROTO_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/master/"
    "samples/dnn/face_detector/deploy.prototxt")
_MODEL_URL = (
    "https://github.com/opencv/opencv_3rdparty/raw/"
    "dnn_samples_face_detector_20170830/"
    "res10_300x300_ssd_iter_140000.caffemodel")


def _download_models():
    """Auto-download model files if not present."""
    os.makedirs(_MODELS_DIR, exist_ok=True)

    if not os.path.exists(_PROTO_PATH):
        print(f"[FaceDetector] Downloading deploy.prototxt...")
        urllib.request.urlretrieve(_PROTO_URL, _PROTO_PATH)
        print(f"[FaceDetector] ✅ Saved: {_PROTO_PATH}")

    if not os.path.exists(_MODEL_PATH):
        print(f"[FaceDetector] Downloading face_detector.caffemodel "
              f"(~10MB)...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print(f"[FaceDetector] ✅ Saved: {_MODEL_PATH}")


class FaceDetector:
    """
    OpenCV DNN face detector using SSD with ResNet10 backbone.

    Why OpenCV DNN instead of MediaPipe:
    - MediaPipe solutions API removed in versions compatible with Python 3.14
    - OpenCV DNN is built into opencv-python (already installed)
    - Works on all Python versions
    - ~30fps on CPU, accurate in varied lighting

    Model: res10_300x300_ssd_iter_140000.caffemodel
    Input: resizes frame to 300x300 internally, returns detections
    Output: bounding boxes with confidence scores
    """

    def __init__(self, min_confidence=0.7):
        self.min_confidence = min_confidence

        # Auto-download if needed
        _download_models()

        if not os.path.exists(_PROTO_PATH):
            raise FileNotFoundError(
                f"deploy.prototxt not found at {_PROTO_PATH}\n"
                f"Download from:\n{_PROTO_URL}")
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"face_detector.caffemodel not found at {_MODEL_PATH}\n"
                f"Download from:\n{_MODEL_URL}")

        self.net = cv2.dnn.readNetFromCaffe(_PROTO_PATH, _MODEL_PATH)
        print(f"[FaceDetector] OpenCV DNN loaded | "
              f"min_confidence={min_confidence}")

    def detect_and_crop(self, frame_bgr, target_size=224, margin=0.3):
        """
        Detects the largest face in the frame and returns a crop.

        Input:  frame_bgr — full webcam frame (H, W, 3) BGR numpy array
        Output: face crop (target_size, target_size, 3) BGR uint8
                or None if no face detected above min_confidence

        margin: padding fraction around detected face box.
                0.3 = expand each side by 30% of box size.
                Needed because ETH-XGaze crops include forehead/chin.
        """
        h, w = frame_bgr.shape[:2]

        # Preprocess: resize to 300x300, subtract mean BGR values
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame_bgr, (300, 300)),
            scalefactor=1.0,
            size=(300, 300),
            mean=(104.0, 177.0, 123.0),  # ImageNet BGR mean
            swapRB=False,
            crop=False)

        self.net.setInput(blob)
        detections = self.net.forward()
        # detections shape: (1, 1, N, 7)
        # Each row: [_, _, confidence, x1, y1, x2, y2] (normalized 0-1)

        # Find highest-confidence detection above threshold
        best_conf = 0.0
        best_box  = None

        for i in range(detections.shape[2]):
            conf = float(detections[0, 0, i, 2])
            if conf < self.min_confidence:
                continue
            if conf > best_conf:
                best_conf = conf
                best_box  = detections[0, 0, i, 3:7]

        if best_box is None:
            return None

        # Convert normalized coords → pixel coords using original size
        x1_raw = int(best_box[0] * w)
        y1_raw = int(best_box[1] * h)
        x2_raw = int(best_box[2] * w)
        y2_raw = int(best_box[3] * h)

        bw = x2_raw - x1_raw
        bh = y2_raw - y1_raw

        if bw <= 0 or bh <= 0:
            return None

        # Add margin — use original (un-shifted) coords for x2/y2
        # to avoid asymmetric crop bug
        mx = int(bw * margin)
        my = int(bh * margin)

        x1 = max(0, x1_raw - mx)
        y1 = max(0, y1_raw - my)
        x2 = min(w, x2_raw + mx)   # x2_raw not x1 — correct
        y2 = min(h, y2_raw + my)   # y2_raw not y1 — correct

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        return cv2.resize(crop, (target_size, target_size),
                          interpolation=cv2.INTER_LINEAR)

    def close(self):
        """No-op — OpenCV DNN doesn't need explicit cleanup."""
        pass