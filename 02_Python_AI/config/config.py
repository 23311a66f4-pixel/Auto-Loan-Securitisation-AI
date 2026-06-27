"""
Module 4 — Centralised configuration.

All paths, thresholds, IFRS 9 rules, DPD bucket definitions, stress multipliers and
logging setup live here so no downstream module hard-codes a constant.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path

# --------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_EXPORTS = ROOT / "data" / "exports"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
PLOTS_DIR = ROOT / "plots"
POWERBI_DIR = ROOT / "powerbi"

for _d in (DATA_PROCESSED, DATA_EXPORTS, MODELS_DIR, REPORTS_DIR, PLOTS_DIR, POWERBI_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------- dataset files
DATASETS = {
    "loans": DATA_RAW / "auto_loan_securitisation_data.csv",
    "dpd": DATA_RAW / "dpd_snapshot_history.csv",
    "dynamic": DATA_RAW / "dynamic_loss_monthly.csv",
    "vintage": DATA_RAW / "static_pool_vintage_data.csv",
}

# ------------------------------------------------------------------ IFRS 9 / DPD rules
# DPD bucket lower bounds (inclusive) -> label
DPD_BUCKETS = [
    (0, 0, "Current"),
    (1, 29, "1-29 DPD"),
    (30, 59, "30-59 DPD"),
    (60, 89, "60-89 DPD"),
    (90, 119, "90-119 DPD"),
    (120, 179, "120-179 DPD"),
    (180, 10**9, "180+ DPD"),
]
# IFRS 9 staging by days-past-due (general model)
STAGE_RULES = {"stage1_max_dpd": 29, "stage2_max_dpd": 89}  # >=90 -> Stage 3
NPA_DPD = 90  # RBI default definition

# ------------------------------------------------------------------- stress scenarios
STRESS_SCENARIOS = {
    "base":     {"pd_mult": 1.00, "lgd_mult": 1.00, "recovery_haircut": 0.00},
    "moderate": {"pd_mult": 1.50, "lgd_mult": 1.10, "recovery_haircut": 0.10},
    "severe":   {"pd_mult": 2.50, "lgd_mult": 1.25, "recovery_haircut": 0.25},
    "crisis":   {"pd_mult": 4.00, "lgd_mult": 1.40, "recovery_haircut": 0.40},
}

# ---------------------------------------------------------------- waterfall assumptions
# Illustrative tranche sizing for waterfall validation (replace with deal term sheet).
WATERFALL = {
    "senior_pct": 0.80, "mezz_pct": 0.12, "equity_pct": 0.08,
    "senior_coupon": 0.085, "mezz_coupon": 0.115, "senior_fee_pct": 0.01,
}

# --------------------------------------------------------------------------- ML config
ML = {
    "target_default": "IsDefaulted",
    "random_state": 42,
    "cv_folds": 5,
    "test_size": 0.25,
    # Small-sample guard: number of positive (default) cases below which ML metrics
    # are flagged as illustrative only.
    "min_positives_for_reliable_ml": 50,
}

# ----------------------------------------------------------------------- agent / LLM
AGENT = {
    # "rule" (default, offline, no key) or "llm".
    "backend": os.getenv("AGENT_BACKEND", "rule"),
    "llm_provider": os.getenv("LLM_PROVIDER", "openai"),  # openai | gemini | ollama
    "llm_model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
}

# --------------------------------------------------------------------------- logging
def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to console at INFO level."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
