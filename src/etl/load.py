from pathlib import Path
from typing import Dict
import pandas as pd
import json


def save_outputs(dfs: Dict[str, pd.DataFrame], report: Dict, out_dir: Path):
    # save each dataframe as parquet and csv
    for name, df in dfs.items():
        base = out_dir / f'{name}'
        base.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(base.with_suffix('.parquet')) , index=False)
        df.to_csv(str(base.with_suffix('.csv')), index=False)
    # write report
    with open(out_dir / 'data_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
