"""
Module 12 — Machine learning (default-risk classification).

IMPORTANT — SMALL-SAMPLE WARNING:
The loan tape contains 500 loans with only ~9 defaults. This is far below the volume
needed to train a reliable credit model. Models here are trained with stratified
cross-validation and reported honestly, but metrics are ILLUSTRATIVE / proof-of-concept
only and MUST NOT be used as a production default model. The runtime prints this warning.
"""
from __future__ import annotations
import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from config.config import get_logger, ML, MODELS_DIR

log = get_logger("ml_models")
warnings.filterwarnings("ignore")

FEATURES = ["LTV_Current", "DTI_Ratio", "CIBIL_Score_Current", "InterestRate",
            "MonthsOnBook", "RemainingTerm", "DelinquencyDays", "PD_Estimate",
            "LGD_Estimate", "BorrowerAge"]


def _prepare(loans: pd.DataFrame):
    df = loans.copy()
    X = df[FEATURES].fillna(df[FEATURES].median())
    y = df[ML["target_default"]].astype(int)
    return X, y


def train_models(loans: pd.DataFrame) -> dict:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.metrics import (roc_auc_score, precision_score, recall_score,
                                 f1_score, confusion_matrix)
    import joblib

    X, y = _prepare(loans)
    n_pos = int(y.sum())
    reliable = n_pos >= ML["min_positives_for_reliable_ml"]
    if not reliable:
        log.warning("ONLY %d positive (default) cases — ML metrics are ILLUSTRATIVE "
                    "ONLY, not a production model.", n_pos)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                               random_state=ML["random_state"]),
    }
    # optional gradient boosters if installed
    try:
        from xgboost import XGBClassifier
        spw = (len(y) - n_pos) / max(n_pos, 1)
        models["XGBoost"] = XGBClassifier(n_estimators=200, scale_pos_weight=spw,
                                          eval_metric="logloss", random_state=ML["random_state"])
    except Exception:
        log.info("xgboost not available — skipping")

    cv = StratifiedKFold(n_splits=min(ML["cv_folds"], n_pos), shuffle=True,
                         random_state=ML["random_state"])
    results = {"n_positives": n_pos, "reliable": reliable, "models": {}}
    for name, model in models.items():
        try:
            proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
            pred = (proba >= 0.5).astype(int)
            results["models"][name] = {
                "roc_auc": float(roc_auc_score(y, proba)) if y.nunique() > 1 else None,
                "precision": float(precision_score(y, pred, zero_division=0)),
                "recall": float(recall_score(y, pred, zero_division=0)),
                "f1": float(f1_score(y, pred, zero_division=0)),
                "confusion_matrix": confusion_matrix(y, pred).tolist(),
            }
            model.fit(X, y)
            joblib.dump(model, MODELS_DIR / f"{name}.joblib")
            log.info("%s trained | ROC-AUC=%s", name, results["models"][name]["roc_auc"])
        except Exception as exc:  # noqa: BLE001
            log.error("%s failed: %s", name, exc)
    # feature importance from RF
    try:
        rf = models["RandomForest"]
        fi = sorted(zip(FEATURES, rf.feature_importances_), key=lambda t: -t[1])
        results["feature_importance"] = [{"feature": f, "importance": float(i)} for f, i in fi]
    except Exception:
        pass
    (MODELS_DIR / "ml_metrics.json").write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    from utils.data_loader import load_all
    from utils.data_cleaner import clean_loans
    r = train_models(clean_loans(load_all()["loans"]))
    print(json.dumps(r["models"], indent=2))
