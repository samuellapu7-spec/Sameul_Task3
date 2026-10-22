
from pathlib import Path
from datetime import datetime
import logging
import shutil
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "outputs"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

CLEANED_FILE = OUTPUT_DIR / "cleaned_delivery_data.csv"
REPORT_FILE = OUTPUT_DIR / "data_quality_report.txt"
LOG_FILE = OUTPUT_DIR / "pipeline.log"
BACKUP_DIR = OUTPUT_DIR / "backups"

BACKUP_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
    force=True,
)


def choose_source(source_path=None):
    """Find and validate the input CSV file."""

    if source_path:
        source = Path(source_path)

        if not source.is_absolute():
            source = BASE / source

        if not source.is_file():
            raise FileNotFoundError(
                f"Source CSV not found: {source}"
            )

        return source

    candidates = [
        p for p in DATA_DIR.glob("*.csv")
        if p.name != CLEANED_FILE.name
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No CSV file found in {DATA_DIR}. "
            "Add a CSV file to the data folder."
        )

    # Use the most recently added/updated CSV (e.g. the latest upload).
    return max(candidates, key=lambda p: p.stat().st_mtime)


def process_pipeline(source_path=None):
    """Validate, process, monitor and save delivery data."""

    started = datetime.now()
    source = choose_source(source_path)

    logging.info("Pipeline started: %s", source.name)

    try:
        # 1. Load source dataset
        df = pd.read_csv(source, low_memory=False)

        if df.empty:
            raise ValueError("Source CSV contains no data rows.")

        original_rows = len(df)
        original_columns = len(df.columns)

        # 2. Standardise column names
        df.columns = df.columns.astype(str).str.strip()

        if len(df.columns) == 0:
            raise ValueError("CSV contains no columns.")

        # 3. Remove exact duplicate rows
        duplicates = int(df.duplicated().sum())
        df = df.drop_duplicates().copy()

        logging.info("Duplicate rows removed: %d", duplicates)

        # 4. Validate date columns
        date_columns = [
            column for column in df.columns
            if "date" in column.lower()
        ]

        invalid_dates = {}

        for column in date_columns:
            original = df[column].copy()

            parsed = pd.to_datetime(
                original,
                errors="coerce",
                dayfirst=True,
                format="mixed"
            )

            invalid_mask = (
                original.notna()
                & original.astype(str).str.strip().ne("")
                & parsed.isna()
            )

            invalid_dates[column] = int(invalid_mask.sum())

            # Invalid or empty dates stay as missing values (blank in CSV).
            df[column] = parsed.dt.strftime("%Y-%m-%d")

            logging.info(
                "Date validation: %s; invalid values: %d",
                column,
                invalid_dates[column]
            )

        # 5. Missing-value monitoring
        missing_by_column = {
            str(column): int(count)
            for column, count in df.isna().sum().items()
            if int(count) > 0
        }

        missing_cells = int(df.isna().sum().sum())

        # 6. Back up previous successful output
        if CLEANED_FILE.exists():
            stamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            backup_path = BACKUP_DIR / (
                f"cleaned_delivery_data_{stamp}.csv"
            )

            shutil.copy2(CLEANED_FILE, backup_path)

            logging.info(
                "Previous output backed up: %s",
                backup_path.name
            )

        # 7. Save safely using a temporary file
        # Temporary and destination files are on the same drive.
        temporary_file = CLEANED_FILE.with_name(
            "cleaned_delivery_data.tmp.csv"
        )

        try:
            df.to_csv(temporary_file, index=False)
            temporary_file.replace(CLEANED_FILE)
        finally:
            if temporary_file.exists():
                temporary_file.unlink()

        elapsed = (
            datetime.now() - started
        ).total_seconds()

        # 8. Create monitoring report
        report_lines = [
            "UNIT 3 - TASK 3 PIPELINE MONITORING REPORT",
            "=" * 48,
            "Student: Sameul",
            "Scenario: SkyRoute Logistics Ltd",
            f"Run time: {started.isoformat(timespec='seconds')}",
            f"Source file: {source.name}",
            f"Rows before processing: {original_rows}",
            f"Columns: {original_columns}",
            f"Duplicate rows removed: {duplicates}",
            f"Rows after processing: {len(df)}",
            f"Date columns checked: {len(date_columns)}",
            f"Invalid date values: {sum(invalid_dates.values())}",
            f"Missing cells after processing: {missing_cells}",
            f"Execution duration: {elapsed:.2f} seconds",
            "",
            "DATE VALIDATION",
        ]

        report_lines += [
            f"{column}: {count} invalid value(s)"
            for column, count in invalid_dates.items()
        ] or ["No date columns detected."]

        report_lines += ["", "MISSING VALUES BY COLUMN"]

        report_lines += [
            f"{column}: {count}"
            for column, count in missing_by_column.items()
        ] or ["No missing values found."]

        # Use absolute paths so the report also works in unit tests.
        report_lines += [
            "",
            f"Processed CSV: {CLEANED_FILE}",
            f"Log file: {LOG_FILE}",
            f"Backup folder: {BACKUP_DIR}",
            "Pipeline status: SUCCESS",
        ]

        REPORT_FILE.write_text(
            "\n".join(report_lines),
            encoding="utf-8"
        )

        logging.info(
            "Pipeline completed successfully. "
            "Rows=%d, duplicates=%d, duration=%.2fs",
            len(df),
            duplicates,
            elapsed
        )

        # 9. Prepare dashboard chart data
        def count_column(terms, top=None):
            column = next(
                (
                    col for col in df.columns
                    if any(term in col.lower() for term in terms)
                ),
                None
            )

            if column is None:
                return {}

            counts = (
                df[column]
                .fillna("Missing")
                .astype(str)
                .value_counts()
            )

            if top:
                counts = counts.head(top)

            return counts.to_dict()

        metrics = {
            "before": original_rows,
            "after": len(df),
            "duplicates": duplicates,
            "columns": original_columns,
            "missing": missing_cells,
            "invalid_dates": sum(invalid_dates.values()),
            "duration": round(elapsed, 2),
        }

        return {
            "data": df,
            "metrics": metrics,
            "status": count_column(["status"]),
            "modes": count_column(["shipment mode", "mode"]),
            "countries": count_column(["country"], top=8),
            "source": source.name,
        }

    except Exception:
        logging.exception("Pipeline execution failed")
        raise


def rollback_latest_backup():
    """Restore the latest available processed-data backup."""

    backups = sorted(
        BACKUP_DIR.glob("cleaned_delivery_data_*.csv")
    )

    if not backups:
        raise FileNotFoundError(
            "No rollback backup is available."
        )

    latest_backup = backups[-1]
    shutil.copy2(latest_backup, CLEANED_FILE)

    logging.warning(
        "Rollback performed using: %s",
        latest_backup.name
    )

    return latest_backup


if __name__ == "__main__":
    import sys

    # Optional: python pipeline.py data\your_file.csv
    result = process_pipeline(sys.argv[1] if len(sys.argv) > 1 else None)

    print("Pipeline completed successfully.")
    print("Metrics:", result["metrics"])
    print("Report:", REPORT_FILE)
    print("Log:", LOG_FILE)
