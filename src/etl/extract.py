from pathlib import Path
from typing import Dict
import pandas as pd
import logging

SUPPORTED_EXT = ['.csv', '.parquet', '.pq', '.xlsx', '.xls']


def read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    logging.info('Reading %s', path)
    if suffix == '.csv':
        return pd.read_csv(path)
    if suffix in ['.parquet', '.pq']:
        return pd.read_parquet(path)
    if suffix in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    raise ValueError(f'Unsupported file type: {suffix}')


def extract_all(input_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all supported files from input_dir and return a dict keyed by filename (source).
    It adds a small metadata column `__source_file` to trace origin.
    """
    out = {}
    for p in sorted(input_dir.glob('*')):
        if p.suffix.lower() not in SUPPORTED_EXT:
            logging.debug('Skipping unsupported file %s', p)
            continue
        try:
            df = read_file(p)
            df = df.copy()
            df['__source_file'] = p.name
            key = p.stem
            out[key] = df
        except Exception as e:
            logging.exception('Failed to read %s: %s', p, e)
    return out
