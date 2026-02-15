import os
import streamlit as st

from utils.styling import apply_global_style
from utils.data_loader import load_data
from app.pages_exec import render_exec_overview
from app.pages_reveal import render_reveal
from app.pages_predict import render_predict
from app.pages_act import render_act


LOGO_PATH = os.path.join("assets", "genesis_logo.png")

st.set_page_config(
    page_title="Genesis | No-show & Eficiência de Agenda",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ✅ agora não passa mais logo_path
apply_global_style()

st.sidebar.header("Filtros")

# Logo na sidebar (se existir)
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)

df = load_data()

min_date = df["data_agendamento"].min()
max_date = df["data_agendamento"].max()

date_range = st.sidebar.date_input(
    "Período (data do agendamento)",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

canais = ["Todos"] + sorted(df["canal_confirmacao"].unique().tolist())
bairros = ["Todos"] + sorted(df["bairro"].unique().tolist())

canal = st.sidebar.selectbox("Canal de confirmação", canais, index=0)
bairro = st.sidebar.selectbox("Bairro", bairros, index=0)

dff = df.copy()
dff = dff[(dff["data_agendamento"] >= start_date) & (dff["data_agendamento"] <= end_date)]

if canal != "Todos":
    dff = dff[dff["canal_confirmacao"] == canal]
if bairro != "Todos":
    dff = dff[dff["bairro"] == bairro]

tab1, tab2, tab3, tab4 = st.tabs(["Executive Overview", "Reveal", "Predict", "Act"])

with tab1:
    render_exec_overview(dff)

with tab2:
    render_reveal(dff)

with tab3:
    render_predict(dff)

with tab4:
    render_act(dff)
