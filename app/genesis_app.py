import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# 1. CONFIGURAÇÃO BÁSICA
# =========================
st.set_page_config(
    page_title="Genesis - MVP (Reveal / Predict / Act)",
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

st.title("Genesis – MVP")
st.caption("Módulos REVEAL, PREDICT e ACT integrados em um único app")

# =========================
# 2. GERANDO DADOS SINTÉTICOS ÚNICOS
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

    # Idades 18–90
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

    # Ajuste pela idade (60+)
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

    # Abandono simulado
    df["abandona"] = np.random.binomial(1, df["score_risco"])

    # Etapa de abandono (apenas para quem abandona)
    probs_etapas = np.array([0.10, 0.20, 0.35, 0.25, 0.10])
    etapas_abandono = np.random.choice(etapas, size=n, p=probs_etapas)
    df["etapa_abandono"] = np.where(
        df["abandona"] == 1,
        etapas_abandono,
        "Não abandonou"
    )

    # Faixas de risco
    bins = [0, 0.3, 0.6, 1.0]
    labels = ["Baixo", "Moderado", "Alto"]
    df["faixa_risco"] = pd.cut(df["score_risco"], bins=bins, labels=labels, include_lowest=True)

    # Regras de ação padrão (ACT)
    def definir_acao(row):
        if row["faixa_risco"] == "Alto":
            return "WhatsApp + Ligação do Call Center"
        elif row["faixa_risco"] == "Moderado":
            return "Lembrete WhatsApp"
        else:
            return "Sem ação automática"

    df["acao_sugerida"] = df.apply(definir_acao, axis=1)

    return df, etapas


df, ordem_etapas = gerar_dados_sinteticos()

# =========================
# 3. FILTROS GERAIS (COMUNS A TODAS AS ABAS)
# =========================

with st.sidebar:
    st.header("Filtros gerais")

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

# Aplica filtros em cima do DF base
df_filt = df[
    (df["canal"].isin(canais_sel)) &
    (df["unidade"].isin(unidades_sel)) &
    (df["especialidade"].isin(especialidades_sel)) &
    (df["idade"].between(idade_min, idade_max))
].copy()

total_pacientes = len(df_filt)

st.markdown("---")

# =========================
# 4. TABS: REVEAL / PREDICT / ACT
# =========================

tab_reveal, tab_predict, tab_act = st.tabs(["REVEAL", "PREDICT", "ACT"])

# ============================================================
# TAB 1 - REVEAL
# ============================================================
with tab_reveal:
    st.subheader("Módulo REVEAL – Ponto exato de abandono")

    df_abandono = df_filt[df_filt["abandona"] == 1].copy()

    # KPIs REVEAL
    total_abandono = df_abandono.shape[0]
    taxa_abandono = (total_abandono / total_pacientes * 100) if total_pacientes else 0

    df_60 = df_filt[df_filt["idade"] >= 60]
    taxa_abandono_60 = (
        df_60["abandona"].mean() * 100
        if len(df_60) > 0 else 0
    )

    # Canal mais crítico em abandono
    canal_critico = "-"
    if total_pacientes > 0:
        canal_stats = (
            df_filt.groupby("canal")["abandona"]
            .mean()
            .sort_values(ascending=False)
        )
        if len(canal_stats) > 0:
            canal_critico = f"{canal_stats.index[0]} ({canal_stats.iloc[0]*100:.1f}%)"

    # Etapa mais crítica
    etapa_critica = "-"
    if len(df_abandono) > 0:
        etapa_stats = (
            df_abandono["etapa_abandono"]
            .value_counts(normalize=True)
            .sort_values(ascending=False)
        )
        if len(etapa_stats) > 0:
            etapa_critica = f"{etapa_stats.index[0]} ({etapa_stats.iloc[0]*100:.1f}%)"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Taxa geral de abandono", f"{taxa_abandono:.1f}%")
    col2.metric("Abandono 60+", f"{taxa_abandono_60:.1f}%")
    col3.metric("Canal mais crítico (abandono)", canal_critico)
    col4.metric("Etapa mais crítica", etapa_critica)

    st.markdown("---")

    # Gráfico: Abandono por etapa
    st.markdown("### Abandono por etapa da jornada")

    if len(df_abandono) > 0:
        etapa_counts = (
            df_abandono["etapa_abandono"]
            .value_counts()
            .reindex(ordem_etapas)
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

    # Gráfico: Abandono por canal
    st.markdown("### Taxa de abandono por canal de captação")

    if total_pacientes > 0:
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
        st.info("Nenhum dado disponível para abandono por canal com os filtros atuais.")

    st.markdown("---")

    with st.expander("Ver amostra de registros brutos filtrados (REVEAL)"):
        st.dataframe(df_filt.head(50))


# ============================================================
# TAB 2 - PREDICT
# ============================================================
with tab_predict:
    st.subheader("Módulo PREDICT – Risco de desistência")

    if total_pacientes == 0:
        st.info("Ajuste os filtros para visualizar dados no módulo PREDICT.")
    else:
        risco_medio = df_filt["score_risco"].mean() * 100
        df_60 = df_filt[df_filt["idade"] >= 60]
        risco_medio_60 = df_60["score_risco"].mean() * 100 if len(df_60) > 0 else 0

        perc_alto_risco = (
            df_filt["faixa_risco"].value_counts(normalize=True)
            .get("Alto", 0) * 100
        )

        canal_critico_risco = "-"
        canal_stats = (
            df_filt.groupby("canal")["score_risco"]
            .mean()
            .sort_values(ascending=False)
        )
        if len(canal_stats) > 0:
            canal_critico_risco = f"{canal_stats.index[0]} ({canal_stats.iloc[0]*100:.1f}%)"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Risco médio de desistência", f"{risco_medio:.1f}%")
        col2.metric("Risco médio 60+", f"{risco_medio_60:.1f}%")
        col3.metric("% de pacientes em alto risco", f"{perc_alto_risco:.1f}%")
        col4.metric("Canal com maior risco médio", canal_critico_risco)

        st.markdown("---")

        # Distribuição por faixa de risco
        st.markdown("### Distribuição por faixa de risco")

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

        st.markdown("---")

        # Risco x idade x canal (scatter)
        st.markdown("### Risco por idade e canal")

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

        st.markdown("---")

        st.markdown("### Pacientes em alto risco (amostra)")
        df_alto = df_filt[df_filt["faixa_risco"] == "Alto"].copy()
        df_alto = df_alto.sort_values(by="score_risco", ascending=False)

        st.dataframe(
            df_alto[["id_paciente", "idade", "canal", "unidade", "especialidade", "score_risco"]]
            .head(50)
            .assign(score_risco=lambda x: (x["score_risco"] * 100).round(1))
            .rename(columns={"score_risco": "Risco (%)"})
        )


# ============================================================
# TAB 3 - ACT
# ============================================================
with tab_act:
    st.subheader("Módulo ACT – Tradução de risco em ação")

    if total_pacientes == 0:
        st.info("Ajuste os filtros para visualizar dados no módulo ACT.")
    else:
        acoes_counts = df_filt["acao_sugerida"].value_counts()
        qtd_alto = (df_filt["faixa_risco"] == "Alto").sum()
        qtd_moderado = (df_filt["faixa_risco"] == "Moderado").sum()
        qtd_baixo = (df_filt["faixa_risco"] == "Baixo").sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de pacientes filtrados", f"{total_pacientes}")
        col2.metric("Pacientes em alto risco", f"{qtd_alto}")
        col3.metric("Pacientes em risco moderado", f"{qtd_moderado}")
        col4.metric("Pacientes em baixo risco", f"{qtd_baixo}")

        st.markdown("---")

        st.markdown("### Distribuição de ações sugeridas")

        if len(acoes_counts) > 0:
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

        st.markdown("### Regras de ação atuais")
        st.write("""
- **Alto risco** → WhatsApp + ligação do call center (intervenção ativa e rápida).  
- **Risco moderado** → Lembrete automático via WhatsApp.  
- **Baixo risco** → Sem ação automática (monitoramento passivo).
        """)

        st.markdown("---")

        st.markdown("### Fila de priorização – pacientes com ação ativa (amostra)")

        df_acao = df_filt[df_filt["acao_sugerida"] != "Sem ação automática"].copy()
        df_acao = df_acao.sort_values(by="score_risco", ascending=False)

        st.dataframe(
            df_acao[["id_paciente", "idade", "canal", "unidade", "especialidade",
                     "faixa_risco", "acao_sugerida", "score_risco"]]
            .head(50)
            .assign(score_risco=lambda x: (x["score_risco"] * 100).round(1))
            .rename(columns={"score_risco": "Risco (%)"})
        )


#streamlit run genesis_app.py
