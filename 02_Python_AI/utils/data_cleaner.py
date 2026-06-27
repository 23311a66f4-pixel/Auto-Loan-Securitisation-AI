"""
Module 6 — Data cleaning.

Handles missing values, duplicates, dtypes, invalid ranges and basic outlier capping.
Pure functions: each takes a DataFrame and returns a cleaned copy.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from config.config import get_logger

log = get_logger("data_cleaner")


def clean_loans(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["LoanID"]).copy()
    # numeric coercion for risk fields
    for c in ["PD_Estimate", "LGD_Estimate", "EAD", "ECL_Provision", "CurrentBalance",
              "OriginalLoanAmount", "LTV_Current", "DTI_Ratio"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # clamp probabilities/ratios to valid ranges
    df["PD_Estimate"] = df["PD_Estimate"].clip(0, 1)
    df["LGD_Estimate"] = df["LGD_Estimate"].clip(0, 1)
    df["LTV_Current"] = df["LTV_Current"].clip(lower=0)
    df["DelinquencyDays"] = pd.to_numeric(df["DelinquencyDays"], errors="coerce").fillna(0).clip(lower=0)
    df["IsDefaulted"] = df["IsDefaulted"].astype(int)
    # ModificationType is sparse by design (only modified loans) -> fill label
    if "ModificationType" in df.columns:
        df["ModificationType"] = df["ModificationType"].fillna("None")
    n_null = int(df[["PD_Estimate", "LGD_Estimate", "EAD"]].isnull().sum().sum())
    if n_null:
        log.warning("Loans: %d null risk values remain after coercion", n_null)
    log.info("Cleaned loans: %d rows", len(df))
    return df


def clean_dpd(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["SnapshotDate", "LoanID"]).copy()
    df["DPD_Days"] = pd.to_numeric(df["DPD_Days"], errors="coerce").fillna(0).clip(lower=0)
    for flag in ["CureFlag", "RollFlag", "RepossessionFlag", "WriteOffFlag"]:
        if flag in df.columns:
            df[flag] = df[flag].astype(str).str.upper().isin(["TRUE", "1", "YES"])
    log.info("Cleaned dpd: %d rows", len(df))
    return df


def clean_dynamic(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["ReportingDate"]).copy()
    df = df.sort_values("ReportingDate").reset_index(drop=True)
    log.info("Cleaned dynamic: %d rows", len(df))
    return df


def clean_vintage(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["VintageID", "MonthsOnBook"]).copy()
    df = df.sort_values(["VintageID", "MonthsOnBook"]).reset_index(drop=True)
    log.info("Cleaned vintage: %d rows", len(df))
    return df


def clean_all(data: dict) -> dict:
    return {
        "loans": clean_loans(data["loans"]),
        "dpd": clean_dpd(data["dpd"]),
        "dynamic": clean_dynamic(data["dynamic"]),
        "vintage": clean_vintage(data["vintage"]),
    }
