# ui_model/face_normalizer.py — FINAL VERSION
# Uses OpenCV's built-in face landmark detector
# No dlib, no mediapipe, no face-alignment needed
# Works on ALL Python versions, no compilation, fast

import cv2
import numpy as np
import os
import urllib.request

_HERE       = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(os.path.dirname(_HERE), 'models')

# OpenCV face landmark model (LBF algorithm)
_LBF_MODEL_PATH = os.path.join(_MODELS_DIR, 'lbfmodel.yaml')
_LBF_MODEL_URL  = (
    "https://raw.githubusercontent.com/kurnianggoro/"
    "GSOC2017/master/data/lbfmodel.yaml")

# Generic 6-point 3D face model for PnP
_FACE_3D = np.array([
    [ 0.0,      0.0,      0.0    ],
    [ 0.0,    -330.0,   -65.0   ],
    [-225.0,   170.0,  -135.0   ],
    [ 225.0,   170.0,  -135.0   ],
    [-150.0,  -150.0,  -125.0   ],
    [ 150.0,  -150.0,  -125.0   ],
], dtype=np.float64)

# LBF gives 68 points — same as dlib
# Indices: nose(30), chin(8), l-eye(36), r-eye(45), l-mouth(48), r-mouth(54)
_LDMK_IDX = [30, 8, 36, 45, 48, 54]


def _download_lbf():
    os.makedirs(_MODELS_DIR, exist_ok=True)
    if not os.path.exists(_LBF_MODEL_PATH):
        print("[FaceNormalizer] Downloading LBF landmark model (~54MB)...")
        urllib.request.urlretrieve(_LBF_MODEL_URL, _LBF_MODEL_PATH)
        print("[FaceNormalizer] ✅ Downloaded")


class FaceNormalizer:
    """
    Face normalizer using OpenCV built-in FacemarkLBF.
    No external dependencies, fast on CPU (~10ms/frame).
    Works on all Python versions including 3.14.
    """

    NORM_FOCAL = 960
    NORM_SIZE  = (224, 224)
    NORM_CAM   = np.array([
        [960, 0,   112],
        [0,   960, 112],
        [0,   0,   1  ]
    ], dtype=np.float64)

    def __init__(self):
        _download_lbf()

        if not os.path.exists(_LBF_MODEL_PATH):
            print("[FaceNormalizer] LBF model not found — normalization disabled")
            self.available = False
            return

        try:
            # Face detector for landmark input
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades +
                'haarcascade_frontalface_alt2.xml')

            # LBF landmark detector
            self._facemark = cv2.face.createFacemarkLBF()
            self._facemark.loadModel(_LBF_MODEL_PATH)
            self.available = True
            print("[FaceNormalizer] ✅ OpenCV LBF loaded (fast, no compilation)")
        except Exception as e:
            print(f"[FaceNormalizer] Failed: {e} — normalization disabled")
            self.available = False

    def normalize(self, frame_bgr, fallback_crop=None):
        """
        Input:  full BGR webcam frame
        Output: 224x224 normalized face BGR or fallback_crop
        """
        if not self.available:
            return fallback_crop

        h, w  = frame_bgr.shape[:2]
        gray  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        
            # Use full frame for Haar detection
        faces = self._face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3,  # lowered from 5
            minSize=(60, 60)) 

# BREAKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
        # # Detect faces
        # faces = self._face_cascade.detectMultiScale(
        #     gray, scaleFactor=1.1, minNeighbors=5,
        #     minSize=(80, 80))

        if len(faces) == 0:
            return fallback_crop

        # Use largest face
        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        faces_arr = np.array([faces[0]], dtype=np.int32)  # shape (1,4)

        # Detect landmarks
        ok, landmarks = self._facemark.fit(gray, faces_arr)
        if not ok or landmarks is None or len(landmarks) == 0:
            return fallback_crop

        lmks = landmarks[0][0]  # shape (68, 2)

        pts2d = np.array([lmks[i] for i in _LDMK_IDX],
                         dtype=np.float64)

        cam  = np.array([
            [float(w), 0,         w/2.0],
            [0,         float(w), h/2.0],
            [0,         0,         1.0 ]
        ], dtype=np.float64)
        dist = np.zeros((4, 1), dtype=np.float64)

        ok, rvec, tvec = cv2.solvePnP(
            _FACE_3D, pts2d, cam, dist,
            flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return fallback_crop

        rot, _   = cv2.Rodrigues(rvec)
        distance = np.linalg.norm(tvec)
        if distance < 1e-6:
            return fallback_crop

        scale    = self.NORM_FOCAL / distance
        norm_mat = self.NORM_CAM @ np.diag([scale, scale, 1.0]) \
                   @ rot @ np.linalg.inv(cam)

        warped = cv2.warpPerspective(frame_bgr, norm_mat, self.NORM_SIZE)
        if warped is None or warped.size == 0:
            return fallback_crop

        return warped

    def close(self):
        pass