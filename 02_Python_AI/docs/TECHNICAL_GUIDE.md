# Technical Guide

## Module map
| Module | File | Role |
|---|---|---|
| 1 | docs/01_folder_structure.md | Folder scaffold |
| 2 | requirements.txt | Dependencies |
| 3 | README.md | Overview |
| 4 | config/config.py | Paths, thresholds, IFRS9/DPD rules, stress scenarios, logging |
| 5 | utils/data_loader.py | Load + validate the 4 datasets |
| 6 | utils/data_cleaner.py | Missing/dtype/outlier handling |
| 7 | analytics/feature_engineering.py | Business features |
| 8 | analytics/ifrs9_engine.py | IFRS 9 ECL, staging, migration, top contributors |
| 9 | analytics/dpd_engine.py | DPD buckets, roll/transition, cure/default rates |
| 10 | analytics/vintage_engine.py | Static-pool loss & pool-factor curves |
| 11 | analytics/dynamic_loss_engine.py | Monthly trends + waterfall |
| 11b | analytics/stress_testing.py | Scenario ECL |
| 12 | ml/ml_models.py | Default classifiers (small-sample honest) |
| 13 | agents/ai_agents.py | Rule-based AI agents (LLM-optional) |
| 14 | analytics/powerbi_export.py | CSV + Excel export |
| 15 | analytics/report_generator.py | Word + Excel reports |
| 16 | app_streamlit.py | Web app |
| 17 | main.py | Orchestrator |

## Data lineage
data/raw (read-only) -> clean_all -> engineer_loan_features -> domain engines ->
powerbi/*.csv + reports/*. ECL recompute validated against ECL_Provision (variance < ₹1).

## Key validated results (this dataset)
- Portfolio ECL: ₹1,16,62,953 (model) vs recompute ₹1,16,62,952.85 → variance ₹0.045
- Pool factor 0.582 | WAC 10.95% | W.Avg LTV 67.5% | NPA/90+ rate ~5.8%
- Worst vintage: 2021-Q2 (cum net loss rate 1.67%)

## Extending
Add a new metric: write a function in the relevant analytics module, add it to the
`pbi_tables` dict in main.py to export it, and (optionally) a sheet in report_generator.
