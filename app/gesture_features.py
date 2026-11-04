"""Feature extraction shared by gesture recording and future prediction.

Input: MediaPipe's 21 image-space landmarks (x, y, z).
Output: 63 wrist-relative, scale-normalized coordinates.

Do not change this function after collecting data without reprocessing
all training data: the live classifier must use exactly the same transform.
"""

from __future__ import annotations

import numpy as np

N_LANDMARKS = 21
N_FEATURES = N_LANDMARKS * 3
FEATURE_COLUMNS = [f"{axis}{i}" for i in range(N_LANDMARKS) for axis in ("x", "y", "z")]


def normalize_landmarks(landmarks) -> np.ndarray:
    """Normalize one hand, returning 63 float32 features.

    Wrist (landmark 0) becomes the origin. Distance in the image plane
    from wrist (0) to middle-finger MCP (9) becomes 1. This removes
    absolute position and much of scale variation, but not 3D rotation.

    Raises ValueError for invalid, missing, or degenerate hands.
    """
    points = np.asarray(
        [[float(point.x), float(point.y), float(point.z)] for point in landmarks],
        dtype=np.float32,
    )
    if points.shape != (N_LANDMARKS, 3):
        raise ValueError(f"Expected 21 3D landmarks, got {points.shape}")
    if not np.all(np.isfinite(points)):
        raise ValueError("Landmark coordinates are not finite")

    points -= points[0].copy()
    scale = float(np.linalg.norm(points[9, :2]))
    if scale < 1e-6:
        raise ValueError("Hand is too small or landmarks are invalid")

    return (points / scale).ravel().astype(np.float32)
