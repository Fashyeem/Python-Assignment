from pathlib import Path
from .extract import extract_all
from .transform import transform_sources
from .validate import validate_datasets
from .load import save_outputs
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def run(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logging.info('Starting extraction from %s', input_path)
    raw = extract_all(input_path)

    logging.info('Transforming extracted datasets')
    transformed = transform_sources(raw)

    logging.info('Validating transformed datasets')
    validated, report = validate_datasets(transformed)

    logging.info('Saving outputs to %s', output_path)
    save_outputs(validated, report, output_path)

    logging.info('Pipeline finished. Quality report written.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ETL pipeline')
    parser.add_argument('--input-dir', default='data/inputs', help='Input directory with raw extracts')
    parser.add_argument('--output-dir', default='outputs', help='Output directory for clean datasets')
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)
