from pathlib import Path
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.linear_model import LogisticRegression

DATA_PATH = Path("data/raw/noshowappointments.csv")
MODEL_PATH = Path("models/model.joblib")


def main():
    print(">>> Iniciando treino baseline")
    print(">>> Lendo CSV:", DATA_PATH)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df = df.rename(columns=lambda x: x.strip())
    print(">>> CSV carregado. Shape:", df.shape)
    print(">>> Colunas:", list(df.columns))

    # Target: 1 = No-show (faltou), 0 = Show (compareceu)
    if "No-show" in df.columns:
        df["target_noshow"] = (df["No-show"].astype(str).str.lower() == "yes").astype(int)
    elif "NoShow" in df.columns:
        df["target_noshow"] = (df["NoShow"].astype(str).str.lower() == "yes").astype(int)
    else:
        raise ValueError("Não encontrei a coluna de target (No-show/NoShow). Verifique o CSV.")

    # Remover IDs
    df = df.drop(columns=["PatientId", "AppointmentID", "AppointmentId"], errors="ignore")

    # Datas -> gerar features e depois REMOVER colunas datetime (correção do seu erro)
    for col in ["ScheduledDay", "AppointmentDay"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "ScheduledDay" in df.columns and "AppointmentDay" in df.columns:
        df["lead_time_hours"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.total_seconds() / 3600.0
        df["sched_dow"] = df["ScheduledDay"].dt.dayofweek
        df["appt_dow"] = df["AppointmentDay"].dt.dayofweek

    # ✅ Correção: remover datas originais para não virar dtype object no hstack do scipy
    df = df.drop(columns=["ScheduledDay", "AppointmentDay"], errors="ignore")

    # Separar X/y
    y = df["target_noshow"]
    X = df.drop(columns=["target_noshow", "No-show", "NoShow"], errors="ignore")

    # Separar colunas categóricas vs numéricas
    cat_cols = [c for c in X.columns if X[c].dtype == "object"]
    num_cols = [c for c in X.columns if c not in cat_cols]

    print(">>> Cat cols:", cat_cols)
    print(">>> Num cols:", num_cols)

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    pipe = Pipeline(steps=[
        ("prep", preprocessor),
        ("model", LogisticRegression(max_iter=1000))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(">>> Treinando...")
    pipe.fit(X_train, y_train)

    print(">>> Avaliando...")
    y_proba = pipe.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_proba)
    print("AUC:", round(auc, 4))
    print(classification_report(y_test, y_pred, digits=4))

    # Salvar modelo
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    print(">>> Modelo salvo em:", MODEL_PATH.resolve())


if __name__ == "__main__":
    main()
