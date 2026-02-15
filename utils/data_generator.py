import numpy as np
import pandas as pd

def generate_synthetic_dataset(n: int = 20000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    channels = ["WhatsApp", "Call Center", "Site/App", "Presencial"]
    units = ["Santo Agostinho", "Contorno", "Salvador", "Goiânia", "Uberlândia"]
    specialties = ["Cardio", "Ortopedia", "Dermato", "Endócrino", "Gastro", "Neuro", "Gineco", "Oftalmo", "Ressonância", "Tomografia"]

    # Perfil
    age = rng.integers(18, 85, size=n)
    is_60_plus = (age >= 60).astype(int)

    channel = rng.choice(channels, size=n, p=[0.35, 0.30, 0.25, 0.10])
    unit = rng.choice(units, size=n, p=[0.28, 0.22, 0.18, 0.16, 0.16])
    specialty = rng.choice(specialties, size=n)

    # Tempo de resposta (min) — canal influencia
    base_rt = rng.normal(loc=12, scale=6, size=n).clip(1, 60)
    rt_multiplier = np.where(channel == "WhatsApp", 0.9, 1.0)
    rt_multiplier = np.where(channel == "Call Center", 1.05, rt_multiplier)
    rt_multiplier = np.where(channel == "Site/App", 1.15, rt_multiplier)
    response_minutes = (base_rt * rt_multiplier).clip(1, 120).round().astype(int)

    # Data
    start = np.datetime64("2026-01-01")
    created_offset = rng.integers(0, 45, size=n)
    created_date = start + created_offset.astype("timedelta64[D]")

    days_ahead = rng.integers(0, 30, size=n)  # antecedência do agendamento (pra quem agenda)
    appointment_date = created_date + days_ahead.astype("timedelta64[D]")

    # Preço (consulta/exame) por especialidade
    base_price_map = {
        "Cardio": 250, "Ortopedia": 240, "Dermato": 260, "Endócrino": 230,
        "Gastro": 260, "Neuro": 320, "Gineco": 220, "Oftalmo": 210,
        "Ressonância": 600, "Tomografia": 480
    }
    price = np.array([base_price_map[s] for s in specialty]) + rng.normal(0, 20, size=n)
    price = price.clip(150, 900).round(0)

    # Probabilidade de agendar (conversão) — base ~35%
    # Pior para 60+ no app, pior com tempo de resposta alto, algumas especialidades mais “sensíveis”
    p = np.full(n, 0.35)

    p -= (response_minutes > 20) * 0.08
    p -= (response_minutes > 35) * 0.10

    p -= ((channel == "Site/App") & (is_60_plus == 1)) * 0.10
    p += (channel == "WhatsApp") * 0.03

    p -= (specialty == "Ressonância") * 0.03
    p -= (specialty == "Tomografia") * 0.02
    p += (specialty == "Dermato") * 0.02

    p = np.clip(p, 0.05, 0.85)
    scheduled = (rng.random(n) < p).astype(int)

    # No-show para agendados — base ~13%
    # Aumenta com antecedência alta, 60+, certas especialidades/turnos (proxy)
    base_ns = np.full(n, 0.13)
    base_ns += (days_ahead >= 10) * 0.06
    base_ns += (is_60_plus == 1) * 0.03
    base_ns += (specialty == "Ressonância") * 0.04
    base_ns += (specialty == "Tomografia") * 0.03
    base_ns += (channel == "Call Center") * 0.01

    base_ns = np.clip(base_ns, 0.03, 0.45)
    no_show = ((rng.random(n) < base_ns) & (scheduled == 1)).astype(int)

    attended = ((scheduled == 1) & (no_show == 0)).astype(int)

    # Etapas do funil (simplificado)
    stages = np.array(["Interesse", "Contato", "Oferta Agenda", "Confirmação", "Agendamento"])
    stage_probs = [0.20, 0.25, 0.25, 0.15, 0.15]
    stage = rng.choice(stages, size=n, p=stage_probs)
    # Quem agendou está na etapa Agendamento
    stage = np.where(scheduled == 1, "Agendamento", stage)

    df = pd.DataFrame({
        "lead_id": np.arange(1, n + 1),
        "created_date": created_date.astype("datetime64[D]"),
        "appointment_date": appointment_date.astype("datetime64[D]"),
        "age": age,
        "is_60_plus": is_60_plus,
        "channel": channel,
        "unit": unit,
        "specialty": specialty,
        "stage": stage,
        "response_minutes": response_minutes,
        "days_ahead": days_ahead,
        "scheduled": scheduled,
        "attended": attended,
        "no_show": no_show,
        "price": price,
    })

    return df
