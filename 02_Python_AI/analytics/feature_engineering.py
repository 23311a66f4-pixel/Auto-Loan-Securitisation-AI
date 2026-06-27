"""
Module 7 — Feature engineering.

Derives business features on the loan tape used by analytics and ML:
loan age, remaining tenure, risk category, collection ratio, loss ratio, delinquency
flags, LTV bands, vintage label, payment behaviour and pool metrics.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from config.config import get_logger, NPA_DPD

log = get_logger("feature_engineering")


def engineer_loan_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # vintage cohort from origination quarter
    if "OriginationDate" in df.columns:
        df["VintageQuarter"] = df["OriginationDate"].dt.to_period("Q").astype(str)
        df["VintageYear"] = df["OriginationDate"].dt.year
    # collection ratio: payments made vs due
    df["CollectionRatio"] = np.where(
        df["TotalPaymentsDue"] > 0,
        df["TotalPaymentsMade"] / df["TotalPaymentsDue"], np.nan)
    # loss ratio
    df["LossRatio"] = np.where(
        df["EAD"] > 0, df["NetLoss"] / df["EAD"], 0.0)
    # delinquency flags
    df["Is30Plus"] = (df["DelinquencyDays"] >= 30).astype(int)
    df["Is60Plus"] = (df["DelinquencyDays"] >= 60).astype(int)
    df["Is90Plus"] = (df["DelinquencyDays"] >= NPA_DPD).astype(int)
    # LTV band
    df["LTV_Band"] = pd.cut(df["LTV_Current"],
                            bins=[-0.01, 0.5, 0.6, 0.7, 0.8, 0.9, np.inf],
                            labels=["0-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90%+"])
    # CIBIL band
    df["CIBIL_Band"] = pd.cut(df["CIBIL_Score_Current"],
                              bins=[0, 600, 650, 700, 750, 800, 900],
                              labels=["<600", "600-650", "650-700", "700-750", "750-800", "800+"])
    # risk category from PD
    df["RiskCategory"] = pd.cut(df["PD_Estimate"],
                                bins=[-0.01, 0.02, 0.05, 0.10, 0.20, 1.01],
                                labels=["Very Low", "Low", "Medium", "High", "Very High"])
    # chronic delinquency proxy
    df["DelinquencyHistoryScore"] = (
        df.get("Times30DPD_Last12M", 0) * 1
        + df.get("Times60DPD_Last12M", 0) * 2
        + df.get("Times90DPD_Last12M", 0) * 3)
    # seasoning ratio
    df["SeasoningRatio"] = np.where(
        df["OriginalTerm"] > 0, df["MonthsOnBook"] / df["OriginalTerm"], 0.0)
    log.info("Engineered %d loan features", df.shape[1])
    return df


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    d = engineer_loan_features(clean_loans(load_all()["loans"]))
    print(d[["LoanID", "RiskCategory", "LTV_Band", "CollectionRatio"]].head())
