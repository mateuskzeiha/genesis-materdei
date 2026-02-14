import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# 1. CONFIGURAÇÃO BÁSICA
# =========================
st.set_page_config(
    page_title="Genesis - Dashboard Reveal",
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

st.title("Genesis – Protótipo Dashboard REVEAL")
st.caption("Identificação do ponto exato de abandono na jornada de agendamento")

# =========================
# 2. GERANDO DADOS SINTÉTICOS
# =========================

@st.cache_data
def gerar_dados_sinteticos(n=3000, random_state=42):
    np.random.seed(random_state)

    canais = ["App", "Site", "WhatsApp", "Call Center"]
    unidades = ["Santo Agostinho", "Betim-Contagem", "Nova Lima", "Goiânia"]
    especialidades = ["Cardiologia", "Oncologia", "Imagem", "Clínica Geral"]
    etapas = [
        "Interesse",
        "Início do Agendamento",
        "Cadastro",
        "Escolha de Horário/Unidade",
        "Confirmação"
    ]

    # Distribuição simples de idades entre 18 e 90 anos
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

    # Ajustes pela idade (60+ abandona mais)
    ajuste_idade = np.where(df["idade"] >= 60, 0.15, 0.0)

    # Ajustes por canal (mais fricção no App / Site)
    ajuste_canal = df["canal"].map({
        "App": 0.12,
        "Site": 0.08,
        "WhatsApp": 0.05,
        "Call Center": 0.02
    }).fillna(0.0)

    prob_abandono = np.clip(prob_base + ajuste_idade + ajuste_canal, 0, 0.95)
    df["abandona"] = np.random.binomial(1, prob_abandono)

    # Para quem abandona, sortear etapa de abandono (peso maior em Cadastro)
    probs_etapas = np.array([0.10, 0.20, 0.35, 0.25, 0.10])
    df["etapa_abandono"] = np.where(
        df["abandona"] == 1,
        np.random.choice(etapas, size=n, p=probs_etapas),
        "Não abandonou"
    )

    return df, etapas


# Gera os dados ANTES de usar df nos filtros
df, ordem_etapas = gerar_dados_sinteticos()

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
total_abandono = df_filt["abandona"].sum()
taxa_abandono = (total_abandono / total_pacientes * 100) if total_pacientes else 0

df_60 = df_filt[df_filt["idade"] >= 60]
taxa_abandono_60 = (df_60["abandona"].mean() * 100) if len(df_60) > 0 else 0

# Canal mais crítico (maior taxa de abandono)
canal_critico = "-"
if total_pacientes > 0:
    canal_stats = (
        df_filt.groupby("canal")["abandona"]
        .mean()
        .sort_values(ascending=False)
    )
    if len(canal_stats) > 0:
        canal_critico = f"{canal_stats.index[0]} ({canal_stats.iloc[0]*100:.1f}%)"

# Etapa mais crítica (apenas quem abandona)
df_abandono = df_filt[df_filt["abandona"] == 1].copy()
etapa_critica = "-"
if len(df_abandono) > 0:
    etapa_stats = (
        df_abandono["etapa_abandono"]
        .value_counts(normalize=True)
        .sort_values(ascending=False)
    )
    if len(etapa_stats) > 0:
        etapa_critica = f"{etapa_stats.index[0]} ({etapa_stats.iloc[0]*100:.1f}%)"

# Cards de KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("Taxa geral de abandono", f"{taxa_abandono:.1f}%")
col2.metric("Abandono 60+", f"{taxa_abandono_60:.1f}%")
col3.metric("Canal mais crítico", canal_critico)
col4.metric("Etapa mais crítica", etapa_critica)

st.markdown("---")

# =========================
# 5. GRÁFICO – ABANDONO POR ETAPA (REVEAL)
# =========================

st.subheader("Ponto de abandono por etapa da jornada")

if len(df_abandono) > 0:
    etapa_counts = (
        df_abandono["etapa_abandono"]
        .value_counts()
        .reindex(ordem_etapas)  # mantém ordem lógica
        .dropna()
    )
    etapa_df = etapa_counts.reset_index()
    etapa_df.columns = ["Etapa", "Qtde"]

    fig_etapas = px.bar(
        etapa_df,
        x="Etapa",
        y="Qtde",
        text="Qtde",
        title="Abandono por etapa da jornada",
        color_discrete_sequence=["#369565"]
    )
    fig_etapas.update_traces(textposition="outside")
    fig_etapas.update_layout(
        xaxis_title="Etapa da Jornada",
        yaxis_title="Quantidade de pacientes que abandonaram",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )
    st.plotly_chart(fig_etapas, use_container_width=True)
else:
    st.info("Nenhum abandono encontrado com os filtros atuais para exibir por etapa.")

st.markdown("---")

# =========================
# 6. GRÁFICO – ABANDONO POR CANAL
# =========================

st.subheader("Abandono por canal de captação")

if len(df_filt) > 0:
    canal_df = (
        df_filt.groupby("canal")["abandona"]
        .mean()
        .reset_index()
    )
    canal_df["taxa_abandono"] = canal_df["abandona"] * 100

    fig_canal = px.bar(
        canal_df,
        x="canal",
        y="taxa_abandono",
        text="taxa_abandono",
        labels={"canal": "Canal", "taxa_abandono": "Taxa de abandono (%)"},
        title="Taxa de abandono por canal",
        color_discrete_sequence=["#369565"]
    )
    fig_canal.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_canal.update_layout(
        yaxis_range=[0, max(5, canal_df["taxa_abandono"].max() * 1.2)]
    )
    st.plotly_chart(fig_canal, use_container_width=True)
else:
    st.info("Nenhum dado disponível para exibir abandono por canal com os filtros atuais.")

# =========================
# 7. TABELA DETALHADA (OPCIONAL)
# =========================

with st.expander("Ver amostra de registros brutos filtrados"):
    st.dataframe(df_filt.head(50))


#streamlit run reveal_dashboard.py
