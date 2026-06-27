# AI Agent for Auto Loan Securitisation Risk Analytics & Investor Reporting

A production-style Python platform that analyses an auto-loan securitisation portfolio,
reproduces the business logic behind the Power BI dashboards, and adds IFRS 9 ECL
analytics, DPD/roll-rate analysis, static-pool vintage curves, dynamic-loss & waterfall
analysis, stress testing, an honest ML layer, rule-based AI agents, Power BI export and
automated Word/Excel reporting.

> **Pool:** ZAAUTO2024-1 — 500 loans, auto-loan ABS (synthetic project data).

---

## Business Problem

Securitisation analysts must turn raw loan-level and monthly performance data into the
risk metrics that credit committees, rating agencies, investors and regulators demand —
ECL provisions, delinquency trends, vintage loss curves, prepayment speeds and trigger
status. Doing this by hand each month is slow and error-prone. This project automates the
full path from raw CSV to investor-ready report and dashboard tables.

## What it does

- **IFRS 9 / ECL** — loan-level PD × LGD × EAD, stage classification, coverage ratios,
  top ECL contributors. The independent recompute reconciles to the model's
  `ECL_Provision` column to within rounding (portfolio variance ≈ ₹0.05).
- **DPD analytics** — bucket distribution, roll/transition matrix, cure & default rates.
- **Vintage / static pool** — cumulative net-loss curves, pool-factor curves, worst-vintage detection.
- **Dynamic loss & waterfall** — collection efficiency, CPR/SMM, excess spread, sequential cash-flow waterfall.
- **Stress testing** — base / moderate / severe / crisis ECL under PD/LGD multipliers.
- **Machine learning** — default-risk classifiers with **honest small-sample handling** (see note below).
- **AI agents** — portfolio-health, IFRS 9, investor-reporting, Q&A and dashboard-narrator agents (rule-based, LLM-optional).
- **Power BI export** — refresh-ready CSVs + a consolidated Excel workbook.
- **Automated reports** — Word (.docx) and Excel summary.

## Architecture

```
raw CSV ─▶ utils (load + clean) ─▶ analytics (feature eng, IFRS9, DPD, vintage,
          dynamic loss, stress) ─▶ ml ─▶ agents ─▶ powerbi export + reports
```
Layered: each layer depends only on the ones beneath it. All paths/thresholds live in
`config/config.py`.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py                  # full pipeline: analytics + ML + agents + exports + reports
streamlit run app_streamlit.py  # interactive dashboard + AI chat
python -m analytics.ifrs9_engine     # run any module standalone
```

Outputs land in `powerbi/` (dashboard tables), `reports/` (Word + Excel), `plots/` (PNGs)
and `models/` (trained models + metrics JSON).

## AI Agents

| Agent | Purpose |
|---|---|
| PortfolioRiskAgent | Portfolio-health verdict & risk commentary |
| IFRS9Assistant | ECL / PD / LGD / EAD explanations, top contributors |
| InvestorReportingAgent | Investor-style portfolio summary |
| PortfolioQAAgent | Natural-language Q&A router |
| DashboardNarrator | Auto executive narrative per dashboard page |

Agents are **rule-based and run offline** (reproducible, no API key). Set
`AGENT_BACKEND=llm` with a provider key to route phrasing through an LLM; the underlying
numbers are always computed locally.

## ML Models — honest note

The loan tape has **500 loans with only ~9 defaults**. That is far below the volume needed
for a reliable credit model. The ML module trains Logistic Regression / Random Forest
(and XGBoost if installed) with stratified cross-validation, **but prints a small-sample
warning and labels all metrics as illustrative / proof-of-concept**. Do not use these as a
production default model. Supply a larger loan-level dataset to change this.

## Power BI Integration

`powerbi/` contains `kpi_summary.csv`, `dpd_distribution.csv`, `vintage_summary.csv`,
`dynamic_loss_trends.csv`, `stress_scenarios.csv`, `top_ecl_contributors.csv`,
`waterfall.csv`, plus `powerbi_master.xlsx`. Point Power BI at this folder and refresh.

## Future Improvements

- Larger labelled dataset to make ML production-grade.
- Live LLM agent with a vector store over rating-agency methodology PDFs.
- Contractual waterfall from the actual deal term sheet.
- Scheduled refresh + FastAPI service.

## Project provenance & honesty

This is a portfolio/learning project on synthetic securitisation data. Numbers are derived
from the uploaded datasets; assumptions (tranche sizing, stress multipliers) are stated in
code and reports. It is not affiliated with any bank or rating agency.
