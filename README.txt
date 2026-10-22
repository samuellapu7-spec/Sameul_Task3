SAMEUL TASK 3 - SKYROUTE PIPELINE PROJECT

Files:
- app.py: Flask dashboard and CSV upload
- pipeline.py: main data pipeline, monitoring, report, output backup/rollback helper
- templates/index.html: dashboard charts and data preview
- data/sample_delivery_data.csv: demo CSV for testing
- tests/test_pipeline.py: basic unit test
- SCHEDULING.txt: Windows Task Scheduler setup notes
- requirements.txt: required Python packages

Run on Windows in VS Code:
1. Extract ZIP and open this folder in VS Code.
2. Open Terminal in this folder.
3. Run:
   python -m venv .venv
   .venv\\Scripts\\activate
   python -m pip install -r requirements.txt
   python app.py
4. Visit http://127.0.0.1:5000
5. To run pipeline without dashboard:
   python pipeline.py
6. Run unit test:
   python -m unittest discover -s tests -v

Dataset:
A small sample CSV is included for demo/testing. Upload your real CSV in the dashboard if you have one.
Do not present sample-data results as actual SkyRoute company results.

Important Task 3 coverage:
- P4: Explain manual, scheduled and serverless deployment in your report; this package does not automatically create a cloud/serverless deployment.
- P5: Pipeline processing is automated when run; Windows Task Scheduler must be configured separately.
- P6: Logging, data-quality report, duplicate/date checks, dashboard and unit test.
- M2: Backup helper supports output rollback; Git/GitHub version control and evidence must be configured separately.
The Flask app is intended for local demonstration; debug mode is disabled.
