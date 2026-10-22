from pathlib import Path
import logging
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from pipeline import process_pipeline, LOG_FILE, REPORT_FILE, CLEANED_FILE, DATA_DIR

app = Flask(__name__)
app.secret_key = "local-task3-demo"
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded = request.files.get("dataset")
        if not uploaded or not uploaded.filename:
            flash("Choose a CSV file first.")
            return redirect(url_for("index"))
        if not uploaded.filename.lower().endswith(".csv"):
            flash("Only CSV files are supported.")
            return redirect(url_for("index"))
        safe_name = Path(uploaded.filename).name
        uploaded.save(DATA_DIR / safe_name)
        flash(f"Uploaded {safe_name}. Pipeline will run now.")
        return redirect(url_for("run_pipeline_route"))

    try:
        result = process_pipeline()
        df = result["data"]
        return render_template(
            "index.html",
            result=result,
            columns=list(df.columns),
            rows=df.head(10).fillna("").to_dict("records"),
            log_exists=LOG_FILE.exists(),
            report_exists=REPORT_FILE.exists(),
            error=None,
        )
    except Exception as exc:
        logging.exception("Dashboard pipeline failed")
        return render_template(
            "index.html", result=None, columns=[], rows=[],
            log_exists=LOG_FILE.exists(), report_exists=REPORT_FILE.exists(),
            error=str(exc),
        )

@app.route("/run")
def run_pipeline_route():
    try:
        process_pipeline()
        flash("Pipeline ran successfully; output and monitoring report refreshed.")
    except Exception as exc:
        logging.exception("Manual pipeline run failed")
        flash(f"Pipeline failed: {exc}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=False)
