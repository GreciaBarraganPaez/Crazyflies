"""Train and evaluate a binary two-hand clock gesture classifier."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.clock_features import PAIR_FEATURE_COLUMNS


def load_data(data_dir):
    paths = sorted(Path(data_dir).rglob('clock_pairs.csv'))
    if not paths:
        raise SystemExit(f'No clock_pairs.csv found under {data_dir}. Record positive and negative samples first.')
    frames = []
    required = {'label', 'person_id', 'session_id', *PAIR_FEATURE_COLUMNS}
    for path in paths:
        frame = pd.read_csv(path)
        missing = required - set(frame.columns)
        if missing:
            raise SystemExit(f'{path}: missing columns: {", ".join(sorted(missing))}')
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True).dropna(subset=list(required))
    labels = set(data['label'].astype(str))
    if labels != {'clock_positive', 'clock_negative'}:
        raise SystemExit(f'Expected clock_positive and clock_negative, found: {sorted(labels)}')
    return data


def classifier():
    return make_pipeline(StandardScaler(), SVC(kernel='rbf', C=3.0, gamma='scale', probability=True, random_state=42))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / 'landmarks')
    parser.add_argument('--model', type=Path, default=ROOT / 'models' / 'clock_pair_svm.joblib')
    parser.add_argument('--reports', type=Path, default=ROOT / 'reports' / 'clock')
    parser.add_argument('--mode', choices=('random', 'session'), default='random')
    args = parser.parse_args()

    data = load_data(args.data)
    X = data[PAIR_FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    y = data['label'].astype(str).to_numpy()
    if args.mode == 'session':
        groups = (data['person_id'].astype(str) + ':' + data['session_id'].astype(str)).to_numpy()
        splitter = GroupShuffleSplit(n_splits=100, test_size=.25, random_state=42)
        for train_idx, test_idx in splitter.split(X, y, groups):
            if set(y[train_idx]) == set(y) and set(y[test_idx]) == set(y):
                break
        else:
            raise SystemExit('Session split needs positive and negative samples in at least two sessions.')
    else:
        train_idx, test_idx = train_test_split(np.arange(len(y)), test_size=.25, random_state=42, stratify=y)

    model = classifier()
    model.fit(X[train_idx], y[train_idx])
    train_pred = model.predict(X[train_idx])
    test_pred = model.predict(X[test_idx])
    labels = ['clock_negative', 'clock_positive']
    train_accuracy = accuracy_score(y[train_idx], train_pred)
    test_accuracy = accuracy_score(y[test_idx], test_pred)
    report = classification_report(y[test_idx], test_pred, labels=labels, zero_division=0)
    gap = train_accuracy - test_accuracy
    args.reports.mkdir(parents=True, exist_ok=True)
    (args.reports / 'evaluation.txt').write_text(
        f'Split: {args.mode}\nSamples: {len(data)}\nTrain: {len(train_idx)}\nTest: {len(test_idx)}\n'
        f'Train accuracy: {train_accuracy:.4f}\nTest accuracy: {test_accuracy:.4f}\n'
        f'Generalization gap: {gap:.4f}\n\n{report}\n', encoding='utf-8')
    cm = confusion_matrix(y[test_idx], test_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm, cmap='Blues')
    ax.set_xticks(range(2), labels, rotation=25, ha='right')
    ax.set_yticks(range(2), labels)
    ax.set_xlabel('Predicted'); ax.set_ylabel('Actual'); ax.set_title('Clock gesture test confusion matrix')
    for i in range(2):
        for j in range(2): ax.text(j, i, str(cm[i, j]), ha='center', va='center')
    fig.tight_layout(); fig.savefig(args.reports / 'confusion_matrix.png', dpi=160); plt.close(fig)
    args.model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'feature_columns': PAIR_FEATURE_COLUMNS,
                 'labels': labels, 'normalization': 'paired wrist-relative landmarks-v1'}, args.model)
    print(f'Train accuracy: {train_accuracy:.1%}')
    print(f'Test accuracy: {test_accuracy:.1%}')
    print(f'Generalization gap: {gap:.1%}')
    print(f'Saved model: {args.model}')
    print(f'Saved report: {args.reports / "evaluation.txt"}')


if __name__ == '__main__':
    main()
