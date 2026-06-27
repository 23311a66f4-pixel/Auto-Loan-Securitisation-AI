"""
Module 8 — IFRS 9 & Expected Credit Loss engine.

Reproduces the dashboard ECL logic: portfolio ECL = sum(PD x LGD x EAD), stage
classification (DPD-driven), 12-month vs lifetime ECL split, stage migration and
coverage ratios. Validated against the model ECL_Provision column.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from config.config import get_logger, STAGE_RULES

log = get_logger("ifrs9_engine")


def classify_stage(dpd_days: float) -> int:
    if dpd_days <= STAGE_RULES["stage1_max_dpd"]:
        return 1
    if dpd_days <= STAGE_RULES["stage2_max_dpd"]:
        return 2
    return 3


def compute_ecl(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute loan-level ECL = PD x LGD x EAD and stage from DPD."""
    df = df.copy()
    df["ECL_Recompute"] = df["PD_Estimate"] * df["LGD_Estimate"] * df["EAD"]
    df["Stage_FromDPD"] = df["DelinquencyDays"].apply(classify_stage)
    # 12-month ECL for Stage 1, lifetime for Stage 2/3 (here ECL field already final;
    # we split for reporting using a 12m fraction proxy of remaining term)
    horizon = np.minimum(12, df["RemainingTerm"].clip(lower=1)) / df["RemainingTerm"].clip(lower=1)
    df["ECL_12m"] = np.where(df["IFRS9_Stage"] == 1, df["ECL_Recompute"], df["ECL_Recompute"] * horizon)
    df["ECL_Lifetime"] = df["ECL_Recompute"]
    return df


def portfolio_ecl_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_ecl(df)
    rows = []
    for stage in [1, 2, 3]:
        s = df[df["IFRS9_Stage"] == stage]
        rows.append({
            "Stage": f"Stage {stage}",
            "LoanCount": len(s),
            "CurrentBalance": s["CurrentBalance"].sum(),
            "EAD": s["EAD"].sum(),
            "Model_ECL": s["ECL_Provision"].sum(),
            "Recompute_ECL": s["ECL_Recompute"].sum(),
            "CoverageRatio": s["ECL_Provision"].sum() / s["CurrentBalance"].sum()
                             if s["CurrentBalance"].sum() else 0,
        })
    summary = pd.DataFrame(rows)
    total = {
        "Stage": "TOTAL", "LoanCount": summary["LoanCount"].sum(),
        "CurrentBalance": summary["CurrentBalance"].sum(), "EAD": summary["EAD"].sum(),
        "Model_ECL": summary["Model_ECL"].sum(), "Recompute_ECL": summary["Recompute_ECL"].sum(),
        "CoverageRatio": summary["Model_ECL"].sum() / summary["CurrentBalance"].sum(),
    }
    summary = pd.concat([summary, pd.DataFrame([total])], ignore_index=True)
    summary["Variance"] = summary["Model_ECL"] - summary["Recompute_ECL"]
    var = abs(total["Model_ECL"] - total["Recompute_ECL"])
    log.info("Portfolio ECL model=%.2f recompute=%.2f variance=%.4f",
             total["Model_ECL"], total["Recompute_ECL"], var)
    return summary


def stage_migration(df: pd.DataFrame) -> pd.DataFrame:
    """Compare model stage vs DPD-derived stage (proxy for migration check)."""
    df = compute_ecl(df)
    return pd.crosstab(df["IFRS9_Stage"], df["Stage_FromDPD"],
                       rownames=["Model Stage"], colnames=["DPD-Derived Stage"])


def top_ecl_contributors(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = ["LoanID", "Region", "IFRS9_Stage", "CurrentBalance", "PD_Estimate",
            "LGD_Estimate", "EAD", "ECL_Provision"]
    return df.nlargest(n, "ECL_Provision")[cols].reset_index(drop=True)


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    loans = clean_loans(load_all()["loans"])
    print(portfolio_ecl_summary(loans).to_string(index=False))
