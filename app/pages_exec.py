import streamlit as st
import plotly.express as px

from utils.kpis import compute_exec_kpis, pipeline_agenda, perda_financeira, simular_reducao_no_show

def render_exec_overview(df):
    st.subheader("Executive Overview")

    st.caption("Visão rápida para diretoria: taxa de no-show, perda estimada e potencial de recuperação.")

    kpis = compute_exec_kpis(df)
    fin = perda_financeira(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conversão", "N/A (base só tem agendados)")
    c2.metric("Comparecimento", f"{kpis['taxa_comparecimento']:.1%}")
    c3.metric("No-show", f"{kpis['taxa_no_show']:.1%}")
    c4.metric("Perda estimada (no-show)", f"R$ {fin['perda_no_show']:,.0f}".replace(",", "."))

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### Pipeline de Agenda")
        st.caption("O que olhar: proporção de faltas vs presença. Por quê: no-show = ociosidade + perda direta.")
        pipe = pipeline_agenda(df)
        fig = px.funnel(pipe, x="qtd", y="etapa", orientation="h")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Simulador de ROI")
        st.caption("O que olhar: quanto recupera em R$ ao reduzir no-show em X%.")
        reducao = st.slider("Redução de no-show (%)", 0, 30, 5, 1)
        impacto = simular_reducao_no_show(df, reducao / 100.0)
        st.success(f"Receita recuperável estimada: **R$ {impacto:,.0f}**".replace(",", "."))
