#!/usr/bin/env python3
"""Windows webcam + MediaPipe + mirrored SVM -> optional WSL UDP demo.

Safe default: PREVIEW ONLY. To enable UDP: pass --send, then press E in the
webcam window to enable transmission. X sends a landing request regardless
of whether transmission is enabled (only if --send was specified).
This is not certified or safe for real drone flight.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import socket
import time

import cv2
import joblib
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from app.gesture_features import FEATURE_COLUMNS, normalize_landmarks
from app.gesture_gate import StableGestureGate
from app.hand_steering import HandSteering

PROJECT_ROOT=Path(__file__).resolve().parent.parent

KNOWN = {'one', 'peace', 'three', 'ok', 'palm', 'fist'}
ACTIONS = {'one': 'takeoff', 'peace': 'front-view heart',
           'three': 'front-view sine curve', 'ok': 'front-view spiral',
           'palm': 'return to grid and land', 'fist': 'return to grid'}



def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, default=PROJECT_ROOT/'models/gesture_svm_mirrored.joblib')
    p.add_argument('--landmarker', type=Path, default=PROJECT_ROOT/'models/hand_landmarker.task')
    p.add_argument('--camera', type=int, default=0)
    p.add_argument('--threshold', type=float, default=0.8)
    p.add_argument('--hold', type=float, default=0.7, help='Required continuous recognition in seconds')
    p.add_argument('--cooldown', type=float, default=1.5)
    p.add_argument('--send', action='store_true', help='Permit UDP sending (still disabled until E is pressed)')
    p.add_argument('--host', help='Ubuntu WSL IPv4 address, required for --send')
    p.add_argument('--port', type=int, default=5055)
    p.add_argument('--snake-player', action='store_true', help='Enable four hand-position steering zones for the separate playable Snake mode')
    args = p.parse_args()
    actions={**ACTIONS,**({k:'start hand-controlled Snake' for k in ('peace','three','ok')} if args.snake_player else {})}
    if args.snake_player:actions['one']='takeoff / point to steer'
    if args.send and not args.host:
        p.error('--send requires --host with the IP from `hostname -I` inside Ubuntu')
    if not 0 < args.threshold <= 1 or args.hold < 0.2 or args.cooldown < 0:
        p.error('Invalid threshold/hold/cooldown')
    for path in (args.model, args.landmarker):
        if not path.exists():
            p.error(f'Missing file: {path}')

    artifact = joblib.load(args.model)  # Only load models trained by your own trusted code.
    if artifact['feature_columns'] != FEATURE_COLUMNS:
        p.error('Feature mismatch: model expects different landmark normalization/order.')
    model = artifact['model']
    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(args.landmarker)),
        running_mode=vision.RunningMode.VIDEO, num_hands=1,
        min_hand_detection_confidence=0.5, min_tracking_confidence=0.5,
    )
    cam = cv2.VideoCapture(args.camera)
    if not cam.isOpened():
        p.error(f'Cannot open camera {args.camera}')

    enabled = False
    gate = StableGestureGate(args.hold, args.cooldown)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start = time.monotonic()
    prev_ms = -1
    last_action = 'none'
    steering=HandSteering()
    try:
        with vision.HandLandmarker.create_from_options(options) as detector:
            while True:
                ok, frame = cam.read()
                if not ok:
                    print('Camera frame unavailable; stopping.')
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                now = time.monotonic()
                timestamp_ms = max(int((now - start) * 1000), prev_ms + 1)
                prev_ms = timestamp_ms
                result = detector.detect_for_video(mp_image, timestamp_ms)
                label, score = 'no hand', 0.0
                hand_x=hand_y=None
                if result.hand_landmarks:
                    hand = result.hand_landmarks[0]
                    hand_x=1-sum(hand[i].x for i in (0,5,9,13,17))/5
                    hand_y=sum(hand[i].y for i in (0,5,9,13,17))/5
                    height, width = frame.shape[:2]
                    for lm in hand:
                        cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 3,
                                   (0, 255, 0), -1)
                    try:
                        features = normalize_landmarks(hand).reshape(1, -1)
                        probs = model.predict_proba(features)[0]
                        idx = int(probs.argmax())
                        score = float(probs[idx])
                        label = str(model.classes_[idx]) if score >= args.threshold else 'uncertain'
                    except ValueError:
                        label = 'invalid hand'
                event = gate.accept(label, now)
                if args.snake_player:
                    turn=steering.update(hand_x,hand_y,now,pointing=label=='one' and enabled)
                    if turn and args.send and enabled:
                        udp.sendto(turn.encode('ascii'),(args.host,args.port))
                        last_action='steer '+turn
                    # Mirror only this mode's display; recognition retains the trained input.
                    frame=cv2.flip(frame,1)
                    h,w=frame.shape[:2]
                    cv2.rectangle(frame,(int(.32*w),int(.32*h)),(int(.68*w),int(.68*h)),(255,180,0),2)
                if event is not None:
                    last_action = f'{event} -> {actions[event]}'
                    if args.send and enabled:
                        udp.sendto(event.encode('ascii'), (args.host, args.port))
                        print('SENT:', last_action)
                    else:
                        print('PREVIEW:', last_action)
                status = 'SENDING ON' if args.send and enabled else 'PREVIEW ONLY'
                cv2.putText(frame, f'{status} | gesture: {label} ({score:.2f})',
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 0), 2)
                cv2.putText(frame, f'Last stable: {last_action}', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, 'E: enable/disable UDP | X: land | Q: quit',
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                if args.snake_player:
                    cv2.putText(frame,'Point one finger: move LEFT / RIGHT / UP / DOWN; center = straight',
                                (10,120),cv2.FONT_HERSHEY_SIMPLEX,.48,(255,210,80),1)
                    for text,x,y in (('UP',w//2-15,145),('DOWN',w//2-25,h-15),
                                     ('LEFT',15,h//2),('RIGHT',w-65,h//2)):
                        cv2.putText(frame,text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,210,80),2)
                cv2.imshow('SwarmGesture - simulation gestures', frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q'), 27):
                    break
                if key in (ord('e'), ord('E')):
                    enabled = (not enabled) if args.send else False
                    gate = StableGestureGate(args.hold, args.cooldown)
                    steering=HandSteering()
                    print('UDP sending', 'enabled' if enabled else 'disabled')
                if key in (ord('x'), ord('X')):
                    enabled = False
                    gate = StableGestureGate(args.hold, args.cooldown)
                    steering=HandSteering()
                    if args.send:
                        udp.sendto(b'palm', (args.host, args.port))
                        print('KEYBOARD X: sent controlled-landing request; transmission disabled')
                    else:
                        print('KEYBOARD X: preview-only, no network command sent')
    finally:
        if args.send:
            # A final best-effort landing request; UDP delivery is not guaranteed.
            udp.sendto(b'palm', (args.host, args.port))
        udp.close()
        cam.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
