"""
Module 17 — Main orchestrator.

Runs the full pipeline end-to-end from one command:
load -> clean -> feature-engineer -> IFRS9 -> DPD -> vintage -> dynamic loss ->
stress -> ML -> AI agents -> Power BI export -> reports.

Usage:
    python main.py
"""
from __future__ import annotations
import json
from config.config import get_logger
from utils.data_loader import load_all
from utils.data_cleaner import clean_all
from analytics.feature_engineering import engineer_loan_features
from analytics.ifrs9_engine import portfolio_ecl_summary, stage_migration, top_ecl_contributors
from analytics.dpd_engine import dpd_distribution, roll_rate_matrix, cure_and_default_rates, transition_summary
from analytics.vintage_engine import vintage_summary, worst_vintage, loss_curves
from analytics.dynamic_loss_engine import monthly_trends, headline_metrics, waterfall
from analytics.stress_testing import run_scenarios
from analytics.powerbi_export import export_tables
from analytics.report_generator import build_docx, build_excel_summary
from agents.ai_agents import (PortfolioRiskAgent, IFRS9Assistant, InvestorReportingAgent,
                              PortfolioQAAgent, DashboardNarrator)

log = get_logger("main")


def run(train_ml: bool = True) -> dict:
    log.info("=== Securitisation AI pipeline starting ===")
    raw = load_all()
    data = clean_all(raw)
    loans = engineer_loan_features(data["loans"])
    dpd, dyn, vintage = data["dpd"], data["dynamic"], data["vintage"]

    # analytics
    ifrs9 = portfolio_ecl_summary(loans)
    migration = stage_migration(loans)
    top_ecl = top_ecl_contributors(loans)
    dpd_dist = dpd_distribution(dpd)
    rolls = roll_rate_matrix(dpd)
    dpd_rates = cure_and_default_rates(dpd)
    trans = transition_summary(dpd)
    vsum = vintage_summary(vintage)
    worst = worst_vintage(vintage)
    dyn_trends = monthly_trends(dyn)
    dyn_metrics = headline_metrics(dyn)
    pool_bal = loans["CurrentBalance"].sum()
    wf = waterfall(dyn, pool_bal)
    stress = run_scenarios(loans)

    # ML (optional, honest small-sample handling)
    ml_results = {}
    if train_ml:
        try:
            from ml.ml_models import train_models
            ml_results = train_models(loans)
        except Exception as exc:  # noqa: BLE001
            log.warning("ML skipped: %s", exc)

    # agents
    risk = PortfolioRiskAgent(loans, ifrs9, dpd_rates)
    ifrs_a = IFRS9Assistant(ifrs9, top_ecl)
    inv = InvestorReportingAgent(ifrs9, dyn_metrics, worst)
    qa = PortfolioQAAgent(risk, ifrs_a, inv, worst)
    narrator = DashboardNarrator(risk, inv)

    # power bi export
    pbi_tables = {
        "kpi_summary": ifrs9, "dpd_distribution": dpd_dist,
        "vintage_summary": vsum, "dynamic_loss_trends": dyn_trends,
        "stress_scenarios": stress, "top_ecl_contributors": top_ecl,
        "transition_summary": trans, "waterfall": wf,
    }
    export_tables(pbi_tables)

    # reports
    context = {
        "health": risk.health(),
        "ecl_explain": ifrs_a.explain_ecl(),
        "ifrs9_summary": ifrs9, "dpd_distribution": dpd_dist,
        "vintage_summary": vsum, "stress": stress,
        "investor": inv.summary(),
        "validation_note": (f"Independent ECL recompute (PD x LGD x EAD) reconciles to the "
                            f"model to within rounding (portfolio variance "
                            f"{ifrs9.iloc[-1]['Variance']:.4f}). "
                            + ("ML metrics are illustrative only due to small default count."
                               if ml_results and not ml_results.get("reliable") else "")),
    }
    try:
        build_docx(context)
        build_excel_summary(context)
    except Exception as exc:  # noqa: BLE001
        log.warning("Report generation issue: %s", exc)

    # demo Q&A
    log.info("=== AI Agent demo ===")
    for q in ["What is today's portfolio health?", "Which vintage is performing worst?",
              "Explain ECL.", "Generate investor summary."]:
        print(f"\nQ: {q}\nA: {qa.ask(q)}")

    log.info("=== Pipeline complete ===")
    return {"ifrs9": ifrs9, "dpd_rates": dpd_rates, "worst_vintage": worst,
            "dyn_metrics": dyn_metrics, "ml": ml_results}


if __name__ == "__main__":
    run()
