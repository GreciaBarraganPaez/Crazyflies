"""
hand_tracker.py
Live hand tracking with the MediaPipe Hand Landmarker.

What it does:
    1. Opens the webcam.
    2. Sends every frame to MediaPipe, which finds up to two hands
       and returns 21 landmarks (joints and fingertips) per hand.
    3. Draws a green dot on every landmark and shows the result.
"""

import time
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# Configuration
options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=str(PROJECT_ROOT/"models/hand_landmarker.task")),        # pretrained model file
    running_mode=vision.RunningMode.VIDEO,                                              # frames come from a video stream (enables tracking)
    num_hands=2,                                                                        # detect up to two hands
    min_hand_detection_confidence=0.5,                                                  # how sure the detector must be to report a hand
    min_tracking_confidence=0.5,                                                        # how sure the tracker must be to keep following it
)

# Camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera 0 could not be opened")
    raise SystemExit

t0 = time.monotonic()                                                                   # start time, used for the frame timestamps

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        
        # Read one frame (OpenCV delivers BGR colors)
        ok, frame_bgr = cap.read()
        if not ok:
            print("Could not read a frame from the camera")
            break

        # MediaPipe expects RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Detect hands; the timestamp (ms) must increase with every frame
        timestamp_ms = int((time.monotonic() - t0) * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        # Draw the 21 landmarks of each hand (x, y are 0..1, so scale to pixels)
        h, w = frame_bgr.shape[:2]
        for hand in result.hand_landmarks:
            for lm in hand:
                cv2.circle(frame_bgr, (int(lm.x * w), int(lm.y * h)), 3, (0, 255, 0), -1)

        cv2.imshow("hands", frame_bgr)
        if cv2.waitKey(1) & 0xFF == 27:  # Esc to quit
            break

cap.release()
cv2.destroyAllWindows()