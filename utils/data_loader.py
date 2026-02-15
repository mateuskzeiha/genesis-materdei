import os
import pandas as pd

DATA_PATH = os.path.join("data", "noshowappointments.csv")

def load_data() -> pd.DataFrame:
    """
    Carrega o dataset do Kaggle (No-show appointments) e normaliza para um modelo em português,
    pronto para dashboard executivo.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {DATA_PATH}\n"
            "Coloque o CSV do Kaggle em /data com o nome noshowappointments.csv"
        )

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

    # "Canal" aqui é o tipo de confirmação (proxy): recebeu SMS ou não
    out["canal_confirmacao"] = df["SMS_received"].map({1: "SMS", 0: "Sem SMS"}).fillna("Sem SMS")

    # Localização (proxy de unidade): bairro
    out["bairro"] = df["Neighbourhood"].astype(str)

    # Campos que não existem nesse dataset (mantemos para compatibilidade e clareza)
    out["especialidade"] = "Geral"

    # Antecedência (dias) entre agendamento e consulta
    delta_minutes = (df["AppointmentDay"] - df["ScheduledDay"]).dt.total_seconds() / 60.0
    delta_minutes = delta_minutes.fillna(0).clip(lower=0)

    out["antecedencia_minutos"] = delta_minutes.round().astype(int)
    out["antecedencia_dias"] = (delta_minutes / (60 * 24)).round().astype(int)

    # No Kaggle, todos já são agendados (não existe etapa de "interessado")
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

    # Valor não existe no Kaggle → proxy (ajustável no futuro)
    out["valor_medio"] = 150.0

    return out
