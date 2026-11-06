"""Create reproducible train/test CSV splits from landmark recordings."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=root / 'data' / 'landmarks')
    parser.add_argument('--output', type=Path, default=root / 'data' / 'split')
    parser.add_argument('--label', default=None, help='Only split one gesture label, e.g. clock')
    parser.add_argument('--test-size', type=float, default=0.2)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    paths = sorted(args.data.rglob('*.csv'))
    if not paths:
        raise SystemExit(f'No CSV recordings found under {args.data}')
    frames = [pd.read_csv(path).assign(_source=path.name) for path in paths]
    data = pd.concat(frames, ignore_index=True)
    if args.label:
        data = data[data['label'].astype(str) == args.label].copy()
        if data.empty:
            raise SystemExit(f'No recordings found for label {args.label!r}')
    if 'label' not in data or data['label'].nunique() < 1:
        raise SystemExit('No gesture labels found.')
    stratify = data['label'] if data['label'].nunique() > 1 else None
    train, test = train_test_split(data, test_size=args.test_size,
                                   random_state=args.seed, stratify=stratify)
    for name, frame in (('train', train), ('test', test)):
        target = args.output / name
        target.mkdir(parents=True, exist_ok=True)
        for source, part in frame.groupby('_source'):
            part.drop(columns='_source').to_csv(target / source, index=False)
    print(f'Train: {len(train)} samples')
    print(train['label'].value_counts().sort_index().to_string())
    print(f'Test: {len(test)} samples')
    print(test['label'].value_counts().sort_index().to_string())
    print(f'Created: {args.output}')


if __name__ == '__main__':
    main()
