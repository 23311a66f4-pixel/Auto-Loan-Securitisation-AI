"""
Module 14 — Power BI export.

Writes refresh-ready CSVs (and one Excel summary) to the /powerbi folder for the
dashboard to consume: KPI table, IFRS9 summary, DPD distribution, vintage summary,
dynamic-loss trends, stress scenarios and ML predictions.
"""
from __future__ import annotations
import pandas as pd
from config.config import get_logger, POWERBI_DIR

log = get_logger("powerbi_export")


def export_tables(tables: dict) -> list:
    written = []
    for name, df in tables.items():
        if df is None or (hasattr(df, "empty") and df.empty):
            continue
        path = POWERBI_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        written.append(path.name)
        log.info("Exported %s (%d rows)", path.name, len(df))
    # consolidated Excel
    xlsx = POWERBI_DIR / "powerbi_master.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        for name, df in tables.items():
            if df is not None and not (hasattr(df, "empty") and df.empty):
                df.to_excel(xw, sheet_name=name[:31], index=False)
    written.append(xlsx.name)
    return written
