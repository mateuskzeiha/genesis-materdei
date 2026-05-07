import streamlit as st
import plotly.express as px

from utils.kpis import compute_exec_kpis, pipeline_agenda, perda_financeira, simular_reducao_no_show
from utils.components import kpi_card, kpi_row, alert_banner


def render_exec_overview(df):
    st.subheader("Executive Overview")
    st.caption(
        "Visão consolidada para gestão: taxa de no-show, impacto financeiro e potencial de "
        "recuperação com intervenções direcionadas."
    )

    kpis = compute_exec_kpis(df)
    fin = perda_financeira(df)
    taxa_no_show = kpis["taxa_no_show"]
    taxa_comp = kpis["taxa_comparecimento"]

    # Alerta dinâmico colorido
    st.markdown(alert_banner(taxa_no_show), unsafe_allow_html=True)

    # KPI Cards HTML
    cor_noshow = "#d32f2f" if taxa_no_show > 0.20 else ("#f57c00" if taxa_no_show > 0.15 else "#388e3c")
    perda_fmt = f"R$ {fin['perda_no_show']:,.0f}".replace(",", ".")

    cards = [
        kpi_card("📅", "Agendamentos", f"{kpis['agendados']:,}".replace(",", "."),
                 sublabel="no período filtrado"),
        kpi_card("✅", "Comparecimento", f"{taxa_comp:.1%}",
                 sublabel=f"{kpis['compareceram']:,} pacientes".replace(",", "."),
                 color="#388e3c"),
        kpi_card("⚠️", "No-show", f"{taxa_no_show:.1%}",
                 sublabel=f"{kpis['faltaram']:,} faltas".replace(",", "."),
                 color=cor_noshow),
        kpi_card("💸", "Perda estimada", perda_fmt,
                 sublabel="por no-show no período",
                 color="#9333ea"),
    ]
    st.markdown(kpi_row(cards), unsafe_allow_html=True)

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
        reducao = st.slider("Redução de no-show (%)", 0, 30, 5, 1, key="exec_roi_slider")
        impacto = simular_reducao_no_show(df, reducao / 100.0)
        st.markdown(
            kpi_card("💰", "Receita recuperável estimada",
                     f"R$ {impacto:,.0f}".replace(",", "."),
                     sublabel=f"com {reducao}% de redução no no-show",
                     color="#089489"),
            unsafe_allow_html=True,
        )
