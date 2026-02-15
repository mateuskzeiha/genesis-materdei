import streamlit as st
import plotly.express as px

from utils.model import treinar_modelo_no_show, pontuar_risco_no_show


def render_predict(df):
    st.subheader("Predict — Risco de No-show")

    st.caption(
        "Objetivo desta aba: **priorizar quem contatar primeiro** (confirmação/WhatsApp/SMS/ligação) "
        "para reduzir no-show com o menor esforço possível."
    )

    colA, colB = st.columns([1.2, 1])

    # ======================
    # COLUNA A — Modelo + fatores
    # ======================
    with colA:
        model_pack = treinar_modelo_no_show(df)
        if model_pack is None:
            st.warning("Sem dados suficientes para treinar modelo.")
            return

        auc = float(model_pack["auc"])

        st.markdown("### Qualidade do modelo (AUC na validação)")
        st.caption(
            "**AUC** mede a capacidade do modelo de separar quem **vai faltar** de quem **vai comparecer**.\n"
            "- **0,50** = chute (aleatório)\n"
            "- **0,65–0,75** = bom para priorização operacional\n"
            f"- **Seu AUC: {auc:.3f}** = já útil para ordenar atendimento e focar esforço onde importa"
        )
        st.metric("AUC (validação)", f"{auc:.3f}")

        st.divider()

        st.markdown("### O que mais influencia o risco de no-show (explicação do modelo)")
        st.caption(
            "Este gráfico mostra os **fatores que o modelo mais usa** para estimar risco.\n"
            "Importante: não é “culpa” do fator — é **padrão estatístico na base**.\n"
            "**Como ler:** barra maior = maior peso na previsão (impacta mais o score de risco)."
        )

        # Renomeia colunas para português
        fi = model_pack["feature_importance"].copy()
        fi = fi.rename(columns={"feature": "Fator (o que o modelo usa)", "importance": "Peso na previsão"})

        # Traduções e limpeza de nomes para ficar humano
        def traduzir_feature(nome: str) -> str:
            n = str(nome)

            # One-hot do bairro/canal
            n = n.replace("canal_confirmacao_", "Canal: ")
            n = n.replace("bairro_", "Bairro: ")

            # Numéricos
            n = n.replace("idade_60_mais", "Idade 60+ (sim/não)")
            n = n.replace("idade", "Idade")
            n = n.replace("antecedencia_dias", "Antecedência (dias)")
            n = n.replace("antecedencia_minutos", "Antecedência (minutos)")

            return n

        fi["Fator (o que o modelo usa)"] = fi["Fator (o que o modelo usa)"].apply(traduzir_feature)

        fig = px.bar(
            fi,
            x="Peso na previsão",
            y="Fator (o que o modelo usa)",
            orientation="h",
            title="Fatores com maior impacto na previsão de no-show (proxy)",
        )
        fig.update_layout(height=430, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "**O que significa na prática (bem direto):**\n"
            "- **Bairro**: não é “o bairro causa no-show”. Ele funciona como **proxy** de padrões reais (acesso, distância, perfil socioeconômico, logística). "
            "Se um bairro aparece forte, é um sinal de que ali existe um comportamento diferente na base.\n"
            "- **Canal: SMS / Sem SMS**: é um proxy de **estratégia de confirmação**. Se “Sem SMS” pesa, sugere que lembrete/confirmação tem efeito.\n"
            "- **Antecedência**: marcar muito antes pode aumentar chance de esquecer/mudar plano; isso costuma subir o risco.\n"
            "- **Idade (60+)**: pode demandar comunicação mais clara e ativa (ex.: ligação humana em casos críticos)."
        )

    # ======================
    # COLUNA B — Distribuição + lista de ação
    # ======================
    with colB:
        st.markdown("### Distribuição do risco de no-show (na base filtrada)")
        st.caption(
            "Este histograma mostra **quantos pacientes estão em cada nível de risco**.\n"
            "**Como ler:**\n"
            "- Quanto mais barras no lado direito, mais casos de alto risco.\n"
            "- Use isso para **dimensionar esforço** (ex.: quantos ligar hoje / quantos automatizar)."
        )

        scored = pontuar_risco_no_show(df, model_pack)
        if scored is None:
            st.warning("Não foi possível gerar score.")
            return

        fig = px.histogram(
            scored,
            x="risco_no_show",
            nbins=20,
            title="Distribuição do score de risco (0 = baixo, 1 = alto)",
            labels={"risco_no_show": "Score de risco de no-show (0 a 1)"},
        )
        fig.update_layout(height=310, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # regra simples de “alto risco” para ficar autoexplicável
        limiar = st.slider(
            "Limiar para considerar 'alto risco' (0 a 1)",
            0.50, 0.95, 0.75, 0.01,
            key="predict_limiar_alto_risco"
        )
        qtd_alto_risco = int((scored["risco_no_show"] >= limiar).sum())
        total = len(scored)

        st.success(
            f"**Alto risco (≥ {limiar:.2f}): {qtd_alto_risco} de {total} agendamentos** "
            f"({(qtd_alto_risco/total if total else 0):.1%})."
        )

        st.markdown("### Top 15 para intervenção (lista acionável)")
        st.caption(
            "Aqui está o que vira ação: **quem contatar primeiro**.\n"
            "Sugestão prática: priorize **alto risco** com ligação ou confirmação dupla; risco médio com automação."
        )

        top = scored.sort_values("risco_no_show", ascending=False).head(15)[
            ["id_agendamento", "idade", "canal_confirmacao", "bairro", "antecedencia_dias", "risco_no_show"]
        ].rename(columns={
            "id_agendamento": "ID",
            "idade": "Idade",
            "canal_confirmacao": "Canal",
            "bairro": "Bairro",
            "antecedencia_dias": "Antecedência (dias)",
            "risco_no_show": "Risco (0-1)",
        })

        st.dataframe(top, use_container_width=True)
