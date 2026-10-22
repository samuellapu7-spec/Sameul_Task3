import unittest
import tempfile
from pathlib import Path
import pandas as pd
import pipeline

class PipelineTests(unittest.TestCase):
    def test_duplicate_rows_removed_and_output_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            source = temp_dir / "test.csv"
            pd.DataFrame([
                {"ID": "A1", "Scheduled Date": "01/10/2026"},
                {"ID": "A1", "Scheduled Date": "01/10/2026"},
                {"ID": "A2", "Scheduled Date": "not-a-date"},
            ]).to_csv(source, index=False)

            # Redirect output paths for isolated test
            old_cleaned, old_report, old_backup = pipeline.CLEANED_FILE, pipeline.REPORT_FILE, pipeline.BACKUP_DIR
            try:
                pipeline.CLEANED_FILE = temp_dir / "cleaned.csv"
                pipeline.REPORT_FILE = temp_dir / "report.txt"
                pipeline.BACKUP_DIR = temp_dir / "backups"
                pipeline.BACKUP_DIR.mkdir()
                result = pipeline.process_pipeline(source)
                self.assertEqual(result["metrics"]["before"], 3)
                self.assertEqual(result["metrics"]["after"], 2)
                self.assertEqual(result["metrics"]["duplicates"], 1)
                self.assertTrue(pipeline.CLEANED_FILE.exists())
                self.assertTrue(pipeline.REPORT_FILE.exists())
            finally:
                pipeline.CLEANED_FILE, pipeline.REPORT_FILE, pipeline.BACKUP_DIR = old_cleaned, old_report, old_backup

if __name__ == "__main__":
    unittest.main()
