import streamlit as st
import plotly.express as px
import pandas as pd

from utils.kpis import priorizar_acoes, simular_reducao_no_show
from utils.model import treinar_modelo_no_show, pontuar_risco_no_show
from utils.components import protocol_blocks, kpi_card, kpi_row


# Custos unitários de intervenção (referência operacional)
CUSTO_SMS = 0.10        # R$ por SMS
CUSTO_WHATSAPP = 0.50   # R$ por mensagem WhatsApp
CUSTO_LIGACAO = 8.00    # R$ por ligação (tempo de analista ~3 min)


def render_act(df):
    st.subheader("Act — Plano de Ação Operacional")

    st.caption(
        "Esta aba traduz o risco em operação: **quem acionar, por qual canal e quando**. "
        "O protocolo abaixo define o padrão — a fila de trabalho implementa automaticamente."
    )

    # ======================
    # PROTOCOLO DE AÇÃO (blocos visuais)
    # ======================
    st.markdown("### Protocolo padrão de intervenção")
    st.caption("Referência imutável: toda decisão de acionamento segue estes critérios.")

    st.markdown(protocol_blocks(), unsafe_allow_html=True)

    st.divider()

    # ======================
    # GERAR SCORE DE RISCO
    # ======================
    model_pack = treinar_modelo_no_show(df)
    if model_pack is None:
        st.warning("Sem dados suficientes para gerar score e montar fila de ação.")
        return

    scored = pontuar_risco_no_show(df, model_pack)
    if scored is None or len(scored) == 0:
        st.warning("Não foi possível gerar score para a base filtrada.")
        return

    # ======================
    # CONFIGURAÇÃO DE FAIXAS
    # ======================
    st.markdown("### Configuração das faixas de risco")
    st.caption(
        "Ajuste os limiares conforme a capacidade operacional do time. "
        "Padrão do protocolo: moderado ≥ 30%, alto ≥ 60%."
    )

    cA, cB, cC = st.columns([1, 1, 1.2])
    with cA:
        limiar_moderado = st.slider(
            "Limite risco moderado", 0.20, 0.70, 0.30, 0.01,
            key="act_limiar_moderado"
        )
    with cB:
        limiar_alto = st.slider(
            "Limite alto risco", 0.40, 0.95, 0.60, 0.01,
            key="act_limiar_alto"
        )
    with cC:
        st.info(
            "Dica: se a fila de ligações for muito grande, **suba o limite alto**. "
            "Se quiser ampliar WhatsApp automatizado, **baixe o moderado**."
        )

    if limiar_alto < limiar_moderado:
        limiar_alto = limiar_moderado

    # ======================
    # ROTULAR FAIXA + AÇÃO
    # ======================
    tmp = scored.copy()

    def faixa_risco(r: float) -> str:
        if r >= limiar_alto:
            return "ALTO"
        if r >= limiar_moderado:
            return "MODERADO"
        return "BAIXO"

    def acao_recomendada(risco: float, idade_60_mais: int) -> str:
        if risco >= limiar_alto:
            if int(idade_60_mais) == 1:
                return "Ligação (manual) — confirmação ativa"
            return "WhatsApp + SMS (bot) — confirmação dupla"
        if risco >= limiar_moderado:
            return "WhatsApp (bot) + SMS padrão"
        return "SMS padrão — lembrete"

    def tipo_execucao(acao: str) -> str:
        return "Manual (analista)" if "Ligar" in acao or "Ligação" in acao else "Automático (bot)"

    def custo_unitario(acao: str) -> float:
        if "Ligação" in acao or "Ligar" in acao:
            return CUSTO_LIGACAO
        if "WhatsApp" in acao:
            return CUSTO_WHATSAPP + CUSTO_SMS  # combo
        return CUSTO_SMS

    tmp["faixa_risco"] = tmp["risco_no_show"].apply(faixa_risco)
    tmp["acao_recomendada"] = tmp.apply(
        lambda row: acao_recomendada(row["risco_no_show"], row["idade_60_mais"]), axis=1
    )
    tmp["execucao"] = tmp["acao_recomendada"].apply(tipo_execucao)
    tmp["custo_intervencao"] = tmp["acao_recomendada"].apply(custo_unitario)

    # ======================
    # RESUMO EXECUTIVO — QUANTOS CASOS
    # ======================
    st.divider()
    st.markdown("### Distribuição atual por faixa de risco")
    st.caption(
        "Breakdown dos agendamentos filtrados nas 3 faixas do protocolo, "
        "com custo estimado de intervenção e perda financeira evitável."
    )

    total = len(tmp)
    valor_medio = float(df["valor_medio"].mean()) if "valor_medio" in df.columns else 150.0

    faixas_info = []
    for faixa, canal_label, custo_u in [
        ("BAIXO", "SMS", CUSTO_SMS),
        ("MODERADO", "WhatsApp", CUSTO_WHATSAPP + CUSTO_SMS),
        ("ALTO", "Ligação / WhatsApp+SMS", CUSTO_LIGACAO),
    ]:
        sub = tmp[tmp["faixa_risco"] == faixa]
        qtd = len(sub)
        risco_medio = float(sub["risco_no_show"].mean()) if qtd > 0 else 0.0
        no_shows_estimados = round(qtd * risco_medio)
        custo_total = round(qtd * custo_u, 2)
        perda_evitavel = round(no_shows_estimados * valor_medio, 2)
        roi = perda_evitavel / custo_total if custo_total > 0 else 0.0
        faixas_info.append({
            "Faixa": faixa,
            "Canal": canal_label,
            "Qtd agendamentos": qtd,
            "% do total": f"{(qtd / total * 100 if total else 0):.1f}%",
            "No-shows estimados": no_shows_estimados,
            "Custo intervenção (R$)": f"R$ {custo_total:,.2f}".replace(",", "."),
            "Perda evitável (R$)": f"R$ {perda_evitavel:,.2f}".replace(",", "."),
            "ROI estimado": f"{roi:.1f}x",
        })

    st.dataframe(pd.DataFrame(faixas_info), use_container_width=True, hide_index=True)

    custo_total_geral = sum(tmp["custo_intervencao"])
    no_shows_geral = round(sum(tmp["risco_no_show"]))
    perda_geral = no_shows_geral * valor_medio

    cards_roi = [
        kpi_card("💸", "Custo total de intervenção",
                 f"R$ {custo_total_geral:,.0f}".replace(",", "."),
                 sublabel="SMS + WhatsApp + ligações", color="#9333ea"),
        kpi_card("🚨", "No-shows estimados",
                 f"{no_shows_geral:,}".replace(",", "."),
                 sublabel="evitáveis com intervenção", color="#d32f2f"),
        kpi_card("💰", "Perda evitável",
                 f"R$ {perda_geral:,.0f}".replace(",", "."),
                 sublabel="receita em risco no período", color="#089489"),
    ]
    st.markdown(kpi_row(cards_roi), unsafe_allow_html=True)

    # ======================
    # RESUMO DE CARGA OPERACIONAL
    # ======================
    st.divider()
    st.markdown("### Visão rápida da operação")

    alto = int((tmp["faixa_risco"] == "ALTO").sum())
    moderado = int((tmp["faixa_risco"] == "MODERADO").sum())
    baixo = int((tmp["faixa_risco"] == "BAIXO").sum())
    manual = int((tmp["execucao"] == "Manual (analista)").sum())
    auto = int((tmp["execucao"] == "Automático (bot)").sum())

    cards_op = [
        kpi_card("📋", "Total agendamentos", f"{total:,}".replace(",", "."),
                 sublabel="no período filtrado"),
        kpi_card("🔴", "Alto risco", f"{alto:,}".replace(",", "."),
                 sublabel=f"{(alto/total if total else 0):.1%} do total", color="#d32f2f"),
        kpi_card("🟠", "Risco moderado", f"{moderado:,}".replace(",", "."),
                 sublabel=f"{(moderado/total if total else 0):.1%} do total", color="#f57c00"),
        kpi_card("🟢", "Baixo risco", f"{baixo:,}".replace(",", "."),
                 sublabel=f"{(baixo/total if total else 0):.1%} do total", color="#388e3c"),
        kpi_card("📞", "Ligações manuais", f"{manual:,}".replace(",", "."),
                 sublabel=f"{(manual/total if total else 0):.1%} — custo maior", color="#7c3aed"),
    ]
    st.markdown(kpi_row(cards_op), unsafe_allow_html=True)

    st.caption(
        f"Automático (bot): **{auto}** casos — zero custo humano. "
        f"Manual (analista): **{manual}** casos — fila priorizada abaixo."
    )

    # ======================
    # RANKING POR FAIXA
    # ======================
    st.divider()
    st.markdown("### Ranking de ações por segmento")
    st.caption("Cada linha é um grupo de pacientes com a mesma ação recomendada — use para dimensionar o time.")

    agg = tmp.groupby(["faixa_risco", "idade_60_mais", "acao_recomendada", "execucao"]).agg(
        qtd=("id_agendamento", "count"),
        risco_medio=("risco_no_show", "mean"),
        antecedencia_media=("antecedencia_dias", "mean"),
    ).reset_index()

    agg["grupo_idade"] = agg["idade_60_mais"].apply(lambda x: "60+" if int(x) == 1 else "<60")
    ordem = {"ALTO": 0, "MODERADO": 1, "BAIXO": 2}
    agg["ordem"] = agg["faixa_risco"].map(ordem).fillna(9)
    agg = agg.sort_values(["ordem", "qtd"], ascending=[True, False]).drop(columns=["ordem", "idade_60_mais"])
    agg = agg.rename(columns={
        "faixa_risco": "Faixa",
        "grupo_idade": "Grupo etário",
        "acao_recomendada": "Ação recomendada",
        "execucao": "Execução",
        "qtd": "Qtd casos",
        "risco_medio": "Risco médio",
        "antecedencia_media": "Antecedência média (dias)",
    })
    st.dataframe(agg, use_container_width=True, hide_index=True)

    # ======================
    # FILA ACIONÁVEL
    # ======================
    st.divider()
    st.markdown("### Fila operacional (planilha para o analista)")
    st.caption(
        "Lista completa ordenada por risco decrescente. "
        "Pronto para exportar e repassar ao call center ou bot."
    )

    fila = tmp.sort_values("risco_no_show", ascending=False)[
        ["id_agendamento", "idade", "canal_confirmacao", "bairro",
         "antecedencia_dias", "faixa_risco", "acao_recomendada", "execucao", "risco_no_show"]
    ].rename(columns={
        "id_agendamento": "ID",
        "idade": "Idade",
        "canal_confirmacao": "Canal",
        "bairro": "Bairro",
        "antecedencia_dias": "Antecedência (dias)",
        "faixa_risco": "Faixa",
        "acao_recomendada": "Ação recomendada",
        "execucao": "Execução",
        "risco_no_show": "Risco (0-1)",
    })

    st.dataframe(fila.head(200), use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Baixar fila completa (CSV)",
        data=fila.to_csv(index=False).encode("utf-8"),
        file_name="fila_acao_no_show.csv",
        mime="text/csv",
        key="act_download_fila_csv",
    )

    # ======================
    # CLUSTERS E ROI
    # ======================
    st.divider()
    st.markdown("### Onde está a perda estrutural (clusters) e quanto recupera")
    st.caption("Cluster = bairro + canal. Use para ações estruturais além do caso individual.")

    prio = priorizar_acoes(df)
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("#### Ranking de clusters (Top 20)")
        st.dataframe(prio.head(20), use_container_width=True)

    with right:
        st.markdown("#### Pareto da perda estimada (Top 12)")
        pareto = prio.head(12).copy()
        fig = px.bar(pareto, x="cluster", y="perda_estimada",
                     labels={"perda_estimada": "Perda estimada (R$)"})
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### Simulação de ROI — quanto recuperar ao reduzir no-show")
    st.caption("Tradução para gestão: cada ponto percentual de redução equivale a R$ X de receita recuperada.")

    reducao = st.slider(
        "Redução de no-show (%)", 0, 30, 5, 1,
        key="act_reducao_no_show_roi"
    )
    impacto = simular_reducao_no_show(df, reducao / 100.0)
    st.success(f"Receita recuperável estimada: **R$ {impacto:,.0f}**".replace(",", "."))
