"""Stable paired-hand features for training/evaluating the clock gesture."""
from __future__ import annotations

from app.gesture_features import normalize_landmarks

PAIR_FEATURE_COLUMNS = [
    f'{hand}_{axis}{index}'
    for hand in ('hand_a', 'hand_b')
    for index in range(21)
    for axis in ('x', 'y', 'z')
]


def normalize_pair(hands):
    if len(hands) != 2:
        raise ValueError(f'Expected two hands, got {len(hands)}')
    return tuple(normalize_landmarks(hand) for hand in hands)
