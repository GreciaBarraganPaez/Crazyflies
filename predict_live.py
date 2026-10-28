"""Preview trained SwarmGesture predictions with webcam. DOES NOT control drones.

Usage:
    python predict_live.py

Q or Escape: quit.
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
import time

import cv2
import joblib
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from gesture_features import FEATURE_COLUMNS, normalize_landmarks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("models/gesture_svm.joblib"))
    parser.add_argument("--landmarker", type=Path, default=Path("hand_landmarker.task"))
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=0.65)
    args = parser.parse_args()

    if not args.model.exists():
        raise SystemExit(f"Missing {args.model}. Run: python train_model.py")
    if not args.landmarker.exists():
        raise SystemExit(f"Missing {args.landmarker}. Download the MediaPipe .task model first.")
    if not 0 <= args.threshold <= 1:
        raise SystemExit("Threshold must be between 0 and 1")

    artifact = joblib.load(args.model)  # Load only your own trusted model files.
    if artifact["feature_columns"] != FEATURE_COLUMNS:
        raise SystemExit("Model expects a different feature order. Check gesture_features.py.")
    model = artifact["model"]

    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(args.landmarker)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    cam = cv2.VideoCapture(args.camera)
    if not cam.isOpened():
        raise SystemExit(f"Cannot open camera {args.camera}")
    recent = deque(maxlen=5)
    start = time.monotonic()
    prev_ms = -1
    try:
        with vision.HandLandmarker.create_from_options(options) as detector:
            while True:
                ok, frame = cam.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ms = max(int((time.monotonic() - start) * 1000), prev_ms + 1)
                prev_ms = ms
                result = detector.detect_for_video(image, ms)
                label = "no hand"
                score = 0.0
                if result.hand_landmarks:
                    hand = result.hand_landmarks[0]
                    h, w = frame.shape[:2]
                    for lm in hand:
                        cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 3, (0, 255, 0), -1)
                    try:
                        features = normalize_landmarks(hand).reshape(1, -1)
                        probabilities = model.predict_proba(features)[0]
                        ix = int(probabilities.argmax())
                        score = float(probabilities[ix])
                        label = str(model.classes_[ix]) if score >= args.threshold else "uncertain"
                    except ValueError:
                        label = "invalid hand"
                recent.append(label)
                stable = label if len(recent) == recent.maxlen and all(x == label for x in recent) else "waiting"
                cv2.putText(frame, f"Gesture: {label} | score: {score:.2f}",
                            (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 0), 2)
                cv2.putText(frame, f"Stable (5 frames): {stable}",
                            (12, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 0), 2)
                cv2.putText(frame, "Demo only - no drone commands | Q: quit",
                            (12, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                cv2.imshow("SwarmGesture - live predictions", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
