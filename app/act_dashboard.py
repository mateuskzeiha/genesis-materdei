import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# 1. CONFIGURAÇÃO BÁSICA
# =========================
st.set_page_config(
    page_title="Genesis - Dashboard ACT",
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

st.title("Genesis – Protótipo Dashboard ACT")
st.caption("Tradução de risco em ações práticas (nudges e priorização)")

# =========================
# 2. GERANDO DADOS SINTÉTICOS
# =========================

@st.cache_data
def gerar_dados_sinteticos(n=3000, random_state=42):
    np.random.seed(random_state)

    canais = ["App", "Site", "WhatsApp", "Call Center"]
    unidades = ["Santo Agostinho", "Betim-Contagem", "Nova Lima", "Goiânia"]
    especialidades = ["Cardiologia", "Oncologia", "Imagem", "Clínica Geral"]

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

    prob_base = 0.30
    ajuste_idade = np.where(df["idade"] >= 60, 0.15, 0.0)
    ajuste_canal = df["canal"].map({
        "App": 0.12,
        "Site": 0.08,
        "WhatsApp": 0.05,
        "Call Center": 0.02
    }).fillna(0.0)

    score_risco = np.clip(prob_base + ajuste_idade + ajuste_canal, 0, 0.95)
    df["score_risco"] = score_risco

    bins = [0, 0.3, 0.6, 1.0]
    labels = ["Baixo", "Moderado", "Alto"]
    df["faixa_risco"] = pd.cut(df["score_risco"], bins=bins, labels=labels, include_lowest=True)

    # Regras de ação padrão
    def definir_acao(row):
        if row["faixa_risco"] == "Alto":
            return "WhatsApp + Ligação do Call Center"
        elif row["faixa_risco"] == "Moderado":
            return "Lembrete WhatsApp"
        else:
            return "Sem ação automática"

    df["acao_sugerida"] = df.apply(definir_acao, axis=1)

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
# 4. KPIs PRINCIPAIS (AÇÕES)
# =========================

total_pacientes = len(df_filt)

acoes_counts = df_filt["acao_sugerida"].value_counts() if total_pacientes > 0 else pd.Series(dtype=int)
qtd_alto = (df_filt["faixa_risco"] == "Alto").sum() if total_pacientes > 0 else 0
qtd_moderado = (df_filt["faixa_risco"] == "Moderado").sum() if total_pacientes > 0 else 0
qtd_baixo = (df_filt["faixa_risco"] == "Baixo").sum() if total_pacientes > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de pacientes filtrados", f"{total_pacientes}")
col2.metric("Pacientes em alto risco", f"{qtd_alto}")
col3.metric("Pacientes em risco moderado", f"{qtd_moderado}")
col4.metric("Pacientes em baixo risco", f"{qtd_baixo}")

st.markdown("---")

# =========================
# 5. AÇÕES SUGERIDAS (VISÃO GERAL)
# =========================

st.subheader("Distribuição de ações sugeridas")

if total_pacientes > 0 and len(acoes_counts) > 0:
    acoes_df = acoes_counts.reset_index()
    acoes_df.columns = ["Ação sugerida", "Qtde"]

    fig_acoes = px.bar(
        acoes_df,
        x="Ação sugerida",
        y="Qtde",
        text="Qtde",
        title="Quantidade de pacientes por tipo de ação sugerida",
        color_discrete_sequence=["#369565"]
    )
    fig_acoes.update_traces(textposition="outside")
    fig_acoes.update_layout(
        xaxis_title="Ação sugerida",
        yaxis_title="Quantidade de pacientes",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )
    st.plotly_chart(fig_acoes, use_container_width=True)
else:
    st.info("Nenhuma ação sugerida com os filtros atuais.")

st.markdown("---")

# =========================
# 6. REGRA DE AÇÃO (EXPLICAÇÃO)
# =========================

st.subheader("Regras de ação atuais")

st.write("""
- **Alto risco** → WhatsApp + ligação do call center (intervenção ativa e rápida).  
- **Risco moderado** → Lembrete automático via WhatsApp.  
- **Baixo risco** → Sem ação automática (monitoramento passivo).
""")

st.markdown("---")

# =========================
# 7. LISTA DE PRIORIZAÇÃO (TOP PACIENTES COM AÇÃO)
# =========================

st.subheader("Fila de priorização – pacientes com ação ativa (amostra)")

if total_pacientes > 0:
    df_acao = df_filt[df_filt["acao_sugerida"] != "Sem ação automática"].copy()
    df_acao = df_acao.sort_values(by="score_risco", ascending=False)

    st.dataframe(
        df_acao[["id_paciente", "idade", "canal", "unidade", "especialidade",
                 "faixa_risco", "acao_sugerida", "score_risco"]]
        .head(50)
        .assign(score_risco=lambda x: (x["score_risco"] * 100).round(1))
        .rename(columns={"score_risco": "Risco (%)"})
    )
else:
    st.info("Nenhum paciente com ação ativa nos filtros atuais.")


#streamlit run act_dashboard.py
