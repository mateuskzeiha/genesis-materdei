import streamlit as st
import plotly.express as px

from utils.kpis import compute_exec_kpis, pipeline_agenda, perda_financeira, simular_reducao_no_show


def render_exec_overview(df):
    st.subheader("Executive Overview")

    st.caption(
        "Visão consolidada para gestão: taxa de no-show, impacto financeiro e potencial de "
        "recuperação com intervenções direcionadas."
    )

    kpis = compute_exec_kpis(df)
    fin = perda_financeira(df)
    taxa_no_show = kpis["taxa_no_show"]

    # Alerta colorido quando taxa de no-show ultrapassa 20%
    if taxa_no_show > 0.20:
        st.error(
            f"⚠️ **Alerta: taxa de no-show está em {taxa_no_show:.1%}** — acima do limite crítico de 20%. "
            "Recomenda-se ativar protocolo de intervenção imediata (aba **Act**)."
        )
    elif taxa_no_show > 0.15:
        st.warning(
            f"⚠️ Taxa de no-show em {taxa_no_show:.1%} — atenção, aproximando-se do limite de 20%. "
            "Monitore tendência nas próximas semanas."
        )
    else:
        st.success(
            f"✅ Taxa de no-show em {taxa_no_show:.1%} — dentro da faixa aceitável (< 15%)."
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conversão", "N/A (base só tem agendados)")
    c2.metric("Comparecimento", f"{kpis['taxa_comparecimento']:.1%}")
    c3.metric("No-show", f"{taxa_no_show:.1%}")
    c4.metric("Perda estimada (no-show)", f"R$ {fin['perda_no_show']:,.0f}".replace(",", "."))

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### Pipeline de Agenda")
        st.caption(
            "Proporção de consultas agendadas que resultaram em comparecimento vs falta. "
            "No-show = ociosidade + perda direta de receita."
        )
        pipe = pipeline_agenda(df)
        fig = px.funnel(pipe, x="qtd", y="etapa", orientation="h")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Simulador de ROI")
        st.caption(
            "Quanto de receita é recuperável ao reduzir o no-show em X%? "
            "Use como argumento para justificar investimento nas intervenções."
        )
        reducao = st.slider("Redução de no-show (%)", 0, 30, 5, 1)
        impacto = simular_reducao_no_show(df, reducao / 100.0)
        st.success(f"Receita recuperável estimada: **R$ {impacto:,.0f}**".replace(",", "."))
