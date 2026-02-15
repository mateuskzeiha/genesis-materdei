import streamlit as st
import plotly.express as px

from utils.kpis import no_show_por, impacto_antecedencia, comparecimento_por

def render_reveal(df):
    st.subheader("Reveal — Diagnóstico")

    st.caption("Aqui a pergunta é: onde está o no-show e quais padrões explicam o problema.")

    a, b = st.columns(2)

    with a:
        st.markdown("### No-show por canal de confirmação")
        st.caption(
            "Métrica: **No-show (%)**. "
            "Canal de confirmação aqui é **SMS vs Sem SMS** (proxy do Kaggle)."
        )
        ns = no_show_por(df, "canal_confirmacao")
        fig = px.bar(
            ns,
            x="canal_confirmacao",
            y="taxa_no_show",
            text="taxa_no_show",
            labels={
                "canal_confirmacao": "Canal de confirmação",
                "taxa_no_show": "No-show (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1%}",
            textposition="outside",
            hovertemplate="Canal: %{x}<br>No-show: %{y:.1%}<extra></extra>",
        )
        fig.update_layout(height=330, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    with b:
        st.markdown("### No-show por bairro (Top 12)")
        st.caption(
            "Métrica: **No-show (%)**. "
            "O que olhar: bairros com maior taxa e maior volume para priorização operacional."
        )
        ns_b = no_show_por(df, "bairro").head(12)
        fig = px.bar(
            ns_b,
            x="bairro",
            y="taxa_no_show",
            text="taxa_no_show",
            labels={
                "bairro": "Bairro",
                "taxa_no_show": "No-show (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1%}",
            textposition="outside",
            hovertemplate="Bairro: %{x}<br>No-show: %{y:.1%}<extra></extra>",
        )
        fig.update_layout(height=330, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Antecedência (dias) x No-show")
        st.caption(
            "Definição: **Antecedência (dias) = data da consulta − data do agendamento**. "
            "Métrica: **No-show (%)**. "
            "O que olhar: se marcar com muita antecedência aumenta o risco de falta."
        )
        da = impacto_antecedencia(df)

        fig = px.line(
            da,
            x="faixa_antecedencia",
            y="taxa_no_show",
            markers=True,
            labels={
                "faixa_antecedencia": "Antecedência (dias)",
                "taxa_no_show": "No-show (%)",
            },
        )
        fig.update_traces(
            hovertemplate="Antecedência: %{x} dias<br>No-show: %{y:.1%}<extra></extra>"
        )
        fig.update_layout(height=330, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "Se o no-show subir nas faixas **15–30** e **30+ dias**, isso sugere ação simples: "
            "**reforçar confirmação** e **facilitar reagendamento** para quem marca com muita antecedência."
        )

    with c2:
        st.markdown("### Comparecimento por faixa etária")
        st.caption(
            "Métrica: **Comparecimento (%)**. "
            "O que olhar: diferença de comportamento em **60+ vs <60** para personalizar a comunicação."
        )
        tmp = df.copy()
        tmp["faixa_idade"] = tmp["idade"].apply(lambda x: "60+" if x >= 60 else "<60")
        att = comparecimento_por(tmp, "faixa_idade")

        fig = px.bar(
            att,
            x="faixa_idade",
            y="taxa_comparecimento",
            text="taxa_comparecimento",
            labels={
                "faixa_idade": "Faixa etária",
                "taxa_comparecimento": "Comparecimento (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1%}",
            textposition="outside",
            hovertemplate="Faixa: %{x}<br>Comparecimento: %{y:.1%}<extra></extra>",
        )
        fig.update_layout(height=330, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
