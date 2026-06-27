"""
Module 11b — Stress testing & scenario analysis.

Applies PD/LGD/recovery multipliers from config scenarios to recompute portfolio ECL
under base / moderate / severe / crisis conditions.
"""
from __future__ import annotations
import pandas as pd
from config.config import get_logger, STRESS_SCENARIOS

log = get_logger("stress_testing")


def run_scenarios(loans: pd.DataFrame) -> pd.DataFrame:
    base_ecl = (loans["PD_Estimate"] * loans["LGD_Estimate"] * loans["EAD"]).sum()
    rows = []
    for name, p in STRESS_SCENARIOS.items():
        pd_s = (loans["PD_Estimate"] * p["pd_mult"]).clip(0, 1)
        lgd_s = (loans["LGD_Estimate"] * p["lgd_mult"]).clip(0, 1)
        ecl = (pd_s * lgd_s * loans["EAD"]).sum()
        rows.append({
            "Scenario": name.title(),
            "PD_Mult": p["pd_mult"], "LGD_Mult": p["lgd_mult"],
            "Stressed_ECL": ecl,
            "ECL_Increase": ecl - base_ecl,
            "ECL_Increase_Pct": (ecl - base_ecl) / base_ecl if base_ecl else 0,
        })
    out = pd.DataFrame(rows)
    log.info("Stress scenarios computed; crisis ECL = %.0f", out.iloc[-1]["Stressed_ECL"])
    return out


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    print(run_scenarios(clean_loans(load_all()["loans"])).to_string(index=False))
