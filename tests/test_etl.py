# Basic smoke test for core ETL functions
import pandas as pd
from src.etl.extract import read_file
from src.etl.transform import transform_sources
from src.etl.validate import validate_datasets


def test_transform_validate_roundtrip():
    # Build a small DataFrame emulating a revenue extract
    df = pd.DataFrame({
        'CustomerID': ['C1', 'C2', 'C2', 'C3'],
        'Rev': ['100.0', '200.5', '200.5', 'invalid'],
        'Region_Name': ['North', 'South', 'South', None]
    })
    sources = {'revenue_sample': df}
    transformed = transform_sources(sources)
    validated, report = validate_datasets(transformed)
    assert 'revenue_sample' in validated
    # C3 has invalid revenue -> treated as 0.0 and accepted by schema if >=0
    assert report['revenue_sample']['input_rows'] == 4
