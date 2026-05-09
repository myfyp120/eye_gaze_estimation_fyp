"""
CalibrationManager
──────────────────
Collects raw gaze predictions at 9 known screen positions and computes
a linear correction mapping. Ready to wire to the real model later.

Usage:
    mgr = CalibrationManager()
    mgr.start()

    # For each point i (0-8):
    mgr.begin_point(i)
    mgr.add_sample(raw_x, raw_y)   # call this each frame while user stares
    mgr.end_point()

    result = mgr.compute()          # returns CalibrationResult
    corrected_x, corrected_y = mgr.correct(raw_x, raw_y)
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math


# ── 9 calibration target positions (normalized 0-1) ──────
# Order: top-left → top-center → top-right →
#        mid-left → center → mid-right →
#        bot-left → bot-center → bot-right
CALIB_POINTS: List[Tuple[float, float]] = [
    (0.1,  0.1),   # 0  top-left
    (0.5,  0.1),   # 1  top-center
    (0.9,  0.1),   # 2  top-right
    (0.1,  0.5),   # 3  mid-left
    (0.5,  0.5),   # 4  center
    (0.9,  0.5),   # 5  mid-right
    (0.1,  0.9),   # 6  bot-left
    (0.5,  0.9),   # 7  bot-center
    (0.9,  0.9),   # 8  bot-right
]


@dataclass
class CalibrationResult:
    success:       bool
    accuracy:      float          # 0-100 %
    point_errors:  List[float]    # per-point error in normalized units
    message:       str


class CalibrationManager:
    def __init__(self):
        self._samples:  List[List[Tuple[float, float]]] = [[] for _ in range(9)]
        self._active:   int  = -1
        self._ready:    bool = False

        # Linear mapping coefficients  (scale + offset per axis)
        # corrected_x = _ax * raw_x + _bx
        # corrected_y = _ay * raw_y + _by
        self._ax = 1.0;  self._bx = 0.0
        self._ay = 1.0;  self._by = 0.0

    # ── Session control ───────────────────────────────────
    def start(self):
        """Reset everything and prepare for a new calibration."""
        self._samples  = [[] for _ in range(9)]
        self._active   = -1
        self._ready    = False
        self._ax = 1.0;  self._bx = 0.0
        self._ay = 1.0;  self._by = 0.0

    def begin_point(self, index: int):
        """Call when the dot for point `index` appears."""
        assert 0 <= index < 9
        self._active = index
        self._samples[index] = []

    def add_sample(self, raw_x: float, raw_y: float):
        """Call every frame while the user is staring at the active point."""
        if self._active < 0:
            return
        self._samples[self._active].append((raw_x, raw_y))

    def end_point(self):
        """Call when the dot for the current point is done."""
        self._active = -1

    # ── Computation ───────────────────────────────────────
    # def compute(self) -> CalibrationResult:
    #     """
    #     Compute the linear mapping from raw → screen coordinates.
    #     Returns a CalibrationResult with accuracy info.
    #     """
    #     # Average raw prediction per point
    #     means: List[Optional[Tuple[float, float]]] = []
    #     for i, samples in enumerate(self._samples):
    #         if not samples:
    #             means.append(None)
    #         else:
    #             avg_x = sum(s[0] for s in samples) / len(samples)
    #             avg_y = sum(s[1] for s in samples) / len(samples)
    #             means.append((avg_x, avg_y))

    #     valid = [(CALIB_POINTS[i], means[i])
    #             for i in range(9) if means[i] is not None]

    #     if len(valid) < 4:
    #         return CalibrationResult(
    #             success=False, accuracy=0.0,
    #             point_errors=[0.0]*9,
    #             message="Not enough calibration data."
    #         )

    #     # Fit separate 1-D linear regression for X and Y
    #     # target = a * raw + b
    #     self._ax, self._bx = self._fit_linear(
    #         [(m[0], t[0]) for t, m in valid]
    #     )
    #     self._ay, self._by = self._fit_linear(
    #         [(m[1], t[1]) for t, m in valid]
    #     )

    #     # Compute per-point error after correction
    #     point_errors = [0.0] * 9
    #     total_error  = 0.0
    #     for i, (target, mean) in enumerate(
    #             zip(CALIB_POINTS, means)):
    #         if mean is None:
    #             continue
    #         cx = self._ax * mean[0] + self._bx
    #         cy = self._ay * mean[1] + self._by
    #         err = math.hypot(cx - target[0], cy - target[1])
    #         point_errors[i] = err
    #         total_error += err

    #     avg_error = total_error / len(valid)
    #     # Map error to accuracy: 0 error → 100%, 0.1 error → 0%
    #     accuracy  = max(0.0, min(100.0, (1 - avg_error / 0.1) * 100))

    #     self._ready = True
    #     return CalibrationResult(
    #         success      = accuracy > 50,
    #         accuracy     = round(accuracy, 1),
    #         point_errors = point_errors,
    #         message      = (
    #             "Calibration successful!" if accuracy > 75
    #             else "Calibration OK — consider recalibrating for better accuracy."
    #             if accuracy > 50
    #             else "Calibration poor — please recalibrate."
    #         )
    #     )

    # def correct(self, raw_x: float, raw_y: float) -> Tuple[float, float]:
    #     """Apply calibration correction to a raw model prediction."""
    #     if not self._ready:
    #         return raw_x, raw_y
    #     cx = max(0.0, min(1.0, self._ax * raw_x + self._bx))
    #     cy = max(0.0, min(1.0, self._ay * raw_y + self._by))
    #     return cx, cy
    
    def compute(self) -> CalibrationResult:
        means = []
        for i, samples in enumerate(self._samples):
            if not samples:
                means.append(None)
            else:
                # Skip first 3 samples — eye still moving to dot
                stable = samples[3:] if len(samples) > 3 else samples
                avg_x = sum(s[0] for s in stable) / len(stable)
                avg_y = sum(s[1] for s in stable) / len(stable)
                means.append((avg_x, avg_y))

        valid = [(CALIB_POINTS[i], means[i])
                for i in range(9) if means[i] is not None]

        if len(valid) < 4:
            return CalibrationResult(
                success=False, accuracy=0.0,
                point_errors=[0.0]*9,
                message="Not enough calibration data.")

        # Auto-scale: find actual raw ranges from collected means
        raw_xs = [m[0] for _, m in valid]
        raw_ys = [m[1] for _, m in valid]
        
        # raw_x_min, raw_x_max = min(raw_xs), max(raw_xs)
        # raw_y_min, raw_y_max = min(raw_ys), max(raw_ys)
        
        pad = 0.05
        raw_x_min = min(raw_xs) - pad
        raw_x_max = max(raw_xs) + pad
        raw_y_min = min(raw_ys) - pad
        raw_y_max = max(raw_ys) + pad
        
        # Normalize raw means to 0-1 using actual observed range
        def norm_x(rx): 
            r = raw_x_max - raw_x_min
            return (rx - raw_x_min) / r if r > 0.01 else 0.5
        
        def norm_y(ry):
            r = raw_y_max - raw_y_min
            return (ry - raw_y_min) / r if r > 0.01 else 0.5

        # Store for use in correct()
        self._raw_x_min = raw_x_min
        self._raw_x_max = raw_x_max
        self._raw_y_min = raw_y_min
        self._raw_y_max = raw_y_max

        # Fit linear map from normalized raw → screen target
        self._ax, self._bx = self._fit_linear(
            [(norm_x(m[0]), t[0]) for t, m in valid])
        self._ay, self._by = self._fit_linear(
            [(norm_y(m[1]), t[1]) for t, m in valid])

        # Compute errors
        point_errors = [0.0] * 9
        total_error = 0.0
        for i, (target, mean) in enumerate(zip(CALIB_POINTS, means)):
            if mean is None:
                continue
            cx = self._ax * norm_x(mean[0]) + self._bx
            cy = self._ay * norm_y(mean[1]) + self._by
            err = math.hypot(cx - target[0], cy - target[1])
            point_errors[i] = err
            total_error += err

        avg_error = total_error / len(valid)
        # accuracy = max(0.0, min(100.0, (1 - avg_error / 0.1) * 100))
        accuracy = max(0.0, min(100.0, (1 - avg_error / 0.2) * 100))
        self._ready = True

        return CalibrationResult(
            success=accuracy > 50,
            accuracy=round(accuracy, 1),
            point_errors=point_errors,
            message=(
                "Calibration successful!" if accuracy > 60
                else "Calibration OK — consider recalibrating."
                if accuracy > 50
                else "Calibration poor — please recalibrate."))
        
        
    def correct(self, raw_x: float, raw_y: float) -> Tuple[float, float]:
        if not self._ready:
            return raw_x, raw_y
        
        rx_min = getattr(self, '_raw_x_min', 0.0)
        rx_max = getattr(self, '_raw_x_max', 1.0)
        ry_min = getattr(self, '_raw_y_min', 0.0)
        ry_max = getattr(self, '_raw_y_max', 1.0)
        
        rx = (raw_x - rx_min) / (rx_max - rx_min) if (rx_max - rx_min) > 0.01 else 0.5
        ry = (raw_y - ry_min) / (ry_max - ry_min) if (ry_max - ry_min) > 0.01 else 0.5
        
        cx = max(0.0, min(1.0, self._ax * rx + self._bx))
        cy = max(0.0, min(1.0, self._ay * ry + self._by))
        
        print(f"[correct] raw=({raw_x:.3f},{raw_y:.3f}) norm=({rx:.3f},{ry:.3f}) out=({cx:.3f},{cy:.3f})")
        
        return cx, cy   

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Helpers ───────────────────────────────────────────
    @staticmethod
    def _fit_linear(pairs: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Least-squares linear fit: target = a * raw + b."""
        n  = len(pairs)
        if n < 2:
            return 1.0, 0.0
        sx  = sum(p[0] for p in pairs)
        sy  = sum(p[1] for p in pairs)
        sxx = sum(p[0]**2 for p in pairs)
        sxy = sum(p[0] * p[1] for p in pairs)
        denom = n * sxx - sx * sx
        if abs(denom) < 1e-9:
            return 1.0, 0.0
        a = (n * sxy - sx * sy) / denom
        b = (sy - a * sx) / n
        return a, b