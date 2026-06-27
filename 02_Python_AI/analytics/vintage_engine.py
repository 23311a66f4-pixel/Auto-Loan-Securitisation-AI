"""
Module 10 — Vintage / static-pool analysis.

Cumulative loss curves, pool-factor curves and vintage comparison from the static
pool dataset.
"""
from __future__ import annotations
import pandas as pd
from config.config import get_logger

log = get_logger("vintage_engine")


def loss_curves(vintage: pd.DataFrame) -> pd.DataFrame:
    """Cumulative net-loss-rate curve per vintage by months-on-book."""
    return vintage.pivot_table(index="MonthsOnBook", columns="VintageID",
                               values="CumulativeNetLossRate").sort_index()


def pool_factor_curves(vintage: pd.DataFrame) -> pd.DataFrame:
    return vintage.pivot_table(index="MonthsOnBook", columns="VintageID",
                               values="PoolFactor").sort_index()


def vintage_summary(vintage: pd.DataFrame) -> pd.DataFrame:
    """Latest MOB snapshot per vintage with headline metrics."""
    idx = vintage.groupby("VintageID")["MonthsOnBook"].idxmax()
    latest = vintage.loc[idx].copy()
    cols = ["VintageID", "MonthsOnBook", "OriginalLoanCount", "OriginalPoolBalance",
            "CumulativeDefaults_Count", "CumulativeNetLoss", "CumulativeNetLossRate",
            "PoolFactor", "CurrentDelinq30Plus", "RemainingPoolBalance"]
    out = latest[cols].sort_values("CumulativeNetLossRate", ascending=False).reset_index(drop=True)
    log.info("Vintage summary: %d cohorts", len(out))
    return out


def worst_vintage(vintage: pd.DataFrame) -> dict:
    s = vintage_summary(vintage)
    top = s.iloc[0]
    return {"vintage": top["VintageID"],
            "cum_net_loss_rate": float(top["CumulativeNetLossRate"]),
            "delinq_30plus": float(top["CurrentDelinq30Plus"])}


def cnl_at_mob(vintage: pd.DataFrame, mob: int) -> pd.DataFrame:
    sub = vintage[vintage["MonthsOnBook"] == mob]
    return sub[["VintageID", "CumulativeNetLossRate"]].sort_values(
        "CumulativeNetLossRate", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_vintage
    v = clean_vintage(load_all()["vintage"])
    print(vintage_summary(v).to_string(index=False))
    print("Worst:", worst_vintage(v))
