"""
Module 5 — Data loading & validation.

Loads each raw CSV, validates that required columns are present, parses dates, and
returns a dict of DataFrames. Raises clear errors when a file or column is missing.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict
import pandas as pd
from config.config import DATASETS, get_logger

log = get_logger("data_loader")

REQUIRED_COLUMNS = {
    "loans": ["LoanID", "CurrentBalance", "OriginalLoanAmount", "DelinquencyDays",
              "IFRS9_Stage", "PD_Estimate", "LGD_Estimate", "EAD", "ECL_Provision",
              "IsDefaulted", "InterestRate", "RemainingTerm", "MonthsOnBook",
              "LTV_Current", "CIBIL_Score_Current", "DTI_Ratio", "Region",
              "VintageID" if False else "OriginationDate"],
    "dpd": ["SnapshotDate", "LoanID", "DPD_Days", "DPD_Bucket", "CurrentBalance",
            "TransitionType", "CureFlag", "RollFlag"],
    "dynamic": ["ReportingDate", "BOP_Balance", "EOP_Balance", "NetLoss_ThisMonth",
                "CollectionsTotal", "CollectionEfficiency", "CPR_Annualised", "SMM"],
    "vintage": ["VintageID", "MonthsOnBook", "OriginalPoolBalance", "CumulativeNetLoss",
                "CumulativeNetLossRate", "PoolFactor", "RemainingPoolBalance"],
}
DATE_COLUMNS = {
    "loans": ["OriginationDate", "CutoffDate", "MaturityDate", "LastPaymentDate"],
    "dpd": ["SnapshotDate", "LastPaymentDate"],
    "dynamic": ["ReportingDate"],
    "vintage": ["VintageStartDate"],
}


def _load_one(key: str, path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset '{key}' not found at {path}")
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS.get(key, []) if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset '{key}' missing required columns: {missing}")
    for col in DATE_COLUMNS.get(key, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    log.info("Loaded '%s': %d rows x %d cols", key, df.shape[0], df.shape[1])
    return df


def load_all() -> Dict[str, pd.DataFrame]:
    """Load and validate every configured dataset."""
    data = {}
    for key, path in DATASETS.items():
        try:
            data[key] = _load_one(key, path)
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to load '%s': %s", key, exc)
            raise
    log.info("All %d datasets loaded successfully.", len(data))
    return data


if __name__ == "__main__":
    d = load_all()
    for k, v in d.items():
        print(f"{k:10s} {v.shape}")
