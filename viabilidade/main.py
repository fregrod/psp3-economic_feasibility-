#!/usr/bin/env python3
"""
=================================================================
MAIN — Viabilidade Econômica: Marketplace de Material de Construção
=================================================================
Script principal que orquestra todos os módulos, imprime resultados
no terminal e gera o dashboard HTML interativo.

Uso:
    python3 viabilidade/main.py

Saída:
    output/dashboard_viabilidade.html
=================================================================
"""
import os
import sys

# Garantir que os módulos locais sejam encontrados
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    WACC, CAPEX_TOTAL, FEE_MARKETPLACE, TAXA_CONVERSAO,
    TOTAL_OBRAS_ANO_BRASIL, GASTO_MATERIAIS_POR_OBRA,
    PAVIMENTOS_MEDIO_POR_OBRA, AREA_POR_PAVIMENTO_M2,
    CUSTO_MEDIO_M2, PCT_CUSTO_MATERIAIS, FEE_POR_OBRA,
    HORIZONTE_ANOS, DEDUCOES_RECEITA, DEPRECIACAO_ANUAL,
    IPCA_2025, TAXA_LIVRE_RISCO, EQUITY_RISK_PREMIUM,
    COUNTRY_RISK_PREMIUM, PREMIO_STARTUP, BETA_ALAVANCADO,
    CUSTO_EQUITY, AREA_TOTAL_MEDIA,
)
from mercado import calcular_mercado
from receitas import calcular_receitas
from despesas import calcular_despesas
from fluxo_caixa import calcular_fluxo_caixa
from indicadores import calcular_indicadores
from opcoes_reais import calcular_opcoes_reais
from cenarios_sensibilidade import gerar_matriz_sensibilidade, gerar_cenarios, simulacao_monte_carlo
from unit_economics import calcular_unit_economics
from otimizacao_solver import otimizar_mix_marketing
from dashboard import gerar_dashboard


def _sep(title=""):
    print()
    print("━" * 72)
    if title:
        print(f"  {title}")
        print("━" * 72)


def _fmt(v, div=1e6, pre="R$ ", suf="M", fmt=".2f"):
    return f"{pre}{v/div:{fmt}}{suf}"


def main():
    # ══════════════════════════════════════════════════════
    # 1. PREMISSAS
    # ══════════════════════════════════════════════════════
    _sep("1. PREMISSAS DO PROJETO")

    print(f"\n  ── Mercado ──")
    print(f"  Total obras / ano:         {TOTAL_OBRAS_ANO_BRASIL:,}")
    print(f"  Pavimentos médios:         {PAVIMENTOS_MEDIO_POR_OBRA}")
    print(f"  Área por pavimento:        {AREA_POR_PAVIMENTO_M2:,} m²")
    print(f"  Área total média:          {AREA_TOTAL_MEDIA:,.0f} m²")
    print(f"  Custo / m²:                R$ {CUSTO_MEDIO_M2:,}")
    print(f"  % materiais:               {PCT_CUSTO_MATERIAIS:.0%}")
    print(f"  Gasto materiais / obra:    {_fmt(GASTO_MATERIAIS_POR_OBRA, 1, suf='')}")

    print(f"\n  ── Marketplace ──")
    print(f"  Fee:                       {FEE_MARKETPLACE:.1%}")
    print(f"  Fee / obra:                {_fmt(FEE_POR_OBRA, 1, suf='')}")
    print(f"  Taxa de conversão:         {TAXA_CONVERSAO:.0%}")

    print(f"\n  ── Custo de Capital (CAPM) ──")
    print(f"  IPCA 2025:                 {IPCA_2025:.2%}   (IBGE)")
    print(f"  Taxa livre de risco (Rf):  {TAXA_LIVRE_RISCO:.2%}   (BCB / B3)")
    print(f"  Equity Risk Premium:       {EQUITY_RISK_PREMIUM:.2%}   (Damodaran)")
    print(f"  Country Risk Premium:      {COUNTRY_RISK_PREMIUM:.2%}   (Damodaran)")
    print(f"  Prêmio startup:            {PREMIO_STARTUP:.2%}   (premissa)")
    print(f"  Beta alavancado:           {BETA_ALAVANCADO:.2f}   (calculado)")
    print(f"  ─────────────────────────────────")
    print(f"  Ke = Rf + β(ERP+CRP) + prêmio")
    print(f"  Ke = {TAXA_LIVRE_RISCO:.2%} + {BETA_ALAVANCADO}×({EQUITY_RISK_PREMIUM:.2%}+{COUNTRY_RISK_PREMIUM:.2%}) + {PREMIO_STARTUP:.2%}")
    print(f"  WACC = Ke =                {CUSTO_EQUITY:.2%}")

    print(f"\n  ── Investimento ──")
    print(f"  CAPEX:                     {_fmt(CAPEX_TOTAL, 1, suf='')}")
    print(f"  Depreciação / ano:         {_fmt(DEPRECIACAO_ANUAL, 1, suf='')}")
    print(f"  Horizonte:                 {HORIZONTE_ANOS} anos")

    # ══════════════════════════════════════════════════════
    # 2. MERCADO
    # ══════════════════════════════════════════════════════
    _sep("2. DIMENSIONAMENTO DE MERCADO")
    m = calcular_mercado()

    print(f"\n  TAM (Total):               {_fmt(m['tam'], 1e9, suf='B')}")
    print(f"    = {TOTAL_OBRAS_ANO_BRASIL:,} obras × R$ {GASTO_MATERIAIS_POR_OBRA:,.0f}")
    print(f"\n  SAM (Endereçável, 20%):    {_fmt(m['sam'], 1e9, suf='B')}")
    print(f"    = {m['pct_obras_formais']:.0%} do TAM (obras formais)")
    print(f"\n  SOM (Meta 5 anos, 5%):     {_fmt(m['som'], 1e9, suf='B')}")
    print(f"    = {m['pct_som_sobre_tam']:.0%} do TAM")

    # ══════════════════════════════════════════════════════
    # 3. RECEITAS
    # ══════════════════════════════════════════════════════
    _sep("3. PROJEÇÃO DE RECEITAS")
    r = calcular_receitas()

    print(f"\n  Fee / obra = R$ {GASTO_MATERIAIS_POR_OBRA:,.0f} × {FEE_MARKETPLACE:.1%} = R$ {FEE_POR_OBRA:,.2f}")
    print(f"  Deduções (PIS+COFINS+ISS): {DEDUCOES_RECEITA:.2%}\n")

    print(f"  {'Ano':<8} {'Obras':>8} {'Rec. Bruta':>14} {'Deduções':>12} {'Rec. Líq.':>14} {'COGS':>10}")
    print(f"  {'─'*8} {'─'*8} {'─'*14} {'─'*12} {'─'*14} {'─'*10}")
    for y in range(HORIZONTE_ANOS):
        print(
            f"  Ano {y+1:<3} {r['obras_por_ano'][y]:>8,.0f} "
            f"{_fmt(r['receita_bruta'][y]):>14} "
            f"{_fmt(r['deducoes'][y], 1e3, suf='k'):>12} "
            f"{_fmt(r['receita_liquida'][y]):>14} "
            f"{_fmt(r['cogs_anual'][y], 1e3, suf='k'):>10}"
        )

    # ══════════════════════════════════════════════════════
    # 4. DESPESAS E INVESTIMENTO INICIAL
    # ══════════════════════════════════════════════════════
    _sep("4. DESPESAS E INVESTIMENTO INICIAL")
    d = calcular_despesas()

    print(f"\n  ── Investimento Inicial (Ano 0) ──")
    print(f"  CAPEX Tangível:            {_fmt(d['capex_tangivel'], 1, suf='')}")
    print(f"  OPEX Pré-operacional:      {_fmt(d['opex_pre_operacional'], 1, suf='')}  (6 meses Fase 1)")
    print(f"  Total Investido:           {_fmt(d['investimento_inicial'], 1, suf='')}")

    print(f"\n  {'Ano':<8} {'OPEX':>12} {'COGS':>10} {'Total':>12}")
    print(f"  {'─'*8} {'─'*12} {'─'*10} {'─'*12}")
    for y in range(HORIZONTE_ANOS):
        print(
            f"  Ano {y+1:<3} "
            f"{_fmt(d['opex_anual'][y]):>12} "
            f"{_fmt(d['cogs_anual'][y], 1e3, suf='k'):>10} "
            f"{_fmt(d['custos_totais'][y]):>12}"
        )

    # ══════════════════════════════════════════════════════
    # 5. FLUXO DE CAIXA LIVRE
    # ══════════════════════════════════════════════════════
    _sep("5. FLUXO DE CAIXA LIVRE (FCL)")
    fc = calcular_fluxo_caixa(r, d)

    print(f"\n  {'':>16} ", end="")
    for y in range(HORIZONTE_ANOS):
        print(f"{'Ano ' + str(y+1):>12}", end=" ")
    print()
    print(f"  {'─'*16} " + "─" * 12 * HORIZONTE_ANOS)

    rows = [
        ("Receita Bruta", fc["receita_bruta"]),
        ("(−) Deduções", r["deducoes"]),
        ("Rec. Líquida", fc["receita_liquida"]),
        ("(−) OPEX", fc["opex"]),
        ("(−) COGS", fc["cogs"]),
        ("= EBITDA", fc["ebitda"]),
        ("(−) Deprec.", fc["depreciacao"]),
        ("= LAJIR", fc["lajir"]),
        ("(−) IR/CSLL", fc["ir_csll"]),
        ("= NOPAT", fc["nopat"]),
        ("(+) Deprec.", fc["depreciacao"]),
        ("(−) Var. NCG", fc["variacao_ncg"]),
        ("= FCL", fc["fcl"]),
    ]
    for label, arr in rows:
        print(f"  {label:<16} ", end="")
        for v in arr:
            print(f"{_fmt(v):>12}", end=" ")
        print()

    print(f"\n  Margem EBITDA:  ", end="")
    for v in fc["margem_ebitda"]:
        print(f"{v:>12.1%}", end=" ")
    print()

    # ══════════════════════════════════════════════════════
    # 6. INDICADORES
    # ══════════════════════════════════════════════════════
    _sep("6. INDICADORES FINANCEIROS")
    ind = calcular_indicadores(fc)

    print(f"\n  WACC (TMA):              {ind['wacc']:.2%}")
    print(f"  VPL (base):              {_fmt(ind['vpl'])}")
    print(f"  TIR:                     {ind['tir']:.2%}")
    print(f"  TIR > WACC?              {'✓ SIM — projeto viável' if ind['tir'] > ind['wacc'] else '✗ NÃO'}")
    print(f"  Payback:                 {ind['payback_meses']:.1f} meses")
    print(f"  Payback descontado:      {ind['payback_desc_anos']:.2f} anos")
    print(f"  Breakeven conversão:     {ind['breakeven_conversao']:.0%}")

    print(f"\n  FCL Descontado:")
    for y in range(HORIZONTE_ANOS):
        print(f"    Ano {y+1}: {_fmt(ind['fcl_descontado'][y])}")

    # ══════════════════════════════════════════════════════
    # 7. OPÇÕES REAIS
    # ══════════════════════════════════════════════════════
    _sep("7. OPÇÕES REAIS — Modelo Binomial")
    op = calcular_opcoes_reais(ind["vpl"], fc["fcl"][0])

    print(f"\n  ── Parâmetros ──")
    print(f"  Volatilidade (σ):        {op['volatilidade']:.0%}")
    print(f"  u = e^σ:                 {op['fator_alta']:.4f}")
    print(f"  d = 1/u:                 {op['fator_baixa']:.4f}")
    print(f"  p (neutra ao risco):     {op['prob_neutra_risco']:.4f}")

    print(f"\n  ── Opção de Expansão (Call) ──")
    print(f"  Exercício: Ano 2 → MG + RJ")
    print(f"  S₀ = 50% × VPL base:    {_fmt(op['s0_expansao'])}")
    print(f"  X  (investimento):       {_fmt(op['x_expansao'])}")
    print(f"  Valor da opção:          {_fmt(op['valor_expansao'])}")

    print(f"\n  ── Opção de Abandono (Put americana) ──")
    print(f"  Exercício: Ano 1 → vender por R$ 3M")
    print(f"  S₀ (valor em risco):     {_fmt(op['s0_abandono'], 1e3, suf='k')}")
    print(f"  X  (resgate):            {_fmt(op['x_abandono'])}")
    print(f"  Valor da opção:          {_fmt(op['valor_abandono'])}")

    print(f"\n  ── VPL Estratégico ──")
    print(f"  VPL base:                {_fmt(op['vpl_base'])}")
    print(f"  + Opção Expansão:        {_fmt(op['valor_expansao'])}")
    print(f"  + Opção Abandono:        {_fmt(op['valor_abandono'])}")
    print(f"  ─────────────────────────")
    print(f"  = VPL Estratégico:       {_fmt(op['vpl_estrategico'])}")
    print(f"    (+{op['pct_sobre_base']:.0%} sobre VPL base)")

    # ══════════════════════════════════════════════════════
    # 8. SENSIBILIDADE E CENÁRIOS
    # ══════════════════════════════════════════════════════
    _sep("8. SENSIBILIDADE E CENÁRIOS")
    
    sensibilidade = gerar_matriz_sensibilidade()
    cenarios = gerar_cenarios()
    monte_carlo = simulacao_monte_carlo(n_iter=2000)
    
    print(f"\n  ── Cenários de Viabilidade ──")
    for c in cenarios:
        print(f"  {c['nome']:<12} | Conv: {c['conversao']:.0%} | VPL: {_fmt(c['vpl']):>12} | Payback: {c['payback']:.1f}m")

    print(f"\n  ── Simulação de Monte Carlo (2.000 iterações) ──")
    print(f"  Probabilidade de Sucesso (VPL > 0): {monte_carlo['probabilidade_sucesso']:.1%}")
    print(f"  VPL Médio Esperado:                 {_fmt(monte_carlo['vpl_medio'])}")

    # ══════════════════════════════════════════════════════
    # 9. UNIT ECONOMICS E OTIMIZAÇÃO (SOLVER)
    # ══════════════════════════════════════════════════════
    _sep("9. UNIT ECONOMICS E OTIMIZAÇÃO (SOLVER)")
    
    ue = calcular_unit_economics(d)
    solver = otimizar_mix_marketing(ue["budget_marketing"])
    
    print(f"\n  LTV Estimado (Vida útil 5 anos): {_fmt(ue['ltv'])}")
    for r_s in solver:
        y = r_s["ano"] - 1
        print(f"\n  Ano {r_s['ano']}:")
        print(f"    Meta vs Solver: {ue['construtoras_adquiridas'][y]:.0f} vs {r_s['clientes_maximos']} clientes")
        print(f"    LTV / CAC:      {ue['ltv_cac_ratio'][y]:.1f}x  (Payback: {ue['cac_payback_meses'][y]:.1f}m)")
        print(f"    Mix de MKT:     {r_s['mix_google_ads']} Ads | {r_s['mix_outbound']} Outbound | {r_s['mix_feiras']} Feiras")

    # ══════════════════════════════════════════════════════
    # 10. DASHBOARD
    # ══════════════════════════════════════════════════════
    _sep("10. GERANDO DASHBOARD")

    project_root = os.path.dirname(os.path.dirname(__file__))
    output_path = os.path.join(project_root, "output", "dashboard_viabilidade.html")

    path = gerar_dashboard(m, r, d, fc, ind, op, sensibilidade, cenarios, monte_carlo, ue, solver, output_path)
    print(f"\n  ✅ Dashboard salvo em: {path}")
    print(f"  → Abra no navegador para visualização interativa")

    _sep("ANÁLISE CONCLUÍDA")
    print(f"\n  Decisão: {'✓ PROJETO VIÁVEL' if ind['vpl'] > 0 else '✗ PROJETO INVIÁVEL'}")
    print(f"  VPL = {_fmt(ind['vpl'])} > 0  ∧  TIR = {ind['tir']:.0%} > WACC = {ind['wacc']:.0%}")
    print(f"  VPL Estratégico (com opções): {_fmt(op['vpl_estrategico'])}")
    print()


if __name__ == "__main__":
    main()
