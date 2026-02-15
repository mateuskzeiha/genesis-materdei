import streamlit as st
import plotly.express as px

from utils.kpis import priorizar_acoes, simular_reducao_no_show
from utils.model import treinar_modelo_no_show, pontuar_risco_no_show


def render_act(df):
    st.subheader("Act — Plano de ação (fila de trabalho para reduzir no-show)")

    st.caption(
        "Aqui vira operação: **quem acionar**, **como acionar** e **qual esforço** (bot vs ligação). "
        "A lógica é baseada no **score de risco** do Predict."
    )

    # ======================
    # 1) Gerar score de risco (reutiliza modelo do Predict)
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
    # 2) Definir faixas de risco (alto / moderado / baixo)
    # ======================
    st.markdown("### Configuração das faixas de risco")
    st.caption(
        "Defina os limites das faixas. "
        "Regra: **Alto risco ≥ limite alto**, **Moderado entre limites**, **Baixo abaixo do limite moderado**."
    )

    cA, cB, cC = st.columns([1, 1, 1.2])

    with cA:
        limiar_moderado = st.slider(
            "Limite do risco moderado",
            0.30, 0.90, 0.55, 0.01,
            key="act_limiar_moderado"
        )

    with cB:
        limiar_alto = st.slider(
            "Limite do alto risco",
            0.40, 0.95, 0.75, 0.01,
            key="act_limiar_alto"
        )

    with cC:
        st.info(
            "Dica prática:\n"
            "- Se sua operação tem pouca gente para ligar, suba o **limite alto**.\n"
            "- Se dá para automatizar mais WhatsApp/SMS, baixe o **limite moderado**."
        )

    # Garante coerência (alto sempre >= moderado)
    if limiar_alto < limiar_moderado:
        limiar_alto = limiar_moderado

    # ======================
    # 3) Rotular faixa + ação recomendada (o que você pediu)
    # ======================
    tmp = scored.copy()

    def faixa_risco(r: float) -> str:
        if r >= limiar_alto:
            return "ALTO"
        elif r >= limiar_moderado:
            return "MODERADO"
        return "BAIXO"

    tmp["faixa_risco"] = tmp["risco_no_show"].apply(faixa_risco)

    # Ações:
    # - ALTO e <60: WhatsApp + SMS (bot)
    # - ALTO e 60+: Ligação (manual)
    # - MODERADO: WhatsApp (bot) + lembrete SMS padrão
    # - BAIXO: lembrete SMS padrão
    def acao_recomendada(risco: float, idade_60_mais: int) -> str:
        if risco >= limiar_alto:
            if int(idade_60_mais) == 1:
                return "Ligar (manual) — confirmação ativa"
            return "WhatsApp + SMS (bot) — confirmação dupla"
        if risco >= limiar_moderado:
            return "WhatsApp (bot) + SMS padrão — confirmar"
        return "SMS padrão — lembrete"

    def tipo_execucao(acao: str) -> str:
        # Para você medir carga operacional
        if "Ligar" in acao:
            return "Manual (analista)"
        return "Automático (bot)"

    tmp["acao_recomendada"] = tmp.apply(
        lambda row: acao_recomendada(row["risco_no_show"], row["idade_60_mais"]),
        axis=1
    )
    tmp["execucao"] = tmp["acao_recomendada"].apply(tipo_execucao)

    # ======================
    # 4) Resumo executivo: quantos casos por faixa + carga manual x bot
    # ======================
    st.divider()
    st.markdown("### Visão rápida da operação (quantos casos e qual esforço)")

    total = len(tmp)
    alto = int((tmp["faixa_risco"] == "ALTO").sum())
    moderado = int((tmp["faixa_risco"] == "MODERADO").sum())
    baixo = int((tmp["faixa_risco"] == "BAIXO").sum())

    manual = int((tmp["execucao"] == "Manual (analista)").sum())
    auto = int((tmp["execucao"] == "Automático (bot)").sum())

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total", f"{total:,}".replace(",", "."))
    k2.metric("Alto risco", f"{alto:,}".replace(",", "."), f"{(alto/total if total else 0):.1%}")
    k3.metric("Risco moderado", f"{moderado:,}".replace(",", "."), f"{(moderado/total if total else 0):.1%}")
    k4.metric("Baixo risco", f"{baixo:,}".replace(",", "."), f"{(baixo/total if total else 0):.1%}")
    k5.metric("Ligaçõ​es (manual)", f"{manual:,}".replace(",", "."), f"{(manual/total if total else 0):.1%}")

    st.caption(
        f"Automático (bot): **{auto}** casos | Manual (analista): **{manual}** casos. "
        "Isso é a fila de trabalho real."
    )

    # ======================
    # 5) Ranking por faixa + idade (alto risco detalhado)
    # ======================
    st.divider()
    st.markdown("### Ranking de ações por faixa (guia para analistas)")

    # visão agregada para facilitar “o que fazer primeiro”
    agg = tmp.groupby(["faixa_risco", "idade_60_mais", "acao_recomendada", "execucao"]).agg(
        qtd=("id_agendamento", "count"),
        risco_medio=("risco_no_show", "mean"),
        antecedencia_media=("antecedencia_dias", "mean"),
    ).reset_index()

    agg["grupo_idade"] = agg["idade_60_mais"].apply(lambda x: "60+" if int(x) == 1 else "<60")

    # ordenação: alto primeiro, depois moderado, depois baixo
    ordem = {"ALTO": 0, "MODERADO": 1, "BAIXO": 2}
    agg["ordem"] = agg["faixa_risco"].map(ordem).fillna(9)
    agg = agg.sort_values(["ordem", "qtd"], ascending=[True, False]).drop(columns=["ordem", "idade_60_mais"])

    agg = agg.rename(columns={
        "faixa_risco": "Faixa de risco",
        "grupo_idade": "Grupo idade",
        "acao_recomendada": "Ação recomendada",
        "execucao": "Execução",
        "qtd": "Qtd casos",
        "risco_medio": "Risco médio (0-1)",
        "antecedencia_media": "Antecedência média (dias)",
    })

    st.dataframe(agg, use_container_width=True)

    st.info(
        "**Regra do ALTO risco (do jeito que você pediu):**\n"
        "- **ALTO + <60** → **WhatsApp + SMS (bot)**\n"
        "- **ALTO + 60+** → **Ligação (manual)**\n\n"
        "Isso cria um roteiro claro para o time: bot onde dá escala, humano onde a chance de falha é mais cara."
    )

    # ======================
    # 6) Fila acionável (planilha/guia)
    # ======================
    st.divider()
    st.markdown("### Fila de ação (planilha operacional)")

    st.caption(
        "Esta tabela é a fila que o analista executa. "
        "Ordenada por risco (maior primeiro)."
    )

    fila = tmp.sort_values("risco_no_show", ascending=False)[
        ["id_agendamento", "idade", "canal_confirmacao", "bairro", "antecedencia_dias", "faixa_risco", "acao_recomendada", "execucao", "risco_no_show"]
    ].rename(columns={
        "id_agendamento": "ID",
        "idade": "Idade",
        "canal_confirmacao": "Canal",
        "bairro": "Bairro",
        "antecedencia_dias": "Antecedência (dias)",
        "faixa_risco": "Faixa de risco",
        "acao_recomendada": "Ação recomendada",
        "execucao": "Execução",
        "risco_no_show": "Risco (0-1)",
    })

    st.dataframe(fila.head(200), use_container_width=True)

    # Export CSV para operar (muito útil)
    st.download_button(
        "Baixar fila completa (CSV)",
        data=fila.to_csv(index=False).encode("utf-8"),
        file_name="fila_acao_no_show.csv",
        mime="text/csv",
        key="act_download_fila_csv",
    )

    # ======================
    # 7) Mantém visão de clusters e ROI (como antes, só mais claro)
    # ======================
    st.divider()
    st.markdown("### Onde está a perda (clusters) e quanto recupera (ROI)")

    prio = priorizar_acoes(df)

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("#### Ranking de clusters (Top 20)")
        st.caption("Cluster = **bairro + canal**. Use para atacar causas estruturais (não só casos individuais).")
        st.dataframe(prio.head(20), use_container_width=True)

    with right:
        st.markdown("#### Pareto da perda estimada (Top 12)")
        st.caption("Mostra onde poucos clusters concentram a maior parte do impacto financeiro.")
        pareto = prio.head(12).copy()
        fig = px.bar(pareto, x="cluster", y="perda_estimada", labels={"perda_estimada": "Perda estimada (R$)"})
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### Simulação final (ROI direto)")
    st.caption("Tradução para banca: reduzir no-show em X% = recuperar R$ Y no período.")

    reducao = st.slider(
        "Redução de no-show (%)",
        0, 30, 5, 1,
        key="act_reducao_no_show_roi"
    )
    impacto = simular_reducao_no_show(df, reducao / 100.0)
    st.success(f"Receita recuperável estimada: **R$ {impacto:,.0f}**".replace(",", "."))
