"""
MLflow experiment logging.
Logs every CiteFind and CiteCheck run for the Analytics page.
"""
import os
import time
import mlflow
from config import cfg

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
mlflow.set_tracking_uri(cfg.MLFLOW_TRACKING_URI)
mlflow.set_experiment("citelens")


def log_citefind_run(
    abstract: str,
    n_claims: int,
    n_papers: int,
    n_groups: int,
    latency: float,
    extra: dict = {},
):
    try:
        with mlflow.start_run(run_name=f"citefind_{int(time.time())}"):
            mlflow.log_param("abstract_len", len(abstract))
            mlflow.log_param("openai_model", cfg.OPENAI_MODEL)
            mlflow.log_param("top_k", cfg.TOP_K_PAPERS)
            mlflow.log_metric("n_claims", n_claims)
            mlflow.log_metric("n_papers_found", n_papers)
            mlflow.log_metric("n_groups_output", n_groups)
            mlflow.log_metric("latency_s", latency)
            for k, v in extra.items():
                mlflow.log_metric(k, v)
    except Exception as e:
        print(f"[MLflow] citefind log failed: {e}")


def log_citecheck_run(
    n_citations: int,
    verdicts: list,
    latency: float,
    extra: dict = {},
):
    try:
        n_verified = verdicts.count("verified")
        n_mismatch = verdicts.count("metadata_mismatch")
        n_not_found = verdicts.count("not_found")
        verified_rate = n_verified / n_citations if n_citations else 0

        with mlflow.start_run(run_name=f"citecheck_{int(time.time())}"):
            mlflow.log_metric("n_citations", n_citations)
            mlflow.log_metric("n_verified", n_verified)
            mlflow.log_metric("n_metadata_mismatch", n_mismatch)
            mlflow.log_metric("n_not_found", n_not_found)
            mlflow.log_metric("verified_rate", round(verified_rate, 3))
            mlflow.log_metric("latency_s", latency)
            for k, v in extra.items():
                mlflow.log_metric(k, v)
    except Exception as e:
        print(f"[MLflow] citecheck log failed: {e}")