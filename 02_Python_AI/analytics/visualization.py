"""
Optional plots — saves PNG charts to /plots. Uses a non-interactive backend so it runs
headless. Skipped silently if matplotlib is unavailable.
"""
from __future__ import annotations
import pandas as pd
from config.config import get_logger, PLOTS_DIR

log = get_logger("visualization")


def save_all(ifrs9: pd.DataFrame, dpd_dist: pd.DataFrame, dyn: pd.DataFrame,
             loss_curves_df: pd.DataFrame) -> list:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        log.warning("matplotlib unavailable, skipping plots: %s", exc)
        return []
    saved = []

    fig, ax = plt.subplots(figsize=(7, 4))
    d = dpd_dist[dpd_dist["Bucket"] != "Current"]
    ax.bar(d["Bucket"], d["PctOfPool"], color="#0EA5E9")
    ax.set_title("Delinquency distribution (% of pool)"); ax.set_ylabel("% of pool")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    p = PLOTS_DIR / "dpd_distribution.png"; fig.savefig(p, dpi=120); plt.close(fig); saved.append(p.name)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(pd.to_datetime(dyn["ReportingDate"]), dyn["MonthlyNetLossRate"] * 12,
            marker="o", color="#0F172A")
    ax.set_title("Annualised net loss rate"); ax.set_ylabel("rate"); plt.tight_layout()
    p = PLOTS_DIR / "net_loss_trend.png"; fig.savefig(p, dpi=120); plt.close(fig); saved.append(p.name)

    if loss_curves_df is not None and not loss_curves_df.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        for col in loss_curves_df.columns[:8]:
            ax.plot(loss_curves_df.index, loss_curves_df[col], label=str(col))
        ax.set_title("Vintage cumulative net loss curves"); ax.set_xlabel("Months on book")
        ax.legend(fontsize=6); plt.tight_layout()
        p = PLOTS_DIR / "vintage_loss_curves.png"; fig.savefig(p, dpi=120); plt.close(fig); saved.append(p.name)

    log.info("Saved %d plots", len(saved))
    return saved
