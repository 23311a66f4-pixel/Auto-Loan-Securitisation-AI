"""
Module 9 — DPD analytics.

Builds DPD bucket distributions, roll/transition matrices, cure rates and default
rates from the DPD snapshot history.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from config.config import get_logger, DPD_BUCKETS

log = get_logger("dpd_engine")

BUCKET_ORDER = ["Current", "1-29 DPD", "30-59 DPD", "60-89 DPD",
                "90-119 DPD", "120-179 DPD", "180+ DPD"]


def assign_bucket(dpd: float) -> str:
    for lo, hi, label in DPD_BUCKETS:
        if lo <= dpd <= hi:
            return label
    return "180+ DPD"


def latest_snapshot(dpd: pd.DataFrame) -> pd.DataFrame:
    last_date = dpd["SnapshotDate"].max()
    return dpd[dpd["SnapshotDate"] == last_date].copy(), last_date


def dpd_distribution(dpd: pd.DataFrame) -> pd.DataFrame:
    snap, dt = latest_snapshot(dpd)
    snap["Bucket"] = snap["DPD_Days"].apply(assign_bucket)
    g = snap.groupby("Bucket").agg(
        LoanCount=("LoanID", "count"),
        Balance=("CurrentBalance", "sum")).reindex(BUCKET_ORDER).fillna(0)
    g["PctOfPool"] = g["Balance"] / g["Balance"].sum()
    g = g.reset_index().rename(columns={"index": "Bucket"})
    log.info("DPD distribution built for snapshot %s", str(dt.date()))
    return g


def roll_rate_matrix(dpd: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month transition matrix by balance using prior/current bucket."""
    df = dpd.dropna(subset=["DPD_Bucket", "DPD_Bucket_Prior"]).copy()
    mat = pd.crosstab(df["DPD_Bucket_Prior"], df["DPD_Bucket"],
                      values=df["CurrentBalance"], aggfunc="sum", normalize="index")
    order = [b for b in BUCKET_ORDER if b in mat.index]
    cols = [b for b in BUCKET_ORDER if b in mat.columns]
    return mat.reindex(index=order, columns=cols).fillna(0)


def cure_and_default_rates(dpd: pd.DataFrame) -> dict:
    df = dpd.copy()
    delinq = df[df["DPD_Days"] >= 30]
    cure_rate = df["CureFlag"].mean() if "CureFlag" in df else np.nan
    # roll-to-worse rate
    roll_rate = df["RollFlag"].mean() if "RollFlag" in df else np.nan
    snap, _ = latest_snapshot(dpd)
    npa = snap[snap["DPD_Days"] >= 90]["CurrentBalance"].sum()
    default_rate = npa / snap["CurrentBalance"].sum() if snap["CurrentBalance"].sum() else 0
    return {"cure_rate": float(cure_rate), "roll_rate": float(roll_rate),
            "npa_default_rate": float(default_rate)}


def transition_summary(dpd: pd.DataFrame) -> pd.DataFrame:
    if "TransitionType" not in dpd.columns:
        return pd.DataFrame()
    g = dpd.groupby("TransitionType").agg(
        Count=("LoanID", "count"),
        Balance=("CurrentBalance", "sum")).reset_index()
    g["PctOfBalance"] = g["Balance"] / g["Balance"].sum()
    return g.sort_values("Balance", ascending=False)


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_dpd
    dpd = clean_dpd(load_all()["dpd"])
    print(dpd_distribution(dpd).to_string(index=False))
    print(cure_and_default_rates(dpd))
