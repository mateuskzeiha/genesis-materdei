import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score

# Texto explicativo fixo — responde diretamente ao feedback do professor
AUC_EXPLANATION_TEMPLATE = (
    "AUC {auc:.2f} significa que o modelo acerta a ordem de risco entre dois pacientes "
    "aleatórios {pct:.0f}% das vezes. Isso permite priorizar intervenções mesmo sem "
    "prever com certeza absoluta — a utilidade está em ordenar quem acionar primeiro, "
    "não em prever o resultado de cada consulta individualmente."
)


def treinar_modelo_no_show(df: pd.DataFrame):
    base = df[df["agendado"] == 1].copy()
    if len(base) < 500:
        return None

    y = base["faltou"].astype(int)

    # Features base + novas (hora, dia_semana, historico_no_show se disponíveis)
    features_base = ["idade", "idade_60_mais", "canal_confirmacao", "bairro",
                     "antecedencia_minutos", "antecedencia_dias"]
    features_extras = ["hora_agendamento", "dia_semana", "historico_no_show"]
    features = features_base + [f for f in features_extras if f in base.columns]

    X = base[features].copy()

    cat = ["canal_confirmacao", "bairro"]
    num = [f for f in features if f not in cat]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
            ("num", "passthrough", num),
        ]
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    pipe = Pipeline(steps=[("pre", pre), ("clf", clf)])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_val)[:, 1]
    pred = pipe.predict(X_val)

    auc = float(roc_auc_score(y_val, proba))
    f1 = float(f1_score(y_val, pred, pos_label=1, zero_division=0))
    precision = float(precision_score(y_val, pred, pos_label=1, zero_division=0))
    recall = float(recall_score(y_val, pred, pos_label=1, zero_division=0))

    ohe = pipe.named_steps["pre"].named_transformers_["cat"]
    cat_names = ohe.get_feature_names_out(cat).tolist()
    feature_names = cat_names + num

    importances = pipe.named_steps["clf"].feature_importances_
    fi = pd.DataFrame({
        "feature": feature_names[:len(importances)],
        "importance": importances[:len(feature_names)],
    }).sort_values("importance", ascending=False).head(15)

    return {
        "pipeline": pipe,
        "auc": auc,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "n_train": int(len(base)),
        "feature_importance": fi,
        "features": features,
        "auc_explanation": AUC_EXPLANATION_TEMPLATE.format(auc=auc, pct=auc * 100),
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
