import streamlit as st
import plotly.express as px

from utils.model import treinar_modelo_no_show, pontuar_risco_no_show


def _acao_por_risco(risco: float) -> tuple[str, str]:
    """Retorna (label_faixa, descricao_acao) baseado no score."""
    if risco >= 0.60:
        return "ALTO", "Ligação humana — contato direto (72h antes)"
    if risco >= 0.30:
        return "MODERADO", "WhatsApp — confirmação ativa (48h antes)"
    return "BAIXO", "SMS — lembrete padrão (24h antes)"


def render_predict(df):
    st.subheader("Predict — Risco de No-show")

    st.caption(
        "Objetivo desta aba: **identificar quem tem maior chance de faltar** e "
        "priorizar quem acionar — com o canal e timing certo para cada nível de risco."
    )

    colA, colB = st.columns([1.2, 1])

    # ======================
    # COLUNA A — Modelo + métricas + fatores
    # ======================
    with colA:
        model_pack = treinar_modelo_no_show(df)
        if model_pack is None:
            st.warning("Sem dados suficientes para treinar modelo (mínimo 500 registros).")
            return

        auc = model_pack["auc"]

        st.markdown("### Qualidade do modelo (métricas de validação)")

        # AUC explicado
        st.info(f"📊 {model_pack['auc_explanation']}")

        # Linha de métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AUC", f"{auc:.3f}")
        m2.metric("F1-score (no-show)", f"{model_pack['f1']:.3f}")
        m3.metric("Precisão", f"{model_pack['precision']:.3f}")
        m4.metric("Recall", f"{model_pack['recall']:.3f}")

        st.caption(
            "**Como ler as métricas:**\n"
            "- **AUC**: capacidade de ordenar risco (0,5 = aleatório, 1,0 = perfeito)\n"
            "- **F1-score**: equilíbrio entre precisão e recall para a classe *faltou*\n"
            "- **Precisão**: dos marcados como risco, quantos realmente faltaram\n"
            "- **Recall**: dos que faltaram, quantos o modelo identificou\n"
            f"- **Base de treino/validação**: {model_pack['n_train']:,} agendamentos"
        )

        st.divider()

        st.markdown("### Fatores que mais influenciam o risco de no-show")
        st.caption(
            "Barra maior = fator com maior peso na previsão. "
            "Isso não é causalidade — é padrão estatístico detectado na base."
        )

        fi = model_pack["feature_importance"].copy()

        def traduzir_feature(nome: str) -> str:
            n = str(nome)
            n = n.replace("canal_confirmacao_", "Canal: ")
            n = n.replace("bairro_", "Bairro: ")
            n = n.replace("idade_60_mais", "Idade 60+ (sim/não)")
            n = n.replace("historico_no_show", "Histórico de no-show")
            n = n.replace("hora_agendamento", "Hora do agendamento")
            n = n.replace("dia_semana", "Dia da semana")
            n = n.replace("antecedencia_dias", "Antecedência (dias)")
            n = n.replace("antecedencia_minutos", "Antecedência (minutos)")
            n = n.replace("idade", "Idade")
            return n

        fi["feature"] = fi["feature"].apply(traduzir_feature)
        fi = fi.rename(columns={"feature": "Fator", "importance": "Peso"})

        fig = px.bar(
            fi,
            x="Peso",
            y="Fator",
            orientation="h",
            title="Importância dos fatores (RandomForest)",
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "**Interpretação prática:**\n"
            "- **Histórico de no-show**: paciente que já faltou antes tem maior risco — "
            "esse é o fator mais acionável (permite segmentação direta).\n"
            "- **Antecedência**: marcar muito antes aumenta o risco de esquecer ou mudar de plano.\n"
            "- **Canal: Sem SMS**: ausência de lembrete ativo eleva o risco — reforça a importância do contato.\n"
            "- **Bairro**: proxy de distância, acesso e perfil logístico — não é estigma, é sinal operacional."
        )

    # ======================
    # COLUNA B — Distribuição + lista de ação
    # ======================
    with colB:
        st.markdown("### Distribuição do score de risco")
        st.caption(
            "Histograma de quantos pacientes estão em cada nível de risco. "
            "Barras à direita = mais casos de alto risco no período filtrado."
        )

        scored = pontuar_risco_no_show(df, model_pack)
        if scored is None:
            st.warning("Não foi possível gerar score.")
            return

        fig = px.histogram(
            scored,
            x="risco_no_show",
            nbins=20,
            title="Score de risco (0 = baixo, 1 = alto)",
            labels={"risco_no_show": "Score de risco de no-show"},
        )
        fig.add_vline(x=0.30, line_dash="dash", line_color="orange",
                      annotation_text="30%", annotation_position="top")
        fig.add_vline(x=0.60, line_dash="dash", line_color="red",
                      annotation_text="60%", annotation_position="top")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

        limiar = st.slider(
            "Limiar para 'alto risco'",
            0.50, 0.95, 0.75, 0.01,
            key="predict_limiar_alto_risco"
        )
        qtd_alto = int((scored["risco_no_show"] >= limiar).sum())
        total = len(scored)

        st.success(
            f"**Alto risco (≥ {limiar:.0%}): {qtd_alto} de {total}** "
            f"({(qtd_alto / total if total else 0):.1%})"
        )

        st.markdown("### Top 15 para intervenção imediata")
        st.caption("Quem contatar primeiro — ordenado por maior score de risco.")

        top = scored.sort_values("risco_no_show", ascending=False).head(15)[
            ["id_agendamento", "idade", "canal_confirmacao", "antecedencia_dias", "risco_no_show"]
        ].rename(columns={
            "id_agendamento": "ID",
            "idade": "Idade",
            "canal_confirmacao": "Canal",
            "antecedencia_dias": "Antecedência (dias)",
            "risco_no_show": "Risco (0-1)",
        })
        st.dataframe(top, use_container_width=True)

    # ======================
    # SEÇÃO ABAIXO DAS COLUNAS — Exemplo prático
    # ======================
    st.divider()
    st.markdown("## Exemplo prático — Paciente de maior risco no período")
    st.caption(
        "Este é o caso mais urgente entre os agendamentos filtrados. "
        "Mostra como o modelo se traduz em ação concreta para o time operacional."
    )

    if scored is not None and len(scored) > 0:
        top1 = scored.sort_values("risco_no_show", ascending=False).iloc[0]
        risco_val = float(top1["risco_no_show"])
        risco_pct = risco_val * 100
        antecedencia = int(top1.get("antecedencia_dias", 0))
        canal = str(top1.get("canal_confirmacao", "N/D"))
        idade = int(top1.get("idade", 0))
        id_mask = f"PAC-{str(int(top1['id_agendamento']))[-5:]}"

        faixa_label, acao = _acao_por_risco(risco_val)

        if faixa_label == "ALTO":
            borda_cor = "#d32f2f"
            fundo_cor = "#fff5f5"
            emoji = "🔴"
        elif faixa_label == "MODERADO":
            borda_cor = "#f57c00"
            fundo_cor = "#fff8f0"
            emoji = "🟠"
        else:
            borda_cor = "#388e3c"
            fundo_cor = "#f5fff5"
            emoji = "🟢"

        st.markdown(
            f"""
<div style="border: 2px solid {borda_cor}; border-radius: 12px; padding: 20px;
     background: {fundo_cor}; max-width: 520px;">
  <h4 style="margin: 0 0 12px 0; color: #222;">{emoji} Paciente {id_mask} — {idade} anos</h4>
  <p style="margin: 6px 0; font-size: 1.1em;">
    <b>Risco de no-show:</b>
    <span style="font-size: 1.5em; font-weight: bold; color: {borda_cor};">{risco_pct:.1f}%</span>
    &nbsp;<span style="background:{borda_cor}; color:#fff; border-radius:4px;
    padding: 2px 8px; font-size: 0.85em;">{faixa_label}</span>
  </p>
  <p style="margin: 6px 0;"><b>Antecedência:</b> {antecedencia} dias até a consulta</p>
  <p style="margin: 6px 0;"><b>Canal atual:</b> {canal}</p>
  <p style="margin: 12px 0 0 0; font-size: 1.05em; border-top: 1px solid {borda_cor}; padding-top: 10px;">
    ✅ <b>Ação recomendada:</b> {acao}
  </p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("### Top 10 pacientes de alto risco — fila acionável")
        st.caption(
            "Tabela resumida para o time operacional: risco, antecedência e ação recomendada "
            "para cada paciente — pronta para impressão ou repasse ao call center."
        )

        top10 = scored.sort_values("risco_no_show", ascending=False).head(10).copy()
        top10["Risco"] = (top10["risco_no_show"] * 100).round(1).astype(str) + "%"
        top10["Faixa"] = top10["risco_no_show"].apply(lambda r: _acao_por_risco(r)[0])
        top10["Ação recomendada"] = top10["risco_no_show"].apply(lambda r: _acao_por_risco(r)[1])

        cols_show = {
            "id_agendamento": "ID",
            "idade": "Idade",
            "canal_confirmacao": "Canal atual",
            "antecedencia_dias": "Antecedência (dias)",
            "Risco": "Risco",
            "Faixa": "Faixa",
            "Ação recomendada": "Ação recomendada",
        }
        top10_view = top10[[c for c in cols_show if c in top10.columns or c in ["Risco", "Faixa", "Ação recomendada"]]].rename(columns=cols_show)
        st.dataframe(top10_view, use_container_width=True, hide_index=True)
