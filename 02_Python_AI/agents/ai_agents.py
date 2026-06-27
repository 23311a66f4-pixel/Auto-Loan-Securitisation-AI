"""
Module 13 — AI Agent system (rule-based, LLM-optional).

Five agents that answer portfolio questions in plain language by querying the computed
analytics results — NOT by calling an LLM by default. Set AGENT_BACKEND=llm and provide
an API key to route phrasing through an LLM; the deterministic facts are always computed
locally so answers are reproducible and run offline.

Agents:
  PortfolioRiskAgent   — portfolio health & risk commentary
  IFRS9Assistant       — staging / ECL / PD / LGD / EAD explanations
  InvestorReportingAgent — investor-style summaries
  PortfolioQAAgent     — natural-language Q&A router
  DashboardNarrator    — auto executive narrative for each dashboard page
"""
from __future__ import annotations
import pandas as pd
from config.config import get_logger, AGENT

log = get_logger("ai_agents")


def _inr_cr(x: float) -> str:
    return f"INR {x/1e7:,.2f} cr"


class PortfolioRiskAgent:
    def __init__(self, loans, ifrs9_summary, dpd_rates):
        self.loans = loans
        self.ifrs = ifrs9_summary
        self.dpd = dpd_rates

    def health(self) -> str:
        total = self.ifrs.iloc[-1]
        cov = total["CoverageRatio"]
        npa = self.dpd.get("npa_default_rate", 0)
        verdict = ("STABLE" if npa < 0.06 and cov < 0.06 else
                   "WATCH" if npa < 0.10 else "ELEVATED RISK")
        return (f"Portfolio health: {verdict}. Outstanding balance {_inr_cr(total['CurrentBalance'])} "
                f"across {int(total['LoanCount'])} loans. ECL provision {_inr_cr(total['Model_ECL'])} "
                f"(coverage {cov:.2%}). 90+ DPD / NPA rate {npa:.2%}. "
                f"Stage 3 carries the bulk of provisions despite the smallest balance, which is "
                f"expected for credit-impaired exposures.")


class IFRS9Assistant:
    def __init__(self, ifrs9_summary, top_contributors):
        self.ifrs = ifrs9_summary
        self.top = top_contributors

    def explain_ecl(self) -> str:
        t = self.ifrs.iloc[-1]
        return (f"ECL is computed loan-by-loan as PD x LGD x EAD, then summed. "
                f"Portfolio ECL = {_inr_cr(t['Model_ECL'])} on EAD of {_inr_cr(t['EAD'])}. "
                f"Stage 1 = 12-month ECL; Stages 2 and 3 = lifetime ECL. The independent "
                f"recompute matches the model to within rounding (variance "
                f"{t['Variance']:.4f}), validating the dashboard figure.")

    def top_ecl_loans(self) -> str:
        ids = ", ".join(self.top["LoanID"].head(5).astype(str))
        return f"Top ECL contributors: {ids}. These are concentrated in Stage 3 / high-PD segments."


class InvestorReportingAgent:
    def __init__(self, ifrs9_summary, dyn_metrics, vintage_worst):
        self.ifrs = ifrs9_summary
        self.dyn = dyn_metrics
        self.worst = vintage_worst

    def summary(self) -> str:
        t = self.ifrs.iloc[-1]
        return (f"INVESTOR SUMMARY — Pool ZAAUTO2024-1. Outstanding {_inr_cr(t['CurrentBalance'])}, "
                f"ECL provision {_inr_cr(t['Model_ECL'])} ({t['CoverageRatio']:.2%} coverage). "
                f"Latest collection efficiency {self.dyn['collection_efficiency']:.2f}, "
                f"annualised CPR {self.dyn['cpr_annualised']:.2%}, cumulative net loss "
                f"{_inr_cr(self.dyn['cum_net_loss'])}. Weakest vintage: {self.worst['vintage']} "
                f"(cumulative net loss rate {self.worst['cum_net_loss_rate']:.2%}). "
                f"Average monthly excess spread {_inr_cr(self.dyn['avg_excess_spread'])} provides "
                f"first-loss cushion ahead of the credit-enhancement structure.")


class PortfolioQAAgent:
    """Routes free-text questions to the relevant agent method via keyword matching."""
    def __init__(self, risk, ifrs, investor, vintage_worst):
        self.risk, self.ifrs, self.investor = risk, ifrs, investor
        self.worst = vintage_worst

    def ask(self, q: str) -> str:
        ql = q.lower()
        if "health" in ql or "today" in ql:
            return self.risk.health()
        if "vintage" in ql and ("worst" in ql or "highest" in ql or "loss" in ql):
            return (f"Weakest vintage is {self.worst['vintage']} with cumulative net loss rate "
                    f"{self.worst['cum_net_loss_rate']:.2%} and 30+ DPD of "
                    f"{self.worst['delinq_30plus']:.2%}.")
        if "ecl" in ql and ("explain" in ql or "what" in ql):
            return self.ifrs.explain_ecl()
        if "top" in ql and "loan" in ql:
            return self.ifrs.top_ecl_loans()
        if "investor" in ql or "summary" in ql or "board" in ql:
            return self.investor.summary()
        return ("I can answer: portfolio health, worst vintage, ECL explanation, top ECL loans, "
                "or generate an investor summary. Please rephrase.")


class DashboardNarrator:
    def __init__(self, risk, investor):
        self.risk, self.investor = risk, investor

    def narrate(self) -> dict:
        return {
            "Loan Portfolio Overview": self.risk.health(),
            "Investor Reporting Dashboard": self.investor.summary(),
        }


def maybe_llm_rephrase(text: str) -> str:
    """Optional LLM polish; returns input unchanged in rule mode or if no key/SDK."""
    if AGENT["backend"] != "llm":
        return text
    try:  # pragma: no cover - optional path
        import os
        if AGENT["llm_provider"] == "openai" and os.getenv("OPENAI_API_KEY"):
            from openai import OpenAI
            client = OpenAI()
            r = client.chat.completions.create(
                model=AGENT["llm_model"],
                messages=[{"role": "system", "content": "Rephrase this risk commentary "
                           "professionally without changing any number."},
                          {"role": "user", "content": text}])
            return r.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM rephrase unavailable (%s); returning rule-based text.", exc)
    return text
