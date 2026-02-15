import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

def treinar_modelo_no_show(df: pd.DataFrame):
    base = df[df["agendado"] == 1].copy()
    if len(base) < 500:
        return None

    y = base["faltou"].astype(int)

    features = ["idade", "idade_60_mais", "canal_confirmacao", "bairro", "antecedencia_minutos", "antecedencia_dias"]
    X = base[features].copy()

    cat = ["canal_confirmacao", "bairro"]
    num = ["idade", "idade_60_mais", "antecedencia_minutos", "antecedencia_dias"]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", "passthrough", num),
        ]
    )

    clf = LogisticRegression(max_iter=1000)
    pipe = Pipeline(steps=[("pre", pre), ("clf", clf)])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, proba)

    ohe = pipe.named_steps["pre"].named_transformers_["cat"]
    cat_names = ohe.get_feature_names_out(cat).tolist()
    feature_names = cat_names + num

    coefs = pipe.named_steps["clf"].coef_[0]
    fi = pd.DataFrame({
        "feature": feature_names,
        "importance": np.abs(coefs[:len(feature_names)]),
    }).sort_values("importance", ascending=False).head(15)

    return {
        "pipeline": pipe,
        "auc": float(auc),
        "n_train": int(len(base)),
        "feature_importance": fi,
        "features": features,
    }

def pontuar_risco_no_show(df: pd.DataFrame, model_pack: dict):
    if model_pack is None:
        return None

    pipe = model_pack["pipeline"]
    features = model_pack["features"]

    base = df[df["agendado"] == 1].copy()
    if len(base) == 0:
        return None

    X = base[features].copy()
    base["risco_no_show"] = pipe.predict_proba(X)[:, 1]
    return base
