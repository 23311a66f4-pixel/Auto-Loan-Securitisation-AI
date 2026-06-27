"""
Module 11 — Dynamic loss & waterfall analysis.

Monthly loss/collection metrics, CPR/SMM, excess spread and a sequential cash-flow
waterfall validation built from the dynamic loss dataset.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from config.config import get_logger, WATERFALL

log = get_logger("dynamic_loss_engine")


def monthly_trends(dyn: pd.DataFrame) -> pd.DataFrame:
    df = dyn.copy()
    df["CumNetLoss"] = df["NetLoss_ThisMonth"].cumsum()
    df["CumRecoveries"] = df["Recoveries_ThisMonth"].cumsum()
    df["AnnualisedNetLossRate"] = df["MonthlyNetLossRate"] * 12
    return df


def headline_metrics(dyn: pd.DataFrame) -> dict:
    df = dyn.sort_values("ReportingDate")
    last = df.iloc[-1]
    return {
        "latest_month": str(pd.to_datetime(last["ReportingDate"]).date()),
        "eop_balance": float(last["EOP_Balance"]),
        "collection_efficiency": float(last["CollectionEfficiency"]),
        "cpr_annualised": float(last["CPR_Annualised"]),
        "smm": float(last["SMM"]),
        "cum_net_loss": float(df["NetLoss_ThisMonth"].sum()),
        "cum_collections": float(df["CollectionsTotal"].sum()),
        "avg_excess_spread": float(df["ExcessSpread_Monthly"].mean()),
    }


def waterfall(dyn: pd.DataFrame, pool_balance: float) -> pd.DataFrame:
    """Illustrative sequential waterfall for the latest month."""
    last = dyn.sort_values("ReportingDate").iloc[-1]
    coll = float(last["CollectionsTotal"])
    net_loss = float(last["NetLoss_ThisMonth"])
    w = WATERFALL
    senior_bal = pool_balance * w["senior_pct"]
    mezz_bal = pool_balance * w["mezz_pct"]
    steps = []
    remaining = coll
    def step(label, amount):
        nonlocal remaining
        remaining += amount
        steps.append({"Item": label, "Amount": amount, "Remaining": remaining})
    steps.append({"Item": "Total collections available", "Amount": coll, "Remaining": coll})
    step("Less: Senior fees", -coll * w["senior_fee_pct"])
    step("Less: Senior interest", -(senior_bal * w["senior_coupon"] / 12))
    step("Less: Mezzanine interest", -(mezz_bal * w["mezz_coupon"] / 12))
    step("Less: Net loss absorbed", -net_loss)
    steps.append({"Item": "Residual to equity", "Amount": remaining, "Remaining": 0.0})
    return pd.DataFrame(steps)


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_dynamic, clean_loans
    data = load_all()
    dyn = clean_dynamic(data["dynamic"])
    pool = clean_loans(data["loans"])["CurrentBalance"].sum()
    print(headline_metrics(dyn))
    print(waterfall(dyn, pool).to_string(index=False))
