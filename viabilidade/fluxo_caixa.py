"""
=================================================================
FLUXO DE CAIXA LIVRE (FCL)
=================================================================
Constrói o FCL pela estrutura clássica:

    Receita Operacional Líquida
    (−) Custos e Despesas Operacionais
    = EBITDA
    (−) Depreciação
    = LAJIR (EBIT)
    (−) IR / CSLL (Lucro Presumido)
    (+) Depreciação (add-back, não-caixa)
    (−) CAPEX
    = FCL — Fluxo de Caixa Livre
=================================================================
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    HORIZONTE_ANOS, CAPEX_TOTAL,
    BASE_PRESUMIDA_SERVICOS, ALIQUOTA_IRPJ,
    ALIQUOTA_IRPJ_ADICIONAL, LIMITE_ADICIONAL_ANUAL,
    ALIQUOTA_CSLL, PCT_RECEITA_NCG,
)


def _calcular_ir_lucro_presumido(receita_bruta_anual: float) -> float:
    """
    Calcula IR + CSLL pelo regime de Lucro Presumido (serviços).

    Base de cálculo = 32% da receita bruta
    IRPJ = 15% da base  +  10% × (base − R$240k)
    CSLL = 9% da base
    """
    base = receita_bruta_anual * BASE_PRESUMIDA_SERVICOS

    # IRPJ normal
    irpj = base * ALIQUOTA_IRPJ

    # IRPJ adicional (sobre o que excede R$240k / ano)
    excedente = max(0, base - LIMITE_ADICIONAL_ANUAL)
    irpj_adicional = excedente * ALIQUOTA_IRPJ_ADICIONAL

    # CSLL
    csll = base * ALIQUOTA_CSLL

    return irpj + irpj_adicional + csll


def calcular_fluxo_caixa(receitas: dict, despesas: dict) -> dict:
    """
    Monta o Fluxo de Caixa Livre a partir das receitas e despesas.

    Parâmetros
    ----------
    receitas : dict retornado por receitas.calcular_receitas()
    despesas : dict retornado por despesas.calcular_despesas()

    Retorna
    -------
    dict com arrays de HORIZONTE_ANOS posições:
        ebitda, margem_ebitda, lajir, ir_csll, nopat, fcl
    """
    rb = receitas["receita_bruta"]
    rl = receitas["receita_liquida"]
    cogs = receitas["cogs_anual"]
    opex = despesas["opex_anual"]
    dep = despesas["depreciacao"]

    n = HORIZONTE_ANOS

    # ── EBITDA ──────────────────────────────────────────────
    ebitda = rl - opex - cogs
    margem_ebitda = ebitda / rb   # sobre receita bruta

    # ── LAJIR (EBIT) ───────────────────────────────────────
    lajir = ebitda - dep

    # ── IR + CSLL (Lucro Presumido) ────────────────────────
    ir_csll = np.array([_calcular_ir_lucro_presumido(rb[y]) for y in range(n)])

    # ── NOPAT (lucro operacional líquido de impostos) ──────
    nopat = lajir - ir_csll

    # ── Necessidade de Capital de Giro (NCG) ───────────────
    # Saldo de NCG no fim de cada ano = % da Receita Bruta daquele ano
    ncg_saldo = rb * PCT_RECEITA_NCG
    
    # Variação da NCG = NCG_t - NCG_{t-1}
    # No ano 1, NCG_anterior é zero
    ncg_anterior = np.zeros(n)
    ncg_anterior[1:] = ncg_saldo[:-1]
    variacao_ncg = ncg_saldo - ncg_anterior

    # ── FCL ────────────────────────────────────────────────
    # FCL = NOPAT + Depreciação − Variação de NCG
    # Investimento Inicial (CAPEX + OPEX pré-op) entra separado no Ano 0
    fcl = nopat + dep - variacao_ncg

    # Array completo: [Ano 0, Ano 1, ..., Ano 5]
    # Ano 0 = −Investimento Inicial Total
    fcl_completo = np.zeros(n + 1)
    fcl_completo[0] = -despesas["investimento_inicial"]
    fcl_completo[1:] = fcl

    return {
        "receita_bruta": rb,
        "receita_liquida": rl,
        "opex": opex,
        "cogs": cogs,
        "ebitda": ebitda,
        "margem_ebitda": margem_ebitda,
        "lajir": lajir,
        "depreciacao": dep,
        "ir_csll": ir_csll,
        "nopat": nopat,
        "ncg_saldo": ncg_saldo,
        "variacao_ncg": variacao_ncg,
        "fcl": fcl,            # Anos 1–5
        "fcl_completo": fcl_completo,  # Anos 0–5 (c/ CAPEX + OPEX pré-op)
    }


if __name__ == "__main__":
    from receitas import calcular_receitas
    from despesas import calcular_despesas

    r = calcular_receitas()
    d = calcular_despesas()
    fc = calcular_fluxo_caixa(r, d)

    print("━" * 70)
    print("FLUXO DE CAIXA LIVRE (FCL)")
    print("━" * 70)
    print(f"{'':>18} {'Ano 1':>12} {'Ano 2':>12} {'Ano 3':>12} {'Ano 4':>12} {'Ano 5':>12}")
    print("─" * 78)

    def _row(label, arr, div=1e6, fmt=",.2f"):
        vals = " ".join(f"{v/div:>12{fmt}}" for v in arr)
        print(f"  {label:<16}{vals}")

    _row("Receita Bruta", fc["receita_bruta"])
    _row("(−) Deduções", r["deducoes"])
    _row("Receita Líq.", fc["receita_liquida"])
    _row("(−) OPEX", fc["opex"])
    _row("(−) COGS", fc["cogs"], div=1e3, fmt=",.1f")
    _row("= EBITDA", fc["ebitda"])
    print(f"  {'Margem EBITDA':<16}" +
          " ".join(f"{v:>12.1%}" for v in fc["margem_ebitda"]))
    _row("(−) Deprec.", fc["depreciacao"], div=1e3, fmt=",.1f")
    _row("= NOPAT", fc["nopat"])
    _row("(+) Deprec.", fc["depreciacao"], div=1e3, fmt=",.1f")
    _row("(−) Var. NCG", fc["variacao_ncg"])
    _row("= FCL", fc["fcl"])
