# Python Assignment ETL Pipeline

This repository contains a Python-based reporting pipeline that loads, cleans, validates, transforms, and combines datasets from multiple enterprise sources to produce reporting-ready outputs consumable by BI tools.

Structure
- src/etl: core pipeline modules (extract, transform, validate, load, main)
- config: configuration and mappings
- data/sample: sample data placeholders (gitignored)
- outputs: generated clean datasets (gitignored)
- tests: basic unit tests

Quick start
1. Create and activate a virtual environment (Python 3.9+ recommended)
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
2. Install dependencies
   pip install -r requirements.txt
3. Place your weekly extracts in a folder (e.g. data/inputs)
4. Run the pipeline
   python -m src.etl.main --input-dir data/inputs --output-dir outputs

What this pipeline does
- Extract: load CSV/Excel/Parquet files from a folder and tag them by source
- Clean & transform: standardize column names, normalize datatypes, deduplicate, derive revenue/region
- Validate: run schema checks and collect counts of excluded/invalid rows
- Load: write clean datasets (Parquet + CSV) and a data-quality report

Next steps
- Add mapping tables and more validation rules specific to your systems
- Add CI tests and sample golden datasets for regression
- Add connectors to cloud storage or a data warehouse if needed
