from typing import Dict, Tuple
import pandera as pa
from pandera import DataFrameSchema, Column, Check
import pandas as pd


# Example schema for a canonical customer revenue dataset
revenue_schema = DataFrameSchema({
    'customer_id': Column(pa.String, nullable=False),
    'revenue': Column(pa.Float, Check.ge(0), nullable=False),
    'region': Column(pa.String, nullable=True),
}, coerce=True)

support_schema = DataFrameSchema({
    'customer_id': Column(pa.String, nullable=False),
    'support_status': Column(pa.String, nullable=True),
    'created_at': Column(pa.DateTime, nullable=True),
}, coerce=True)


def validate_datasets(dfs: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict]:
    """Validate transformed datasets and return only rows that pass validation plus a report.
    The report contains counts of input rows, accepted rows, and rejected rows per source.
    """
    accepted = {}
    report = {}
    for name, df in dfs.items():
        report[name] = {'input_rows': len(df), 'accepted_rows': 0, 'rejected_rows': 0}
        # Pick schema by heuristics
        schema = None
        if 'revenue' in df.columns:
            schema = revenue_schema
        elif 'support_status' in df.columns:
            schema = support_schema
        if schema is None:
            # If we don't have a schema, accept as-is
            accepted[name] = df
            report[name]['accepted_rows'] = len(df)
            continue
        try:
            validated = schema.validate(df, lazy=True)
            accepted[name] = validated
            report[name]['accepted_rows'] = len(validated)
            report[name]['rejected_rows'] = len(df) - len(validated)
        except pa.errors.SchemaErrors as e:
            # Pandera can return the rows that failed via e.failure_cases
            failures = e.failure_cases
            valid_idx = df.index.difference(failures.index if hasattr(failures, 'index') else [])
            validated = df.loc[valid_idx]
            accepted[name] = validated
            report[name]['accepted_rows'] = len(validated)
            report[name]['rejected_rows'] = len(df) - len(validated)
    return accepted, report
