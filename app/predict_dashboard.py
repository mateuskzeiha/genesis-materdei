from pathlib import Path
import pandas as pd
import streamlit as st
import joblib


def project_root() -> Path:
    # app/predict_dashboard.py -> root = .. (pasta do projeto)
    return Path(__file__).resolve().parents[1]


ROOT = project_root()
MODEL_PATH = ROOT / "models" / "model.joblib"


st.set_page_config(page_title="Genesis - Predict", layout="wide")

st.markdown("""
    <style>
    .stButton > button {
        background-color: #3ea06d;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        border: none;
    }
    .stButton > button:hover { background-color: #369565; }
    [data-testid="stMetricValue"] { color: #369565; font-weight: 900; }
    [data-testid="stMetricLabel"] { color: #3ea06d; }
    </style>
""", unsafe_allow_html=True)

st.title("Genesis – Protótipo Dashboard PREDICT")
st.caption("Predição de probabilidade de No-Show com base no modelo treinado (model.joblib)")


@st.cache_resource
def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado em: {path}")
    return joblib.load(path)


model = load_model(MODEL_PATH)


def predict_single(row: dict) -> float:
    df = pd.DataFrame([row])
    proba = model.predict_proba(df)[:, 1][0]
    return float(proba)


# =========================
# 1) PREDIÇÃO UNITÁRIA
# =========================
st.subheader("1) Predição unitária (formulário)")

col1, col2, col3 = st.columns(3)

with col1:
    gender = st.selectbox("Gender", ["F", "M"])
    age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
    neighbourhood = st.text_input("Neighbourhood", value="JARDIM CAMBURI")

with col2:
    scholarship = st.selectbox("Scholarship (0/1)", [0, 1])
    hipertension = st.selectbox("Hipertension (0/1)", [0, 1])
    diabetes = st.selectbox("Diabetes (0/1)", [0, 1])

with col3:
    alcoholism = st.selectbox("Alcoholism (0/1)", [0, 1])
    handcap = st.number_input("Handcap", min_value=0, max_value=4, value=0, step=1)
    sms_received = st.selectbox("SMS_received (0/1)", [0, 1])

st.divider()

col4, col5, col6 = st.columns(3)
with col4:
    lead_time_hours = st.number_input("lead_time_hours", min_value=0.0, value=24.0, step=1.0)
with col5:
    sched_dow = st.number_input("sched_dow (0=Seg ... 6=Dom)", min_value=0, max_value=6, value=0, step=1)
with col6:
    appt_dow = st.number_input("appt_dow (0=Seg ... 6=Dom)", min_value=0, max_value=6, value=1, step=1)

btn = st.button("Prever probabilidade de No-Show")

if btn:
    row = {
        "Gender": gender,
        "Neighbourhood": neighbourhood,
        "Age": float(age),
        "Scholarship": float(scholarship),
        "Hipertension": float(hipertension),
        "Diabetes": float(diabetes),
        "Alcoholism": float(alcoholism),
        "Handcap": float(handcap),
        "SMS_received": float(sms_received),
        "lead_time_hours": float(lead_time_hours),
        "sched_dow": float(sched_dow),
        "appt_dow": float(appt_dow),
    }

    proba = predict_single(row)
    st.metric("Probabilidade de No-Show", f"{proba:.2%}")

    if proba >= 0.50:
        st.warning("Risco alto: recomendável ação preventiva (confirmação ativa, lembrete, WhatsApp, etc.)")
    elif proba >= 0.25:
        st.info("Risco médio: vale reforçar lembrete e confirmação.")
    else:
        st.success("Risco baixo: fluxo padrão deve ser suficiente.")


# =========================
# 2) PREDIÇÃO EM LOTE (CSV)
# =========================
st.divider()
st.subheader("2) Predição em lote (upload CSV)")

st.write("Seu CSV precisa ter as colunas abaixo (iguais ao treino):")
needed = [
    "Gender", "Neighbourhood", "Age", "Scholarship", "Hipertension", "Diabetes",
    "Alcoholism", "Handcap", "SMS_received", "lead_time_hours", "sched_dow", "appt_dow"
]
st.code(", ".join(needed))

file = st.file_uploader("Upload do CSV", type=["csv"])

if file is not None:
    df_in = pd.read_csv(file)
    missing = [c for c in needed if c not in df_in.columns]
    if missing:
        st.error(f"Faltam colunas no CSV: {missing}")
    else:
        proba = model.predict_proba(df_in[needed])[:, 1]
        df_out = df_in.copy()
        df_out["proba_noshow"] = proba
        df_out["pred_noshow_50"] = (df_out["proba_noshow"] >= 0.5).astype(int)

        st.success("Predições geradas.")
        st.dataframe(df_out.head(50), use_container_width=True)

        csv_bytes = df_out.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar CSV com predições",
            data=csv_bytes,
            file_name="predicoes_noshow.csv",
            mime="text/csv"
        )
