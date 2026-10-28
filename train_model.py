"""Train the first SwarmGesture SVM on Stage 1 landmark CSV files.

Usage:
    python train_model.py
    python train_model.py --mode session
    python train_model.py --mode person
    python train_model.py --mirror-augment

A random split with one person is ONLY a smoke test. For a meaningful
performance estimate, collect data from different people/sessions.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from gesture_features import FEATURE_COLUMNS


def load_data(directory: Path) -> pd.DataFrame:
    paths = sorted(directory.rglob("*.csv"))
    if not paths:
        raise SystemExit(f"No CSV files found under {directory}. Expected data/landmarks/p01/palm.csv etc.")
    frames = []
    needed = {"label", "person_id", "session_id", *FEATURE_COLUMNS}
    for path in paths:
        frame = pd.read_csv(path)
        missing = needed - set(frame.columns)
        if missing:
            raise SystemExit(f"{path}: missing columns: {', '.join(sorted(missing))}")
        frame = frame.dropna(subset=["label", "person_id", "session_id", *FEATURE_COLUMNS]).copy()
        if len(frame):
            frame[FEATURE_COLUMNS] = frame[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
            frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLUMNS)
            frames.append(frame)
    if not frames:
        raise SystemExit("The CSV files contain no valid samples.")
    return pd.concat(frames, ignore_index=True)


def mirror_features(X: np.ndarray) -> np.ndarray:
    """Mirror normalized hand landmarks horizontally (x -> -x).

    The CSV feature order is x0,y0,z0,...,x20,y20,z20.
    Training data only is augmented; evaluation data stays untouched.
    """
    mirrored = X.copy()
    mirrored[:, 0::3] *= -1
    return mirrored


def find_group_split(y, groups, test_size=0.25):
    """Try group splits until both partitions contain every gesture class."""
    classes = set(y)
    splitter = GroupShuffleSplit(n_splits=100, test_size=test_size, random_state=42)
    for train_idx, test_idx in splitter.split(np.zeros(len(y)), y, groups):
        if set(y[train_idx]) == classes and set(y[test_idx]) == classes:
            return train_idx, test_idx
    raise ValueError("Cannot make a group holdout containing all labels. Record every gesture in more sessions/people.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/landmarks"))
    parser.add_argument("--mode", choices=("auto", "person", "session", "random"), default="auto")
    parser.add_argument("--model", type=Path, default=Path("models/gesture_svm.joblib"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    parser.add_argument(
        "--mirror-augment", action="store_true",
        help="Add x-mirrored copies to the training samples to help with opposite-hand gestures.",
    )
    args = parser.parse_args()

    data = load_data(args.data)
    print("\nSamples per class:")
    print(data["label"].value_counts().sort_index().to_string())
    print(f"\nParticipants: {data['person_id'].nunique()}; sessions: {data[['person_id', 'session_id']].drop_duplicates().shape[0]}")

    X = data[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    y = data["label"].astype(str).to_numpy()
    counts = pd.Series(y).value_counts()
    if len(counts) < 2:
        raise SystemExit("Need at least two different gestures before training.")
    if (counts < 4).any():
        raise SystemExit("Each gesture needs at least 4 valid samples (more recommended).")

    session_groups = (data["person_id"].astype(str) + ":" + data["session_id"].astype(str)).to_numpy()
    mode = args.mode
    if mode == "auto":
        if data["person_id"].nunique() >= 2:
            mode = "person"
        elif len(set(session_groups)) >= 2:
            mode = "session"
        else:
            mode = "random"

    try:
        if mode == "person":
            train_idx, test_idx = find_group_split(y, data["person_id"].astype(str).to_numpy())
        elif mode == "session":
            train_idx, test_idx = find_group_split(y, session_groups)
        else:
            train_idx, test_idx = train_test_split(
                np.arange(len(y)), test_size=0.25, random_state=42, stratify=y
            )
    except ValueError as exc:
        raise SystemExit(f"Cannot create {mode} split: {exc}") from exc

    if mode == "random":
        warning = ("PILOT TEST ONLY: random frames from the same recording can appear in both "
                   "train and test, so accuracy may be overly optimistic.")
    elif mode == "session":
        warning = "Session-held-out test; a different person's data is still needed for final evaluation."
    else:
        warning = "Person-held-out test; expand to at least 3 independent test participants for final evaluation."
    print(f"\nEvaluation split: {mode} | training {len(train_idx)} / test {len(test_idx)}")
    print(warning)

    def classifier():
        return make_pipeline(
            StandardScaler(),
            SVC(kernel="rbf", C=3.0, gamma="scale", probability=True, random_state=42),
        )

    train_X, train_y = X[train_idx], y[train_idx]
    if args.mirror_augment:
        train_X = np.concatenate([train_X, mirror_features(train_X)], axis=0)
        train_y = np.concatenate([train_y, train_y], axis=0)
        print(f"Mirror augmentation ON: fitting {len(train_X)} samples (including mirrors).")

    evaluation_model = classifier()
    evaluation_model.fit(train_X, train_y)
    predicted = evaluation_model.predict(X[test_idx])
    labels = sorted(set(y))
    accuracy = accuracy_score(y[test_idx], predicted)
    report = classification_report(y[test_idx], predicted, labels=labels, zero_division=0)
    print(f"\nAccuracy: {accuracy:.1%}")
    print(report)

    args.reports.mkdir(parents=True, exist_ok=True)
    (args.reports / "evaluation.txt").write_text(
        f"Split: {mode}\nOriginal train: {len(train_idx)}\nFitted train: {len(train_X)}\n"
        f"Test: {len(test_idx)}\nMirrored training: {args.mirror_augment}\n"
        f"Note: {warning}\n\nAccuracy: {accuracy:.4f}\n\n{report}\n",
        encoding="utf-8",
    )
    # Cell labels show actual numbers of test examples. Color shows the
    # percentage per actual class (row), so unequal class sizes compare fairly.
    cm_counts = confusion_matrix(y[test_idx], predicted, labels=labels)
    row_totals = cm_counts.sum(axis=1, keepdims=True)
    cm_percent = 100 * np.divide(
        cm_counts, row_totals,
        out=np.zeros_like(cm_counts, dtype=float),
        where=row_totals != 0,
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm_percent, cmap="Blues", vmin=0, vmax=100)
    bar = fig.colorbar(im, ax=ax)
    bar.set_label("Share of actual gesture (%)")
    bar.set_ticks([0, 20, 40, 60, 80, 100])
    bar.set_ticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.set_xticks(range(len(labels)), labels, rotation=35, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted gesture")
    ax.set_ylabel("Actual gesture")
    ax.set_title("Gesture confusion matrix (cell counts; color = row %)")
    for row in range(len(labels)):
        for col in range(len(labels)):
            pct = cm_percent[row, col]
            count = cm_counts[row, col]
            ax.text(col, row, str(int(count)), ha="center", va="center",
                    color="white" if pct >= 55 else "black", fontsize=10)
    fig.tight_layout()
    fig.savefig(args.reports / "confusion_matrix.png", dpi=160)
    plt.close(fig)

    # Retrain on all available data for the actual live demo. Evaluation above
    # remains based only on the held-out partition, not on this final model.
    full_X, full_y = X, y
    if args.mirror_augment:
        full_X = np.concatenate([X, mirror_features(X)], axis=0)
        full_y = np.concatenate([y, y], axis=0)
    final_model = classifier()
    final_model.fit(full_X, full_y)
    args.model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": final_model,
        "classes": labels,
        "feature_columns": FEATURE_COLUMNS,
        "normalization": "wrist-origin/wrist-to-middle-mcp-distance-v1",
        "mirrored_training": args.mirror_augment,
    }, args.model)
    print(f"Saved model: {args.model}")
    print(f"Saved evaluation: {args.reports / 'evaluation.txt'}")
    print(f"Saved confusion matrix: {args.reports / 'confusion_matrix.png'}")


if __name__ == "__main__":
    main()
