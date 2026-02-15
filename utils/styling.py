import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go


# Cor padrão solicitada (títulos e identidade)
TITLE_GREEN = "#089489"

# Paleta complementar (discreta, Mater Dei vibe)
GREEN_LIGHT = "#BFECE6"
GREEN_MID = "#4ABFA1"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "rgba(31,41,55,0.70)"

# Fundo: majoritariamente branco com verde leve no canto
BG_GRADIENT = (
    "linear-gradient(135deg, "
    "rgba(255,255,255,1) 0%, "
    "rgba(255,255,255,1) 60%, "
    "rgba(8,148,137,0.10) 100%)"
)


def _apply_plotly_template():
    """
    Template global Plotly (aplica em TODOS os gráficos):
    - fundo transparente (paper/plot)
    - tipografia escura (pra fundo claro)
    - título em #089489
    - grid bem suave
    - paleta puxada pro verde
    """

    template = go.layout.Template()

    template.layout = go.Layout(
        # Transparência real
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        # Fonte padrão (escura, porque o app agora é claro)
        font=dict(color=TEXT_DARK, size=12),

        # Título dos gráficos (cor solicitada)
        title=dict(font=dict(size=16, color=TITLE_GREEN)),

        # Paleta (verde first)
        colorway=[
            TITLE_GREEN,
            GREEN_MID,
            "#2F8F7B",
            "#76D7C4",
            "#1F6F61",
        ],

        # Grid e eixos bem leves
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(31,41,55,0.10)",
            zeroline=False,
            showline=True,
            linecolor="rgba(31,41,55,0.18)",
            tickfont=dict(color="rgba(31,41,55,0.82)"),
            title=dict(font=dict(color=TEXT_DARK)),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(31,41,55,0.10)",
            zeroline=False,
            showline=True,
            linecolor="rgba(31,41,55,0.18)",
            tickfont=dict(color="rgba(31,41,55,0.82)"),
            title=dict(font=dict(color=TEXT_DARK)),
        ),

        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_DARK),
        ),

        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="rgba(31,41,55,0.16)",
            font=dict(color=TEXT_DARK),
        ),

        margin=dict(l=10, r=10, t=60, b=10),
    )

    pio.templates["genesis_materdei_light"] = template
    pio.templates.default = "genesis_materdei_light"


def apply_global_style():
    _apply_plotly_template()

    st.markdown(
        f"""
        <style>
            /* Fundo geral (majoritariamente branco) */
            .stApp {{
                background: {BG_GRADIENT};
            }}

            /* Container */
            .block-container {{
                padding-top: 1.8rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }}

            /* Sidebar clara */
            section[data-testid="stSidebar"] > div {{
                background: rgba(255,255,255,0.72);
                border-right: 1px solid rgba(31,41,55,0.10);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }}

            /* Títulos das páginas (cor #089489) */
            h1, h2, h3 {{
                color: {TITLE_GREEN} !important;
                letter-spacing: -0.2px;
            }}

            /* Textos */
            p, span, li {{
                color: {TEXT_MUTED};
            }}

            /* Cards acrílico */
            div[data-testid="stMetric"] {{
                background: rgba(255,255,255,0.55);
                border: 1px solid rgba(31,41,55,0.10);
                border-radius: 14px;
                padding: 12px;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }}

            /* Tabs */
            button[role="tab"] {{
                border-radius: 10px !important;
            }}
            button[role="tab"][aria-selected="true"] {{
                background: rgba(8,148,137,0.10) !important;
                border: 1px solid rgba(8,148,137,0.20) !important;
            }}

            /* --- CRÍTICO: forçar plotly transparente (evita fundo branco) --- */
            .js-plotly-plot, .plot-container, .svg-container {{
                background: transparent !important;
            }}
            .js-plotly-plot .plotly .main-svg {{
                background: transparent !important;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )
