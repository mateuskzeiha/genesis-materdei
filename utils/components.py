"""
Componentes HTML reutilizáveis para o dashboard Genesis.
Todos retornam strings HTML prontas para st.markdown(..., unsafe_allow_html=True).
"""

# ── Paleta ────────────────────────────────────────────────────────────────────
PRIMARY   = "#089489"
GREEN_MID = "#4ABFA1"
GREEN_LT  = "#BFECE6"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"

RISK_COLORS = {
    "ALTO":     {"border": "#d32f2f", "bg": "#fff5f5", "text": "#d32f2f", "emoji": "🔴"},
    "MODERADO": {"border": "#f57c00", "bg": "#fff8f0", "text": "#f57c00", "emoji": "🟠"},
    "BAIXO":    {"border": "#388e3c", "bg": "#f5fff5", "text": "#388e3c", "emoji": "🟢"},
}


# ── KPI Card ──────────────────────────────────────────────────────────────────

def kpi_card(icon: str, label: str, value: str, sublabel: str = "",
             color: str = PRIMARY, width: str = "100%") -> str:
    sub = f'<div class="genesis-kpi-sub">{sublabel}</div>' if sublabel else ""
    return f"""
<div class="genesis-kpi-card" style="border-top:3px solid {color}; width:{width};">
  <div class="genesis-kpi-icon">{icon}</div>
  <div class="genesis-kpi-label">{label}</div>
  <div class="genesis-kpi-value" style="color:{color};">{value}</div>
  {sub}
</div>"""


def kpi_row(cards: list[str]) -> str:
    """Agrupa múltiplos kpi_card() numa linha flexível."""
    inner = "".join(cards)
    return f'<div class="genesis-kpi-row">{inner}</div>'


# ── Risk Badge ────────────────────────────────────────────────────────────────

def risk_badge(faixa: str) -> str:
    c = RISK_COLORS.get(faixa.upper(), {"border": "#888", "bg": "#f5f5f5", "text": "#888", "emoji": "⚪"})
    return (
        f'<span style="background:{c["bg"]}; color:{c["text"]}; '
        f'border:1px solid {c["text"]}; border-radius:6px; '
        f'padding:2px 10px; font-size:0.82em; font-weight:700; white-space:nowrap;">'
        f'{c["emoji"]} {faixa.upper()}</span>'
    )


# ── Blocos de Protocolo (3 colunas visuais) ───────────────────────────────────

def protocol_blocks() -> str:
    return """
<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin:12px 0 20px 0;">

  <div style="border:2px solid #388e3c; border-radius:14px; padding:20px;
              background:linear-gradient(135deg,#f5fff5,#e8f8e8); text-align:center;">
    <div style="font-size:2em; margin-bottom:6px;">🟢</div>
    <div style="font-size:1.1em; font-weight:700; color:#388e3c; margin-bottom:10px;">BAIXO RISCO</div>
    <div style="font-size:1.6em; font-weight:800; color:#388e3c; margin-bottom:8px;">&lt; 30%</div>
    <hr style="border:none; border-top:1px solid #c8e6c9; margin:10px 0;">
    <div style="font-size:0.95em; color:#2e7d32; margin:4px 0;">📱 <b>Canal:</b> SMS</div>
    <div style="font-size:0.95em; color:#2e7d32; margin:4px 0;">⏰ <b>Timing:</b> 24h antes</div>
    <div style="font-size:0.95em; color:#2e7d32; margin:4px 0;">💰 <b>Custo:</b> R$ 0,10/msg</div>
    <div style="margin-top:10px; background:#c8e6c9; border-radius:8px; padding:6px;
                font-size:0.85em; color:#1b5e20; font-weight:600;">Lembrete automático</div>
  </div>

  <div style="border:2px solid #f57c00; border-radius:14px; padding:20px;
              background:linear-gradient(135deg,#fff8f0,#fdebd0); text-align:center;">
    <div style="font-size:2em; margin-bottom:6px;">🟠</div>
    <div style="font-size:1.1em; font-weight:700; color:#f57c00; margin-bottom:10px;">RISCO MODERADO</div>
    <div style="font-size:1.6em; font-weight:800; color:#f57c00; margin-bottom:8px;">30–60%</div>
    <hr style="border:none; border-top:1px solid #ffe0b2; margin:10px 0;">
    <div style="font-size:0.95em; color:#e65100; margin:4px 0;">💬 <b>Canal:</b> WhatsApp</div>
    <div style="font-size:0.95em; color:#e65100; margin:4px 0;">⏰ <b>Timing:</b> 48h antes</div>
    <div style="font-size:0.95em; color:#e65100; margin:4px 0;">💰 <b>Custo:</b> R$ 0,50/msg</div>
    <div style="margin-top:10px; background:#ffe0b2; border-radius:8px; padding:6px;
                font-size:0.85em; color:#bf360c; font-weight:600;">Confirmação ativa (bot)</div>
  </div>

  <div style="border:2px solid #d32f2f; border-radius:14px; padding:20px;
              background:linear-gradient(135deg,#fff5f5,#fce4e4); text-align:center;">
    <div style="font-size:2em; margin-bottom:6px;">🔴</div>
    <div style="font-size:1.1em; font-weight:700; color:#d32f2f; margin-bottom:10px;">ALTO RISCO</div>
    <div style="font-size:1.6em; font-weight:800; color:#d32f2f; margin-bottom:8px;">&gt; 60%</div>
    <hr style="border:none; border-top:1px solid #ffcdd2; margin:10px 0;">
    <div style="font-size:0.95em; color:#c62828; margin:4px 0;">📞 <b>Canal:</b> Ligação</div>
    <div style="font-size:0.95em; color:#c62828; margin:4px 0;">⏰ <b>Timing:</b> 72h antes</div>
    <div style="font-size:0.95em; color:#c62828; margin:4px 0;">💰 <b>Custo:</b> R$ 8,00/chamada</div>
    <div style="margin-top:10px; background:#ffcdd2; border-radius:8px; padding:6px;
                font-size:0.85em; color:#b71c1c; font-weight:600;">Contato humano (analista)</div>
  </div>

</div>"""


# ── Patient Card ──────────────────────────────────────────────────────────────

def patient_card(id_mask: str, idade: int, risco_pct: float,
                 antecedencia: int, canal: str) -> str:
    faixa = "ALTO" if risco_pct >= 60 else ("MODERADO" if risco_pct >= 30 else "BAIXO")
    c = RISK_COLORS[faixa]
    acoes = {
        "ALTO":     "📞 Ligação humana — contato direto (72h antes)",
        "MODERADO": "💬 WhatsApp — confirmação ativa (48h antes)",
        "BAIXO":    "📱 SMS — lembrete padrão (24h antes)",
    }
    acao = acoes[faixa]

    return f"""
<div style="border:2px solid {c['border']}; border-radius:14px; padding:22px;
     background:linear-gradient(135deg,{c['bg']},{c['bg']}); max-width:520px;
     box-shadow:0 2px 12px rgba(0,0,0,0.07);">
  <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
    <div style="font-size:2em;">{c['emoji']}</div>
    <div>
      <div style="font-size:1.1em; font-weight:700; color:{TEXT_DARK};">Paciente {id_mask} · {idade} anos</div>
      <div>{risk_badge(faixa)}</div>
    </div>
  </div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px;">
    <div style="background:rgba(255,255,255,0.7); border-radius:8px; padding:10px; text-align:center;">
      <div style="font-size:0.78em; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:.5px;">Risco no-show</div>
      <div style="font-size:1.8em; font-weight:800; color:{c['border']}; line-height:1.1;">{risco_pct:.1f}%</div>
    </div>
    <div style="background:rgba(255,255,255,0.7); border-radius:8px; padding:10px; text-align:center;">
      <div style="font-size:0.78em; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:.5px;">Antecedência</div>
      <div style="font-size:1.8em; font-weight:800; color:{TEXT_DARK}; line-height:1.1;">{antecedencia}d</div>
    </div>
  </div>
  <div style="background:rgba(255,255,255,0.6); border-radius:8px; padding:10px; margin-bottom:12px;">
    <span style="font-size:0.85em; color:{TEXT_MUTED};">Canal atual: </span>
    <span style="font-weight:600; color:{TEXT_DARK};">{canal}</span>
  </div>
  <div style="background:{c['border']}; color:#fff; border-radius:8px; padding:12px;
       font-size:0.95em; font-weight:600; text-align:center;">
    ✅ {acao}
  </div>
</div>"""


# ── Genesis Header ────────────────────────────────────────────────────────────

def genesis_header() -> str:
    return f"""
<div style="display:flex; align-items:center; gap:16px; padding:18px 0 10px 0;
     border-bottom:2px solid {GREEN_LT}; margin-bottom:8px;">
  <div style="width:48px; height:48px; background:linear-gradient(135deg,{PRIMARY},{GREEN_MID});
       border-radius:12px; display:flex; align-items:center; justify-content:center;
       font-size:1.6em; flex-shrink:0;">🏥</div>
  <div>
    <div translate="no" style="font-size:1.6em; font-weight:800; color:{PRIMARY}; line-height:1.1;
         letter-spacing:-0.5px;">Genesis</div>
    <div style="font-size:0.85em; color:{TEXT_MUTED};">
      Redução de No-show &amp; Eficiência de Agenda &nbsp;·&nbsp; Mater Dei &nbsp;·&nbsp; Sprint 3
    </div>
  </div>
</div>"""


# ── Alert Banner ──────────────────────────────────────────────────────────────

def alert_banner(taxa: float) -> str:
    if taxa > 0.20:
        return (
            f'<div style="background:#fff5f5; border-left:4px solid #d32f2f; border-radius:0 8px 8px 0; '
            f'padding:12px 16px; margin:8px 0 16px 0;">'
            f'<span style="font-weight:700; color:#d32f2f;">⚠️ Alerta crítico:</span> '
            f'<span style="color:#c62828;">Taxa de no-show em <b>{taxa:.1%}</b> — acima do limite de 20%. '
            f'Ative o protocolo de intervenção na aba <b>Act</b>.</span></div>'
        )
    if taxa > 0.15:
        return (
            f'<div style="background:#fff8f0; border-left:4px solid #f57c00; border-radius:0 8px 8px 0; '
            f'padding:12px 16px; margin:8px 0 16px 0;">'
            f'<span style="font-weight:700; color:#f57c00;">⚠️ Atenção:</span> '
            f'<span style="color:#e65100;">Taxa de no-show em <b>{taxa:.1%}</b> — monitorar tendência.</span></div>'
        )
    return (
        f'<div style="background:#f5fff5; border-left:4px solid #388e3c; border-radius:0 8px 8px 0; '
        f'padding:12px 16px; margin:8px 0 16px 0;">'
        f'<span style="font-weight:700; color:#388e3c;">✅ Normal:</span> '
        f'<span style="color:#2e7d32;">Taxa de no-show em <b>{taxa:.1%}</b> — dentro da faixa aceitável.</span></div>'
    )
