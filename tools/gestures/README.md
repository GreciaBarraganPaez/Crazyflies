# Gesture development tools

These utilities support dataset collection, training and debugging. The live
input app is in `app/`; normal startup does not run these tools.

From the project root:

```powershell
python tools/gestures/hand_tracker.py
python tools/gestures/predict_live.py --model models/gesture_svm_mirrored.joblib
python tools/gestures/record_gestures.py --label peace --person p02 --session s01
python tools/gestures/train_model.py --help
```

The tracker shows landmarks, the prediction preview shows classifier labels,
and the recorder writes landmark CSV files. Training writes classifier and
evaluation artifacts; use it deliberately when changing the dataset. This
cleanup did not run training or change any collected samples.

All tools locate the MediaPipe asset at `models/hand_landmarker.task`.
Recorder/trainer defaults resolve to the project's data/model/report folders.
