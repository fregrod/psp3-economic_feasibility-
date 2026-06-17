"""
=================================================================
INDICADORES FINANCEIROS — VPL, TIR, Payback, Breakeven
=================================================================
Calcula os principais indicadores de viabilidade do projeto.
=================================================================
"""
import numpy as np
from scipy.optimize import brentq
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    HORIZONTE_ANOS, WACC,
    GASTO_MATERIAIS_POR_OBRA, FEE_MARKETPLACE,
)


def calcular_indicadores(fluxo: dict) -> dict:
    """
    Calcula VPL, TIR, Payback, FCL descontado e breakeven.

    Parâmetros
    ----------
    fluxo : dict retornado por fluxo_caixa.calcular_fluxo_caixa()

    Retorna
    -------
    dict com todos os indicadores
    """
    fcl_completo = fluxo["fcl_completo"]   # [Ano0, Ano1, ..., Ano5]
    fcl = fluxo["fcl"]                     # [Ano1, ..., Ano5]
    ebitda = fluxo["ebitda"]

    # ── VPL (Valor Presente Líquido) ───────────────────────
    # VPL = Σ FCL_t / (1 + WACC)^t    para t = 0..5
    fatores_desconto = np.array([
        1 / (1 + WACC) ** t for t in range(len(fcl_completo))
    ])
    fcl_descontado_completo = fcl_completo * fatores_desconto
    vpl = fcl_descontado_completo.sum()

    # FCL descontado por ano (anos 1–5 somente)
    fcl_descontado = np.array([
        fcl[y] / (1 + WACC) ** (y + 1) for y in range(HORIZONTE_ANOS)
    ])

    # ── TIR (Taxa Interna de Retorno) ─────────────────────
    # TIR é a taxa r que zera o VPL:  Σ FCL_t / (1+r)^t = 0
    def _vpn_func(r):
        return sum(
            fcl_completo[t] / (1 + r) ** t
            for t in range(len(fcl_completo))
        )

    try:
        tir = brentq(_vpn_func, -0.5, 50.0)
    except ValueError:
        tir = float("nan")

    # ── Payback simples ───────────────────────────────────
    # Meses até recuperar o investimento inicial com o FCL mensal do Ano 1
    investimento_inicial = -fcl_completo[0]
    fcl_mensal_ano1 = fcl[0] / 12
    payback_meses = investimento_inicial / fcl_mensal_ano1 if fcl_mensal_ano1 > 0 else float("inf")

    # Payback descontado (anos)
    acumulado = 0.0
    payback_desc_anos = float("inf")
    for t in range(len(fcl_completo)):
        acumulado += fcl_descontado_completo[t]
        if acumulado >= 0 and t > 0:
            # Interpolar dentro do ano
            acum_anterior = acumulado - fcl_descontado_completo[t]
            fracao = -acum_anterior / fcl_descontado_completo[t]
            payback_desc_anos = (t - 1) + fracao
            break

    # ── Breakeven de conversão ────────────────────────────
    # Taxa mínima de conversão para EBITDA > 0 no Ano 1
    # EBITDA ∝ receita ∝ taxa_conversão
    # (simplificado: a que taxa a receita = custos)
    margem_ebitda_y1 = ebitda[0] / fluxo["receita_bruta"][0]
    # Se margem = 50% com conversão 30%,
    # breakeven quando receita líq. = custos, ou seja
    # margem = 0 → conversão = 30% × (1 - margem) / (1)
    # Mais precisamente: breakeven ≈ custos / (receita_por_30%)
    receita_bruta_y1 = fluxo["receita_bruta"][0]
    custos_fixos_y1 = fluxo["opex"][0]
    receita_por_pct = receita_bruta_y1 / 0.30  # receita se conversão = 100%
    breakeven_conversao = custos_fixos_y1 / (receita_por_pct * (1 - 0.0565))
    # ≈ 14%

    return {
        "vpl": vpl,
        "tir": tir,
        "payback_meses": payback_meses,
        "payback_desc_anos": payback_desc_anos,
        "fcl_descontado": fcl_descontado,
        "fcl_descontado_completo": fcl_descontado_completo,
        "fatores_desconto": fatores_desconto,
        "breakeven_conversao": breakeven_conversao,
        "wacc": WACC,
    }


if __name__ == "__main__":
    from receitas import calcular_receitas
    from despesas import calcular_despesas
    from fluxo_caixa import calcular_fluxo_caixa

    r = calcular_receitas()
    d = calcular_despesas()
    fc = calcular_fluxo_caixa(r, d)
    ind = calcular_indicadores(fc)

    print("━" * 60)
    print("INDICADORES FINANCEIROS")
    print("━" * 60)
    print(f"  WACC (TMA):            {ind['wacc']:.2%}")
    print(f"  VPL:                   R$ {ind['vpl']/1e6:,.2f} M")
    print(f"  TIR:                   {ind['tir']:.2%}")
    print(f"  Payback:               {ind['payback_meses']:.1f} meses")
    print(f"  Payback descontado:    {ind['payback_desc_anos']:.2f} anos")
    print(f"  Breakeven conversão:   {ind['breakeven_conversao']:.1%}")
    print()
    print("  FCL Descontado por ano:")
    for y in range(HORIZONTE_ANOS):
        print(f"    Ano {y+1}: R$ {ind['fcl_descontado'][y]/1e6:,.2f} M")
