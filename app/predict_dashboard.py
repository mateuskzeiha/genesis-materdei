import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# 1. CONFIGURAÇÃO BÁSICA
# =========================
st.set_page_config(
    page_title="Genesis - Dashboard PREDICT",
    layout="wide"
)

# Estilos customizados (cores Genesis)
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
    .stButton > button:hover {
        background-color: #369565;
    }
    [data-testid="stMetricValue"] {
        color: #369565;
        font-weight: 900;
    }
    [data-testid="stMetricLabel"] {
        color: #3ea06d;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Genesis – Protótipo Dashboard PREDICT")
st.caption("Previsão de risco de desistência por paciente e perfil")

# =========================
# 2. GERANDO DADOS SINTÉTICOS
# =========================

@st.cache_data
def gerar_dados_sinteticos(n=3000, random_state=42):
    np.random.seed(random_state)

    canais = ["App", "Site", "WhatsApp", "Call Center"]
    unidades = ["Santo Agostinho", "Betim-Contagem", "Nova Lima", "Goiânia"]
    especialidades = ["Cardiologia", "Oncologia", "Imagem", "Clínica Geral"]

    # Idade simples 18–90
    idades = np.random.randint(18, 90, size=n)

    df = pd.DataFrame({
        "id_paciente": np.arange(1, n + 1),
        "canal": np.random.choice(canais, size=n, p=[0.35, 0.30, 0.20, 0.15]),
        "idade": idades,
        "unidade": np.random.choice(unidades, size=n),
        "especialidade": np.random.choice(
            especialidades,
            size=n,
            p=[0.25, 0.25, 0.30, 0.20]
        ),
    })

    # Probabilidade base de abandono
    prob_base = 0.30

    # Ajuste pelo fator idade (60+)
    ajuste_idade = np.where(df["idade"] >= 60, 0.15, 0.0)

    # Ajuste por canal
    ajuste_canal = df["canal"].map({
        "App": 0.12,
        "Site": 0.08,
        "WhatsApp": 0.05,
        "Call Center": 0.02
    }).fillna(0.0)

    # Score de risco (0–1)
    score_risco = np.clip(prob_base + ajuste_idade + ajuste_canal, 0, 0.95)
    df["score_risco"] = score_risco

    # Simulação de abandono real a partir do score
    df["abandona"] = np.random.binomial(1, df["score_risco"])

    # Faixas de risco
    bins = [0, 0.3, 0.6, 1.0]
    labels = ["Baixo", "Moderado", "Alto"]
    df["faixa_risco"] = pd.cut(df["score_risco"], bins=bins, labels=labels, include_lowest=True)

    return df


df = gerar_dados_sinteticos()

# =========================
# 3. FILTROS (SIDEBAR)
# =========================

with st.sidebar:
    st.header("Filtros")

    canais_sel = st.multiselect(
        "Canal",
        options=sorted(df["canal"].unique()),
        default=sorted(df["canal"].unique())
    )

    unidades_sel = st.multiselect(
        "Unidade",
        options=sorted(df["unidade"].unique()),
        default=sorted(df["unidade"].unique())
    )

    especialidades_sel = st.multiselect(
        "Especialidade",
        options=sorted(df["especialidade"].unique()),
        default=sorted(df["especialidade"].unique())
    )

    idade_min, idade_max = st.slider(
        "Faixa etária",
        min_value=int(df["idade"].min()),
        max_value=int(df["idade"].max()),
        value=(int(df["idade"].min()), int(df["idade"].max()))
    )

# Aplicando filtros
df_filt = df[
    (df["canal"].isin(canais_sel)) &
    (df["unidade"].isin(unidades_sel)) &
    (df["especialidade"].isin(especialidades_sel)) &
    (df["idade"].between(idade_min, idade_max))
].copy()

# =========================
# 4. KPIs PRINCIPAIS
# =========================

total_pacientes = len(df_filt)
risco_medio = (df_filt["score_risco"].mean() * 100) if total_pacientes else 0

df_60 = df_filt[df_filt["idade"] >= 60]
risco_medio_60 = (df_60["score_risco"].mean() * 100) if len(df_60) > 0 else 0

perc_alto_risco = 0
if total_pacientes > 0:
    perc_alto_risco = (df_filt["faixa_risco"].value_counts(normalize=True)
                       .get("Alto", 0) * 100)

# Canal com maior risco médio
canal_critico = "-"
if total_pacientes > 0:
    canal_stats = (
        df_filt.groupby("canal")["score_risco"]
        .mean()
        .sort_values(ascending=False)
    )
    if len(canal_stats) > 0:
        canal_critico = f"{canal_stats.index[0]} ({canal_stats.iloc[0]*100:.1f}%)"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Risco médio de desistência", f"{risco_medio:.1f}%")
col2.metric("Risco médio 60+", f"{risco_medio_60:.1f}%")
col3.metric("% em alto risco", f"{perc_alto_risco:.1f}%")
col4.metric("Canal com maior risco", canal_critico)

st.markdown("---")

# =========================
# 5. DISTRIBUIÇÃO POR FAIXA DE RISCO
# =========================

st.subheader("Distribuição de pacientes por faixa de risco")

if total_pacientes > 0:
    faixa_df = (
        df_filt["faixa_risco"]
        .value_counts()
        .reindex(["Baixo", "Moderado", "Alto"])
        .dropna()
        .reset_index()
    )
    faixa_df.columns = ["Faixa de risco", "Qtde"]

    fig_faixa = px.bar(
        faixa_df,
        x="Faixa de risco",
        y="Qtde",
        text="Qtde",
        title="Quantidade de pacientes por faixa de risco",
        color_discrete_sequence=["#369565"]
    )
    fig_faixa.update_traces(textposition="outside")
    fig_faixa.update_layout(
        xaxis_title="Faixa de risco",
        yaxis_title="Quantidade de pacientes",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )
    st.plotly_chart(fig_faixa, use_container_width=True)
else:
    st.info("Nenhum dado disponível com os filtros atuais.")

st.markdown("---")

# =========================
# 6. RISCO x IDADE (POR CANAL)
# =========================

st.subheader("Risco de desistência por idade e canal")

if total_pacientes > 0:
    fig_scatter = px.scatter(
        df_filt,
        x="idade",
        y="score_risco",
        color="canal",
        labels={"idade": "Idade", "score_risco": "Risco de desistência"},
        title="Distribuição de risco por idade e canal",
        hover_data=["unidade", "especialidade"],
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_scatter.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Nenhum dado disponível para o gráfico de risco por idade.")

st.markdown("---")

# =========================
# 7. TABELA TOP PACIENTES EM ALTO RISCO
# =========================

st.subheader("Pacientes em alto risco (amostra)")

if total_pacientes > 0:
    df_alto = df_filt[df_filt["faixa_risco"] == "Alto"].copy()
    df_alto = df_alto.sort_values(by="score_risco", ascending=False)
    st.dataframe(
        df_alto[["id_paciente", "idade", "canal", "unidade", "especialidade", "score_risco"]]
        .head(50)
        .assign(score_risco=lambda x: (x["score_risco"] * 100).round(1))
        .rename(columns={"score_risco": "Risco (%)"})
    )
else:
    st.info("Nenhum paciente em alto risco com os filtros atuais.")


#streamlit run predict_dashboard.py
