"""
=================================================================
RECEITAS — Projeção de Receitas (5 anos)
=================================================================
Calcula a receita bruta e líquida anual a partir das premissas
de obras atendidas e fee transacional.
=================================================================
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    HORIZONTE_ANOS, OBRAS_POR_ANO, FEE_POR_OBRA,
    GASTO_MATERIAIS_POR_OBRA, FEE_MARKETPLACE,
    DURACAO_OBRA_MESES, OBRAS_NOVAS_MES_INICIAL,
    DEDUCOES_RECEITA, COGS_POR_OBRA_MES,
)


def calcular_receitas():
    """
    Projeção de receitas anuais.

    Modelo:
        Receita Bruta = obras_no_ano × fee_por_obra
        Fee por obra  = gasto_materiais × fee_rate
        Receita Líquida = Receita Bruta × (1 − deduções)

    Retorna dict com arrays de 5 anos.
    """
    obras = np.array(OBRAS_POR_ANO, dtype=float)

    # --- Receita por obra ---
    # fee_por_obra = R$ 1.282.500 × 2,5% = R$ 32.062,50
    receita_por_obra = GASTO_MATERIAIS_POR_OBRA * FEE_MARKETPLACE

    # --- Receita Bruta anual ---
    receita_bruta = obras * receita_por_obra

    # --- Deduções sobre receita (PIS 0,65% + COFINS 3% + ISS 2% = 5,65%) ---
    deducoes = receita_bruta * DEDUCOES_RECEITA

    # --- Receita Líquida ---
    receita_liquida = receita_bruta - deducoes

    # --- COGS (custo variável por obra ativa) ---
    # Cada obra dura DURACAO_OBRA_MESES, gerando COGS mensal
    cogs_anual = obras * DURACAO_OBRA_MESES * COGS_POR_OBRA_MES

    # --- Métricas auxiliares ---
    obras_mes_medio = obras / 12

    # --- Simulação mensal (para visualização no dashboard) ---
    meses_total = HORIZONTE_ANOS * 12
    obras_novas_mes = np.zeros(meses_total)
    for m in range(meses_total):
        ano = m // 12
        obras_novas_mes[m] = OBRAS_POR_ANO[ano] / 12

    # Obras ativas = rolling window de 3 meses
    obras_ativas_mes = np.zeros(meses_total)
    for m in range(meses_total):
        for k in range(min(m + 1, DURACAO_OBRA_MESES)):
            obras_ativas_mes[m] += obras_novas_mes[m - k]

    receita_mensal = (
        obras_ativas_mes
        * (GASTO_MATERIAIS_POR_OBRA / DURACAO_OBRA_MESES)
        * FEE_MARKETPLACE
    )

    return {
        # Anuais
        "receita_bruta": receita_bruta,
        "receita_liquida": receita_liquida,
        "deducoes": deducoes,
        "cogs_anual": cogs_anual,
        "obras_por_ano": obras,
        "receita_por_obra": receita_por_obra,
        "obras_mes_medio": obras_mes_medio,
        # Mensais (para dashboard)
        "receita_mensal": receita_mensal,
        "obras_novas_mes": obras_novas_mes,
        "obras_ativas_mes": obras_ativas_mes,
    }


if __name__ == "__main__":
    r = calcular_receitas()
    print("━" * 60)
    print("PROJEÇÃO DE RECEITAS")
    print("━" * 60)
    for y in range(HORIZONTE_ANOS):
        print(
            f"  Ano {y+1}: "
            f"Obras {r['obras_por_ano'][y]:,.0f}  |  "
            f"RB R$ {r['receita_bruta'][y]/1e6:,.2f}M  |  "
            f"RL R$ {r['receita_liquida'][y]/1e6:,.2f}M  |  "
            f"COGS R$ {r['cogs_anual'][y]/1e3:,.1f}k"
        )
