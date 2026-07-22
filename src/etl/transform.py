from typing import Dict
import pandas as pd
import numpy as np
import logging


STANDARD_COLUMNS = {
    'customerid': 'customer_id',
    'cust_id': 'customer_id',
    'custid': 'customer_id',
    'region_name': 'region',
    'rev': 'revenue',
}


def _standardize_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c: c.strip().lower().replace(' ', '_') for c in df.columns}
    df = df.rename(columns=cols)
    df = df.rename(columns=STANDARD_COLUMNS)
    return df


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if 'revenue' in df.columns:
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0.0)
    # Dates
    for dcol in ['date', 'created_at', 'closed_at']:
        if dcol in df.columns:
            df[dcol] = pd.to_datetime(df[dcol], errors='coerce')
    return df


def transform_sources(sources: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Apply cleaning steps for each source DataFrame and return transformed versions.
    Steps:
      - Standardize column names
      - Coerce types
      - Drop obvious duplicates
      - Simple enrichment (e.g., revenue -> numeric)
    """
    out = {}
    for name, df in sources.items():
        logging.info('Transforming source %s rows=%d', name, len(df))
        t = df.copy()
        t = _standardize_cols(t)
        t = _coerce_types(t)
        # Trim whitespace for string columns
        for c in t.select_dtypes(include='object').columns:
            t[c] = t[c].astype(str).str.strip()
        # Basic dedupe by customer_id + date if present
        if 'customer_id' in t.columns:
            before = len(t)
            t = t.drop_duplicates(subset=['customer_id'] + ([ 'date' ] if 'date' in t.columns else []))
            after = len(t)
            logging.info('Dropped %d duplicate rows in %s', before-after, name)
        # Derive a 'issue_risk' flag heuristically
        if 'support_status' in t.columns:
            t['issue_risk'] = t['support_status'].str.lower().isin(['open','escalated','critical'])
        out[name] = t
    return out
