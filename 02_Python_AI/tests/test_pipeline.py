"""Smoke tests — verify the pipeline computes and ECL reconciles on the real data."""
from utils.data_loader import load_all
from utils.data_cleaner import clean_all
from analytics.ifrs9_engine import portfolio_ecl_summary


def test_datasets_load():
    data = load_all()
    assert set(data) == {"loans", "dpd", "dynamic", "vintage"}
    assert len(data["loans"]) == 500


def test_ecl_reconciles():
    loans = clean_all(load_all())["loans"]
    s = portfolio_ecl_summary(loans)
    variance = abs(s.iloc[-1]["Variance"])
    assert variance < 1.0, f"ECL variance too large: {variance}"
