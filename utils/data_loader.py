import os
import pandas as pd


def _resolve_path() -> str:
    """
    Resolve o caminho do CSV automaticamente.
    Prioriza:
    1) data/raw/noshowappointments.csv
    2) data/noshowappointments.csv
    """

    path_raw = os.path.join("data", "raw", "noshowappointments.csv")
    path_simple = os.path.join("data", "noshowappointments.csv")

    if os.path.exists(path_raw):
        return path_raw

    if os.path.exists(path_simple):
        return path_simple

    raise FileNotFoundError(
        "Arquivo não encontrado.\n"
        "Coloque o CSV do Kaggle em:\n"
        "- data/raw/noshowappointments.csv\n"
        "ou\n"
        "- data/noshowappointments.csv"
    )


def load_data() -> pd.DataFrame:
    """
    Carrega o dataset do Kaggle (No-show appointments) e normaliza
    para modelo executivo em português.
    """

    DATA_PATH = _resolve_path()
    df = pd.read_csv(DATA_PATH)

    # Datas
    df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"], utc=True, errors="coerce")
    df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"], utc=True, errors="coerce")

    out = pd.DataFrame()

    # Identificadores e datas
    out["id_agendamento"] = df["AppointmentID"].astype(int)
    out["data_agendamento"] = df["ScheduledDay"].dt.date
    out["data_consulta"] = df["AppointmentDay"].dt.date

    # Perfil
    out["idade"] = df["Age"].clip(lower=0)
    out["idade_60_mais"] = (out["idade"] >= 60).astype(int)

    # Canal (proxy: SMS recebido)
    out["canal_confirmacao"] = (
        df["SMS_received"]
        .map({1: "SMS", 0: "Sem SMS"})
        .fillna("Sem SMS")
    )

    # Localização (proxy de unidade)
    out["bairro"] = df["Neighbourhood"].astype(str)

    # Especialidade (proxy fixo)
    out["especialidade"] = "Geral"

    # Antecedência (dias e minutos)
    delta_minutes = (
        (df["AppointmentDay"] - df["ScheduledDay"])
        .dt.total_seconds() / 60.0
    )

    delta_minutes = delta_minutes.fillna(0).clip(lower=0)

    out["antecedencia_minutos"] = delta_minutes.round().astype(int)
    out["antecedencia_dias"] = (delta_minutes / (60 * 24)).round().astype(int)

    # Todos são agendados nesse dataset
    out["agendado"] = 1

    # No-show
    out["faltou"] = (
        df["No-show"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
        .fillna(0)
        .astype(int)
    )

    out["compareceu"] = (out["faltou"] == 0).astype(int)

    # Proxy de valor
    out["valor_medio"] = 150.0

    return out
