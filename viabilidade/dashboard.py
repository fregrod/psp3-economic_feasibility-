"""
=================================================================
DASHBOARD — Visualização Interativa (HTML / Plotly)
=================================================================
Gera um dashboard HTML auto-contido com todos os resultados
da análise de viabilidade econômica.
=================================================================
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from premissas import HORIZONTE_ANOS


# ── Paleta de cores ──────────────────────────────────────────
COLORS = {
    "primary": "#6366f1",       # indigo
    "primary_light": "#818cf8",
    "secondary": "#06b6d4",     # cyan
    "accent": "#f59e0b",        # amber
    "success": "#10b981",       # emerald
    "danger": "#ef4444",        # red
    "bg_dark": "#0f172a",       # slate-900
    "bg_card": "#1e293b",       # slate-800
    "text": "#e2e8f0",          # slate-200
    "text_muted": "#94a3b8",    # slate-400
    "grid": "#334155",          # slate-700
    "gradient_1": "#6366f1",
    "gradient_2": "#8b5cf6",
    "gradient_3": "#a855f7",
}

ANOS = [f"Ano {y+1}" for y in range(HORIZONTE_ANOS)]


def _fmt_brl(valor, suffix=""):
    """Formata valor em BRL com sufixo."""
    if abs(valor) >= 1e9:
        return f"R$ {valor/1e9:,.1f}B{suffix}"
    if abs(valor) >= 1e6:
        return f"R$ {valor/1e6:,.2f}M{suffix}"
    if abs(valor) >= 1e3:
        return f"R$ {valor/1e3:,.0f}k{suffix}"
    return f"R$ {valor:,.0f}{suffix}"


def gerar_dashboard(mercado, receitas, despesas, fluxo, indicadores, opcoes, sensibilidade, cenarios, monte_carlo, ue, solver, output_path):
    """
    Gera o dashboard HTML completo.
    """
    fig = make_subplots(
        rows=7, cols=2,
        subplot_titles=(
            "Dimensionamento de Mercado (TAM · SAM · SOM)",
            "Receita Bruta vs OPEX (R$ milhões)",
            "EBITDA e Margem EBITDA",
            "Fluxo de Caixa Livre e Var. Capital de Giro (R$ milhões)",
            "Árvore Binomial — Opção de Expansão (Call)",
            "Composição do VPL Estratégico",
            "Análise de Sensibilidade: VPL (WACC vs Conversão)",
            "Análise de Cenários: VPL e Payback",
            "Simulação de Monte Carlo (VPL)",
            "Unit Economics (LTV/CAC e Payback)",
            "Mix de Marketing Otimizado (Solver)",
            "Tabela Resumo: Demonstrativo Financeiro Simplificado",
        ),
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy", "secondary_y": True}, {"type": "xy", "secondary_y": True}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "heatmap"}, {"type": "xy", "secondary_y": True}],
            [{"type": "xy", "colspan": 2}, None],
            [{"type": "xy", "secondary_y": True}, {"type": "xy"}],
            [{"type": "table", "colspan": 2}, None],
        ],
        vertical_spacing=0.06,
        horizontal_spacing=0.08,
        row_heights=[0.12, 0.15, 0.12, 0.15, 0.15, 0.15, 0.16],
    )

    # ═══════════════════════════════════════════════════════
    # 1. FUNIL DE MERCADO (TAM / SAM / SOM)
    # ═══════════════════════════════════════════════════════
    market_labels = ["TAM", "SAM", "SOM"]
    market_values = [
        mercado["tam"] / 1e9,
        mercado["sam"] / 1e9,
        mercado["som"] / 1e9,
    ]
    market_colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]

    fig.add_trace(
        go.Bar(
            x=market_labels,
            y=market_values,
            marker_color=market_colors,
            text=[f"R$ {v:,.1f}B" for v in market_values],
            textposition="outside",
            textfont=dict(size=14, color=COLORS["text"]),
            name="Mercado",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # ═══════════════════════════════════════════════════════
    # 2. RECEITA vs OPEX
    # ═══════════════════════════════════════════════════════
    fig.add_trace(
        go.Bar(
            x=ANOS,
            y=receitas["receita_bruta"] / 1e6,
            name="Receita Bruta",
            marker_color=COLORS["primary"],
            text=[f"{v/1e6:.1f}" for v in receitas["receita_bruta"]],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Bar(
            x=ANOS,
            y=despesas["opex_anual"] / 1e6,
            name="OPEX",
            marker_color=COLORS["danger"],
            text=[f"{v/1e6:.1f}" for v in despesas["opex_anual"]],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
        ),
        row=1, col=2,
    )

    # ═══════════════════════════════════════════════════════
    # 3. EBITDA + MARGEM
    # ═══════════════════════════════════════════════════════
    fig.add_trace(
        go.Bar(
            x=ANOS,
            y=fluxo["ebitda"] / 1e6,
            name="EBITDA",
            marker=dict(
                color=COLORS["success"],
                line=dict(width=0),
            ),
            text=[f"{v/1e6:.1f}M" for v in fluxo["ebitda"]],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
        ),
        row=2, col=1, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=ANOS,
            y=fluxo["margem_ebitda"] * 100,
            name="Margem EBITDA (%)",
            mode="lines+markers+text",
            line=dict(color=COLORS["accent"], width=3),
            marker=dict(size=10, color=COLORS["accent"]),
            text=[f"{v:.1f}%" for v in fluxo["margem_ebitda"] * 100],
            textposition="top center",
            textfont=dict(size=11, color=COLORS["accent"]),
        ),
        row=2, col=1, secondary_y=True,
    )

    # ═══════════════════════════════════════════════════════
    # 4. FCL + FCL DESCONTADO + Var. NCG
    # ═══════════════════════════════════════════════════════
    fig.add_trace(
        go.Bar(
            x=ANOS,
            y=fluxo["fcl"] / 1e6,
            name="FCL",
            marker_color=COLORS["primary"],
            text=[f"{v/1e6:.1f}M" for v in fluxo["fcl"]],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
        ),
        row=2, col=2, secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=ANOS,
            y=-fluxo["variacao_ncg"] / 1e6,
            name="Var. Capital de Giro",
            marker_color=COLORS["danger"],
        ),
        row=2, col=2, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=ANOS,
            y=indicadores["fcl_descontado"] / 1e6,
            name="FCL Descontado",
            mode="lines+markers",
            line=dict(color=COLORS["accent"], width=3, dash="dot"),
            marker=dict(size=10, color=COLORS["accent"]),
        ),
        row=2, col=2, secondary_y=True,
    )

    # ═══════════════════════════════════════════════════════
    # 5. ÁRVORE BINOMIAL (EXPANSÃO)
    # ═══════════════════════════════════════════════════════
    tree_s = opcoes["arvore_s_expansao"]
    tree_c = opcoes["arvore_c_expansao"]
    n = 2  # períodos

    # Nós da árvore
    node_x, node_y, node_text = [], [], []
    edge_x, edge_y = [], []

    for i in range(n + 1):
        for j in range(i + 1):
            x_pos = i
            y_pos = (i / 2) - j  # centralizar verticalmente
            s_val = tree_s[j, i]
            c_val = tree_c[j, i]

            node_x.append(x_pos)
            node_y.append(y_pos)
            node_text.append(
                f"S={_fmt_brl(s_val)}<br>C={_fmt_brl(c_val)}"
            )

            # Arestas para o próximo período
            if i < n:
                # Up
                nx_up, ny_up = i + 1, ((i + 1) / 2) - j
                edge_x.extend([x_pos, nx_up, None])
                edge_y.extend([y_pos, ny_up, None])
                # Down
                nx_dn, ny_dn = i + 1, ((i + 1) / 2) - (j + 1)
                edge_x.extend([x_pos, nx_dn, None])
                edge_y.extend([y_pos, ny_dn, None])

    fig.add_trace(
        go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(color=COLORS["text_muted"], width=1.5),
            showlegend=False,
            hoverinfo="skip",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            marker=dict(
                size=35,
                color=COLORS["primary"],
                line=dict(width=2, color=COLORS["primary_light"]),
            ),
            text=[f"S={_fmt_brl(tree_s[j, i])}" for i in range(n+1) for j in range(i+1)],
            textposition="top center",
            textfont=dict(size=9, color=COLORS["text"]),
            hovertext=node_text,
            hoverinfo="text",
            showlegend=False,
        ),
        row=3, col=1,
    )

    # ═══════════════════════════════════════════════════════
    # 6. WATERFALL — VPL ESTRATÉGICO
    # ═══════════════════════════════════════════════════════
    waterfall_labels = [
        "VPL Base",
        "Opção Expansão",
        "Opção Abandono",
        "VPL Estratégico",
    ]
    waterfall_values = [
        opcoes["vpl_base"] / 1e6,
        opcoes["valor_expansao"] / 1e6,
        opcoes["valor_abandono"] / 1e6,
        opcoes["vpl_estrategico"] / 1e6,
    ]

    fig.add_trace(
        go.Waterfall(
            x=waterfall_labels,
            y=waterfall_values,
            measure=["absolute", "relative", "relative", "total"],
            connector=dict(line=dict(color=COLORS["text_muted"], width=1)),
            increasing=dict(marker_color=COLORS["success"]),
            decreasing=dict(marker_color=COLORS["danger"]),
            totals=dict(marker_color=COLORS["primary"]),
            text=[f"R$ {v:,.1f}M" for v in waterfall_values],
            textposition="outside",
            textfont=dict(size=12, color=COLORS["text"]),
            showlegend=False,
        ),
        row=3, col=2,
    )

    # ═══════════════════════════════════════════════════════
    # 7. SENSIBILIDADE E CENÁRIOS (row 4)
    # ═══════════════════════════════════════════════════════
    wacc_r, conv_r, mat_vpl = sensibilidade
    fig.add_trace(
        go.Heatmap(
            z=mat_vpl / 1e6,
            x=[f"{c:.0%}" for c in conv_r],
            y=[f"{w:.1%}" for w in wacc_r],
            colorscale="Viridis",
            text=[[f"R$ {v/1e6:.1f}M" for v in row] for row in mat_vpl],
            texttemplate="%{text}",
            colorbar=dict(title="VPL (M)", x=0.45, y=0.3),
        ),
        row=4, col=1,
    )
    # Atualiza títulos dos eixos do heatmap
    fig.update_xaxes(title_text="Taxa de Conversão", row=4, col=1)
    fig.update_yaxes(title_text="WACC", row=4, col=1)

    cen_names = [c["nome"] for c in cenarios]
    cen_vpl = [c["vpl"] / 1e6 for c in cenarios]
    cen_pbk = [c["payback"] for c in cenarios]
    fig.add_trace(
        go.Bar(
            x=cen_names, y=cen_vpl,
            name="VPL Cenário",
            marker_color=[COLORS["danger"], COLORS["primary"], COLORS["success"]],
            text=[f"R$ {v:.1f}M" for v in cen_vpl],
            textposition="outside"
        ),
        row=4, col=2, secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=cen_names, y=cen_pbk,
            name="Payback (meses)",
            mode="lines+markers+text",
            line=dict(color=COLORS["accent"], width=3),
            text=[f"{p:.1f}m" for p in cen_pbk],
            textposition="top center"
        ),
        row=4, col=2, secondary_y=True
    )
    fig.update_yaxes(title_text="VPL (R$ M)", row=4, col=2, secondary_y=False)
    fig.update_yaxes(title_text="Payback (meses)", row=4, col=2, secondary_y=True)

    # ═══════════════════════════════════════════════════════
    # 8. MONTE CARLO (row 5)
    # ═══════════════════════════════════════════════════════
    vpls_mc = monte_carlo["vpls"] / 1e6
    prob_sucesso = monte_carlo["probabilidade_sucesso"]
    
    fig.add_trace(
        go.Histogram(
            x=vpls_mc,
            nbinsx=50,
            marker_color=COLORS["primary"],
            name="VPL Simulado",
            opacity=0.75,
            showlegend=False
        ),
        row=5, col=1
    )
    # Linha do zero
    fig.add_vline(x=0, line_dash="dash", line_color=COLORS["danger"], row=5, col=1)
    
    # Anotação de probabilidade
    fig.add_annotation(
        x=0.05, y=0.9, xref="x domain", yref="y domain",
        text=f"Prob. VPL > 0: {prob_sucesso:.1%}",
        showarrow=False,
        font=dict(color=COLORS["success"], size=14),
        bgcolor=COLORS["bg_card"],
        bordercolor=COLORS["grid"],
        row=5, col=1
    )
    fig.update_xaxes(title_text="VPL (R$ milhões)", row=5, col=1)
    fig.update_yaxes(title_text="Frequência", row=5, col=1)

    # ═══════════════════════════════════════════════════════
    # 9. UNIT ECONOMICS E SOLVER (row 6)
    # ═══════════════════════════════════════════════════════
    ltv_cac = ue["ltv_cac_ratio"]
    cac_payback = ue["cac_payback_meses"]
    
    fig.add_trace(
        go.Scatter(
            x=ANOS, y=ltv_cac,
            name="LTV / CAC",
            mode="lines+markers+text",
            line=dict(color=COLORS["success"], width=3),
            text=[f"{v:.1f}x" for v in ltv_cac],
            textposition="top center",
        ),
        row=6, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=ANOS, y=cac_payback,
            name="Payback do CAC (meses)",
            marker_color=COLORS["accent"],
            opacity=0.6,
        ),
        row=6, col=1, secondary_y=True
    )
    fig.update_yaxes(title_text="LTV / CAC (x)", row=6, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Meses", row=6, col=1, secondary_y=True)

    # Solver Stacked Bar
    solver_ads = [s["mix_google_ads"] for s in solver]
    solver_out = [s["mix_outbound"] for s in solver]
    solver_evt = [s["mix_feiras"] for s in solver]
    meta_clientes = ue["construtoras_adquiridas"]
    
    fig.add_trace(go.Bar(x=ANOS, y=solver_ads, name="Google Ads", marker_color="#4285F4"), row=6, col=2)
    fig.add_trace(go.Bar(x=ANOS, y=solver_out, name="Outbound", marker_color="#34A853"), row=6, col=2)
    fig.add_trace(go.Bar(x=ANOS, y=solver_evt, name="Feiras", marker_color="#FBBC05"), row=6, col=2)
    
    fig.add_trace(
        go.Scatter(
            x=ANOS, y=meta_clientes,
            name="Meta Original",
            mode="lines+markers",
            line=dict(color=COLORS["danger"], width=2, dash="dash"),
            marker=dict(size=8, symbol="star")
        ),
        row=6, col=2
    )
    fig.update_layout(barmode="stack")

    # ═══════════════════════════════════════════════════════
    # 10. TABELA RESUMO (row 7, full width)
    # ═══════════════════════════════════════════════════════
    header_vals = ["Indicador"] + ANOS
    rb_vals = [_fmt_brl(v) for v in receitas["receita_bruta"]]
    opex_vals = [_fmt_brl(v) for v in despesas["opex_anual"]]
    ncg_vals = [_fmt_brl(v) for v in fluxo["variacao_ncg"]]
    ebitda_vals = [_fmt_brl(v) for v in fluxo["ebitda"]]
    margin_vals = [f"{v:.1%}" for v in fluxo["margem_ebitda"]]
    fcl_vals = [_fmt_brl(v) for v in fluxo["fcl"]]
    fcld_vals = [_fmt_brl(v) for v in indicadores["fcl_descontado"]]

    fig.add_trace(
        go.Table(
            header=dict(
                values=header_vals,
                fill_color=COLORS["primary"],
                font=dict(color="white", size=13),
                align="center",
                height=35,
            ),
            cells=dict(
                values=[
                    ["Receita Bruta", "(−) OPEX", "(−) Var. NCG", "EBITDA", "Margem EBITDA", "FCL Líquido", "FCL Descontado"],
                    *[[rb_vals[y], opex_vals[y], ncg_vals[y], ebitda_vals[y], margin_vals[y], fcl_vals[y], fcld_vals[y]] for y in range(5)],
                ],
                fill_color=[
                    [COLORS["bg_card"]] * 7,
                    *[[COLORS["bg_dark"] if i % 2 == 0 else COLORS["bg_card"] for i in range(7)] for _ in range(5)],
                ],
                font=dict(color=COLORS["text"], size=12),
                align="center",
                height=30,
            ),
        ),
        row=7, col=1,
    )

    # ═══════════════════════════════════════════════════════
    # LAYOUT GLOBAL
    # ═══════════════════════════════════════════════════════
    # KPI annotations
    kpi_data = [
        ("WACC", f"{indicadores['wacc']:.2%}"),
        ("VPL Base", _fmt_brl(indicadores["vpl"])),
        ("TIR", f"{indicadores['tir']:.0%}"),
        ("Payback", f"{indicadores['payback_meses']:.1f} meses"),
        ("VPL Estratégico", _fmt_brl(opcoes["vpl_estrategico"])),
        ("Breakeven", f"{indicadores['breakeven_conversao']:.0%} conv."),
    ]

    annotations = []
    for idx, (label, value) in enumerate(kpi_data):
        x_pos = idx / len(kpi_data) + 0.5 / len(kpi_data)
        annotations.append(
            dict(
                x=x_pos, y=1.08,
                xref="paper", yref="paper",
                text=f"<b>{value}</b><br><span style='font-size:11px;color:{COLORS['text_muted']}'>{label}</span>",
                showarrow=False,
                font=dict(size=18, color=COLORS["accent"]),
                align="center",
            )
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>📊 Viabilidade Econômica — Marketplace de Material de Construção</b>"
                "<br><span style='font-size:14px;color:#94a3b8'>"
                "UnB · Engenharia Econômica · Análise Completa (5 anos)"
                "</span>"
            ),
            font=dict(size=22, color=COLORS["text"]),
            x=0.5,
            y=0.98,
        ),
        annotations=annotations,
        height=3200,
        paper_bgcolor=COLORS["bg_dark"],
        plot_bgcolor=COLORS["bg_dark"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        legend=dict(
            bgcolor="rgba(30,41,59,0.8)",
            bordercolor=COLORS["grid"],
            borderwidth=1,
            font=dict(color=COLORS["text"]),
        ),
        margin=dict(t=160, b=40, l=60, r=40),
        barmode="group",
    )

    # Estilizar eixos
    for i in range(1, 8):
        for j in range(1, 3):
            axis_x = f"xaxis{'' if (i==1 and j==1) else (i-1)*2+j}"
            axis_y = f"yaxis{'' if (i==1 and j==1) else (i-1)*2+j}"

    # Aplicar estilo dark a todos os eixos
    fig.update_xaxes(
        gridcolor=COLORS["grid"],
        linecolor=COLORS["grid"],
        tickfont=dict(color=COLORS["text_muted"]),
    )
    fig.update_yaxes(
        gridcolor=COLORS["grid"],
        linecolor=COLORS["grid"],
        tickfont=dict(color=COLORS["text_muted"]),
    )

    # Títulos dos subplots
    for ann in fig.layout.annotations:
        if hasattr(ann, "font") and ann.font is not None:
            ann.font.color = COLORS["text"]
            ann.font.size = 14

    # Eixo Y2 (margem) range
    fig.update_yaxes(range=[0, 100], row=2, col=1, secondary_y=True,
                     title_text="Margem %", title_font=dict(color=COLORS["accent"]))
    fig.update_yaxes(title_text="R$ milhões", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="R$ milhões", row=2, col=2, secondary_y=False)

    # Remover eixos da árvore binomial
    fig.update_xaxes(visible=False, row=3, col=1)
    fig.update_yaxes(visible=False, row=3, col=1)

    # ── Salvar HTML ───────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(
        output_path,
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "responsive": True},
    )
    return output_path
