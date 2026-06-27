"""
Module 16 — Streamlit web app.  Run:  streamlit run app_streamlit.py
Offline; reads the computed pipeline results live.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from main import run

st.set_page_config(page_title="Securitisation AI", layout="wide")
st.title("Auto Loan Securitisation — Risk Analytics & AI Agent")

@st.cache_data
def _run():
    return run(train_ml=False)

res = _run()
tab = st.sidebar.radio("Page", ["Portfolio", "IFRS9/ECL", "Stress", "AI Chat"])

if tab == "Portfolio":
    st.subheader("IFRS 9 / ECL summary")
    st.dataframe(res["ifrs9"])
    st.metric("NPA / 90+ DPD rate", f"{res['dpd_rates']['npa_default_rate']:.2%}")
elif tab == "IFRS9/ECL":
    st.dataframe(res["ifrs9"])
elif tab == "Stress":
    from analytics.stress_testing import run_scenarios
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    st.dataframe(run_scenarios(clean_loans(load_all()["loans"])))
else:
    from agents.ai_agents import (PortfolioRiskAgent, IFRS9Assistant,
                                  InvestorReportingAgent, PortfolioQAAgent)
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    from analytics.ifrs9_engine import portfolio_ecl_summary, top_ecl_contributors
    loans = clean_loans(load_all()["loans"])
    ifrs9 = portfolio_ecl_summary(loans)
    risk = PortfolioRiskAgent(loans, ifrs9, res["dpd_rates"])
    ifrs_a = IFRS9Assistant(ifrs9, top_ecl_contributors(loans))
    inv = InvestorReportingAgent(ifrs9, res["dyn_metrics"], res["worst_vintage"])
    qa = PortfolioQAAgent(risk, ifrs_a, inv, res["worst_vintage"])
    q = st.text_input("Ask the portfolio agent", "What is today's portfolio health?")
    if q:
        st.write(qa.ask(q))
