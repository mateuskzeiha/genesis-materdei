import os
import pandas as pd


def _resolve_path() -> str:
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
    DATA_PATH = _resolve_path()
    df = pd.read_csv(DATA_PATH)

    df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"], utc=True, errors="coerce")
    df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"], utc=True, errors="coerce")

    out = pd.DataFrame()

    # Identificadores e datas
    out["id_agendamento"] = df["AppointmentID"].astype(int)
    out["id_paciente"] = df["PatientId"].fillna(0).astype(float).astype("int64").astype(str)
    out["data_agendamento"] = df["ScheduledDay"].dt.date
    out["data_consulta"] = df["AppointmentDay"].dt.date

    # Hora do agendamento e dia da semana (features para o modelo)
    out["hora_agendamento"] = df["ScheduledDay"].dt.hour.fillna(0).astype(int)
    out["dia_semana"] = df["AppointmentDay"].dt.dayofweek.fillna(0).astype(int)  # 0=Seg, 6=Dom

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

    # Histórico de no-show por paciente: quantas vezes faltou ANTES desta consulta
    # (ordenado cronologicamente para evitar data leakage)
    _tmp = out.sort_values(["id_paciente", "data_agendamento"]).copy()
    _tmp["historico_no_show"] = (
        _tmp.groupby("id_paciente")["faltou"]
        .cumsum()
        .shift(1)
        .fillna(0)
        .astype(int)
    )
    out = out.merge(
        _tmp[["id_agendamento", "historico_no_show"]],
        on="id_agendamento",
        how="left",
    )
    out["historico_no_show"] = out["historico_no_show"].fillna(0).astype(int)

    return out
