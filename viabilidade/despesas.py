"""
=================================================================
DESPESAS — OPEX, CAPEX, COGS e Depreciação
=================================================================
Modela as despesas operacionais por fase de crescimento,
o investimento inicial (CAPEX) e os custos variáveis (COGS).
=================================================================
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    HORIZONTE_ANOS, OPEX_MENSAL_FASES, CAPEX_TOTAL,
    DEPRECIACAO_ANUAL, COGS_POR_OBRA_MES, OBRAS_POR_ANO,
    DURACAO_OBRA_MESES, OPEX_MESES_PRE_OPERACIONAL,
    TAXA_MEIO_PAGAMENTO, GASTO_MATERIAIS_POR_OBRA, PCT_TRANSACOES_PLATAFORMA
)


def _opex_mensal(mes: int) -> float:
    """Retorna o OPEX mensal para um dado mês (1-indexed)."""
    for (inicio, fim), valor in OPEX_MENSAL_FASES.items():
        if inicio <= mes <= fim:
            return valor
    raise ValueError(f"Mês {mes} fora do horizonte de OPEX definido.")


def calcular_despesas():
    """
    Calcula OPEX, CAPEX, COGS e Depreciação.

    OPEX escala conforme contratação:
      Meses  1–6 : R$ 96.070  (time fundador)
      Meses  7–12: R$ 110.000 (+ CS, + analista)
      Meses 13–24: R$ 140.000 (+ comercial, + ops)
      Meses 25–36: R$ 185.000 (head expansão)
      Meses 37–48: R$ 250.000 (time MG / RJ)
      Meses 49–60: R$ 345.000 (nacional)

    Investimento Inicial (Ano 0) = CAPEX + OPEX Pré-operacional
      - CAPEX: R$ 128.867 (setup jurídico, branding, equipamentos)
      - OPEX Pré-operacional: X meses do time inicial (Vale da Morte)

    COGS = R$ 52,87 / obra / mês (IA, cloud, NF, WhatsApp)
           + Custos de Gateway/Adquirência (1% sobre o GMV transacionado)

    Depreciação = CAPEX / 5 anos (linear)

    Retorna dict com arrays de 5 anos.
    """
    meses_total = HORIZONTE_ANOS * 12

    # --- OPEX mensal ---
    opex_mes = np.array([_opex_mensal(m + 1) for m in range(meses_total)])

    # --- OPEX anual ---
    opex_anual = np.array([
        opex_mes[y * 12:(y + 1) * 12].sum()
        for y in range(HORIZONTE_ANOS)
    ])

    # --- COGS anual ---
    # Cada obra gera COGS de software fixo + COGS variável do Gateway
    cogs_software_obra = DURACAO_OBRA_MESES * COGS_POR_OBRA_MES
    gmv_obra_transacionado = GASTO_MATERIAIS_POR_OBRA * PCT_TRANSACOES_PLATAFORMA
    cogs_gateway_obra = gmv_obra_transacionado * TAXA_MEIO_PAGAMENTO
    cogs_total_por_obra = cogs_software_obra + cogs_gateway_obra
    
    cogs_anual = np.array([
        OBRAS_POR_ANO[y] * cogs_total_por_obra
        for y in range(HORIZONTE_ANOS)
    ])

    # --- CAPEX e OPEX Pré-operacional (Ano 0) ---
    # Consideramos que o OPEX pré-operacional tem o custo da Fase 1 (Meses 1-6)
    opex_pre_op_mensal = _opex_mensal(1)
    opex_pre_op_total = opex_pre_op_mensal * OPEX_MESES_PRE_OPERACIONAL
    capex = CAPEX_TOTAL
    investimento_inicial_total = capex + opex_pre_op_total

    # --- Depreciação linear ---
    depreciacao = np.full(HORIZONTE_ANOS, DEPRECIACAO_ANUAL)

    # --- Custos totais por ano (OPEX + COGS) ---
    custos_totais = opex_anual + cogs_anual

    return {
        "opex_anual": opex_anual,
        "opex_mensal": opex_mes,
        "cogs_anual": cogs_anual,
        "capex_tangivel": capex,
        "opex_pre_operacional": opex_pre_op_total,
        "investimento_inicial": investimento_inicial_total,
        "depreciacao": depreciacao,
        "custos_totais": custos_totais,
    }


if __name__ == "__main__":
    d = calcular_despesas()
    print("━" * 60)
    print("DESPESAS")
    print("━" * 60)
    print(f"  CAPEX (Ano 0):  R$ {d['capex']:,.2f}")
    print(f"  Depreciação / ano: R$ {d['depreciacao'][0]:,.2f}")
    print()
    for y in range(HORIZONTE_ANOS):
        print(
            f"  Ano {y+1}: "
            f"OPEX R$ {d['opex_anual'][y]/1e6:,.2f}M  |  "
            f"COGS R$ {d['cogs_anual'][y]/1e3:,.1f}k  |  "
            f"Total R$ {d['custos_totais'][y]/1e6:,.2f}M"
        )
