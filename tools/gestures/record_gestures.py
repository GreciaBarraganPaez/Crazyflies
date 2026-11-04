"""Capture labeled MediaPipe landmarks from a live webcam.

Examples (from repository root):
    python tools/gestures/record_gestures.py --label palm --person p01
    python tools/gestures/record_gestures.py --label peace --person p02 --session morning

R: toggle recording (one sample every --interval seconds)
Q/Esc: quit

No video or photographs are saved: only normalized 63-dimensional vectors
plus a few metadata columns. One hand is used per frame.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

import sys
PROJECT_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT_ROOT))
from app.gesture_features import FEATURE_COLUMNS, normalize_landmarks

LABELS = ("palm", "fist", "one", "peace", "three", "ok", "unknown")
COLUMNS = ["label", "person_id", "session_id", "handedness", "captured_utc", *FEATURE_COLUMNS]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, choices=LABELS)
    parser.add_argument("--person", required=True, help="Anonymous participant ID, e.g. p01")
    parser.add_argument("--session", default="s01", help="Session ID for grouping related frames")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--interval", type=float, default=0.4, help="Seconds between saved frames")
    parser.add_argument("--model", default=str(PROJECT_ROOT/"models/hand_landmarker.task"), help="MediaPipe .task model path")
    parser.add_argument("--output", default=None, help="Optional CSV path; otherwise data/landmarks/<person>/<label>.csv")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if not args.person.strip() or not args.session.strip():
        parser.error("--person and --session cannot be empty")
    return args


def append_sample(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def main():
    args = arguments()
    model = Path(args.model)
    if not model.is_file():
        raise SystemExit(
            f"Missing {model}. Download hand_landmarker.task using the command in README.md."
        )
    outfile = (
        Path(args.output)
        if args.output
        else PROJECT_ROOT / "data" / "landmarks" / args.person / f"{args.label}.csv"
    )

    opts = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    cam = cv2.VideoCapture(args.camera)
    if not cam.isOpened():
        raise SystemExit(f"Cannot open camera {args.camera}")

    recording = False
    saved = 0
    last_capture = -float("inf")
    t0 = time.monotonic()
    last_timestamp_ms = -1

    print(f"Label: {args.label} | participant: {args.person} | file: {outfile}")
    print("R = start/pause, Q/Esc = quit. Move/rotate hand slightly to diversify samples.")
    try:
        with vision.HandLandmarker.create_from_options(opts) as detector:
            while True:
                ok, image_bgr = cam.read()
                if not ok:
                    print("Camera frame unavailable")
                    break

                image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
                now = time.monotonic()
                timestamp_ms = max(int((now - t0) * 1000), last_timestamp_ms + 1)
                last_timestamp_ms = timestamp_ms
                result = detector.detect_for_video(mp_image, timestamp_ms)
                hands = result.hand_landmarks

                if hands:
                    h, w = image_bgr.shape[:2]
                    for lm in hands[0]:
                        cv2.circle(image_bgr, (int(lm.x * w), int(lm.y * h)), 3, (0, 255, 0), -1)
                    if recording and now - last_capture >= args.interval:
                        try:
                            features = normalize_landmarks(hands[0])
                        except ValueError:
                            pass
                        else:
                            handedness = "unknown"
                            if result.handedness and result.handedness[0]:
                                handedness = result.handedness[0][0].category_name
                            row = {
                                "label": args.label,
                                "person_id": args.person,
                                "session_id": args.session,
                                "handedness": handedness,
                                "captured_utc": datetime.now(timezone.utc).isoformat(),
                                **dict(zip(FEATURE_COLUMNS, map(float, features))),
                            }
                            append_sample(outfile, row)
                            saved += 1
                            last_capture = now

                state = "RECORDING" if recording else "PAUSED"
                cv2.putText(image_bgr, f"{args.label} | {state} | saved: {saved}",
                            (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
                cv2.putText(image_bgr, "R: record/pause | Q/Esc: exit",
                            (10, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.imshow("SwarmGesture â€” record landmarks", image_bgr)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q"), ord("Q")):
                    break
                if key in (ord("r"), ord("R")):
                    recording = not recording
                    last_capture = -float("inf")
    finally:
        cam.release()
        cv2.destroyAllWindows()
        print(f"Saved {saved} new samples to {outfile}")


if __name__ == "__main__":
    main()
