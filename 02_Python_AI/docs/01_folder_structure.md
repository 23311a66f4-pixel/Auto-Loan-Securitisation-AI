# Module 1 — Project Folder Structure

AI Agent for Auto Loan Securitisation Risk Analytics & Investor Reporting.

```
securitisation_ai/
├── data/
│   ├── raw/            # Source datasets (the four uploaded CSVs — read-only inputs)
│   │   ├── auto_loan_securitisation_data.csv     (500 loans × 58 cols)
│   │   ├── dpd_snapshot_history.csv              (6,000 monthly DPD snapshots × 18 cols)
│   │   ├── dynamic_loss_monthly.csv             (12 months × 20 cols)
│   │   └── static_pool_vintage_data.csv         (375 vintage rows × 16 cols)
│   ├── processed/      # Cleaned + feature-engineered tables written by the pipeline
│   └── exports/        # Final CSV/Excel artifacts
├── models/             # Trained ML models (joblib) + metrics JSON
├── reports/            # Generated Word / PDF / Excel reports
├── plots/              # PNG charts
├── powerbi/            # Power BI-ready refresh tables (CSV)
├── config/
│   ├── __init__.py
│   └── config.py       # Centralised paths, thresholds, constants, logging (Module 4)
├── analytics/          # IFRS9, DPD, vintage, dynamic-loss engines (Modules 8–11)
│   └── __init__.py
├── ml/                 # ML training + explainability (Module 12)
│   └── __init__.py
├── agents/             # Rule-based (LLM-optional) AI agents (Module 13)
│   └── __init__.py
├── utils/              # Shared helpers: data loading, cleaning, logging (Modules 5–6)
│   └── __init__.py
├── docs/               # Technical / user / deployment guides
├── tests/              # Unit tests
├── requirements.txt    # Module 2
├── README.md           # Module 3
└── main.py             # Orchestrator — runs the full pipeline (Module 17)
```

## Design principles
- **`data/raw` is read-only.** Nothing in the pipeline overwrites the source CSVs; every
  stage writes to `data/processed`, `data/exports`, or `powerbi`.
- **Layered architecture.** `utils` (load/clean) → `analytics` (domain engines) →
  `ml` → `agents` → reporting/export. Each layer depends only on the ones beneath it.
- **Config-driven.** All paths, thresholds (DPD buckets, IFRS 9 stage rules, stress
  multipliers) live in `config/config.py`, not hard-coded in modules.
- **Runnable offline.** No module requires an internet connection or API key to run.
  The AI agents default to a deterministic rule-based engine; an LLM backend is an
  optional, configurable add-on.
