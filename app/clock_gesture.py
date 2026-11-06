"""Rule-based detector for the two-hand wrist-pointing clock gesture."""
from __future__ import annotations
import math

def _distance(a, b):
    return math.hypot(float(a.x) - float(b.x), float(a.y) - float(b.y))

def _scale(hand):
    return max(_distance(hand[0], hand[9]), 1e-6)

def _index_is_extended(hand):
    scale = _scale(hand)
    index = _distance(hand[8], hand[0]) / scale
    other = sum(_distance(hand[i], hand[0]) / scale for i in (12, 16, 20)) / 3
    return index > 1.35 and index > other * 1.25

def _is_closed(hand):
    scale = _scale(hand)
    tips = (_distance(hand[8], hand[0]), _distance(hand[12], hand[0]),
            _distance(hand[16], hand[0]), _distance(hand[20], hand[0]))
    return max(tips) / scale < 1.45

def detects_wrist_point(hands) -> bool:
    """Return true when an extended index points at the other hand's wrist."""
    if len(hands) < 2:
        return False
    for pointer in hands:
        if not _index_is_extended(pointer):
            continue
        for target in hands:
            if target is pointer or not _is_closed(target):
                continue
            if _distance(pointer[8], target[0]) / _scale(pointer) < 1.15:
                return True
    return False
