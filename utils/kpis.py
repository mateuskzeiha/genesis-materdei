import pandas as pd
import numpy as np

def compute_exec_kpis(df: pd.DataFrame) -> dict:
    agendados = int(df["agendado"].sum())
    compareceram = int(df["compareceu"].sum())
    faltaram = int(df["faltou"].sum())

    conversao = None  # Kaggle não tem "interessados"
    taxa_comparecimento = compareceram / agendados if agendados else 0.0
    taxa_no_show = faltaram / agendados if agendados else 0.0

    return {
        "interessados": None,
        "agendados": agendados,
        "compareceram": compareceram,
        "faltaram": faltaram,
        "conversao": conversao,
        "taxa_comparecimento": taxa_comparecimento,
        "taxa_no_show": taxa_no_show,
    }

def pipeline_agenda(df: pd.DataFrame) -> pd.DataFrame:
    k = compute_exec_kpis(df)
    return pd.DataFrame({
        "etapa": ["Agendados", "Compareceram", "No-show"],
        "qtd": [k["agendados"], k["compareceram"], k["faltaram"]],
    })

def perda_financeira(df: pd.DataFrame) -> dict:
    k = compute_exec_kpis(df)
    valor = float(df["valor_medio"].mean()) if len(df) else 0.0
    perda_no_show = k["faltaram"] * valor
    return {"valor_medio": valor, "perda_no_show": perda_no_show}

def simular_reducao_no_show(df: pd.DataFrame, reducao: float) -> float:
    agendados = int(df["agendado"].sum())
    valor = float(df["valor_medio"].mean()) if len(df) else 0.0
    return agendados * reducao * valor

def no_show_por(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col).agg(
        agendados=("id_agendamento", "count"),
        faltaram=("faltou", "sum"),
    ).reset_index()
    g["taxa_no_show"] = g["faltaram"] / g["agendados"].replace(0, np.nan)
    return g.sort_values("taxa_no_show", ascending=False)

def comparecimento_por(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col).agg(
        agendados=("id_agendamento", "count"),
        compareceram=("compareceu", "sum"),
    ).reset_index()
    g["taxa_comparecimento"] = g["compareceram"] / g["agendados"].replace(0, np.nan)
    return g.sort_values("taxa_comparecimento", ascending=False)

def impacto_antecedencia(df: pd.DataFrame) -> pd.DataFrame:
    bins = [-1, 0, 1, 3, 7, 14, 30, 999]
    labels = ["0", "1", "2-3", "4-7", "8-14", "15-30", "30+"]

    tmp = df.copy()
    tmp["faixa_antecedencia"] = pd.cut(tmp["antecedencia_dias"], bins=bins, labels=labels)

    g = tmp.groupby("faixa_antecedencia").agg(
        agendados=("id_agendamento", "count"),
        faltaram=("faltou", "sum"),
    ).reset_index()

    g["taxa_no_show"] = g["faltaram"] / g["agendados"].replace(0, np.nan)
    return g

def priorizar_acoes(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["bairro", "canal_confirmacao"]).agg(
        agendados=("id_agendamento", "count"),
        faltaram=("faltou", "sum"),
        valor_medio=("valor_medio", "mean"),
        antecedencia_media=("antecedencia_dias", "mean"),
    ).reset_index()

    g["taxa_no_show"] = g["faltaram"] / g["agendados"].replace(0, np.nan)
    g["perda_estimada"] = g["faltaram"] * g["valor_medio"]
    g["cluster"] = g["bairro"] + " | " + g["canal_confirmacao"]

    g["score_prioridade"] = (
        g["perda_estimada"].fillna(0)
        + (g["taxa_no_show"].fillna(0) * 10000)
        + (g["antecedencia_media"].fillna(0) * 30)
    )

    g = g.sort_values("score_prioridade", ascending=False)
    return g[["cluster", "agendados", "taxa_no_show", "antecedencia_media", "perda_estimada"]]
