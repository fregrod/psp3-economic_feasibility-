"""
=================================================================
UNIT ECONOMICS E FUNIL
=================================================================
Calcula Custo de Aquisição de Clientes (CAC),
Life Time Value (LTV) e a Relação LTV/CAC.
=================================================================
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    FEE_POR_OBRA, HORIZONTE_ANOS, OBRAS_POR_ANO,
    DURACAO_OBRA_MESES,
)
from despesas import calcular_despesas

# Premissas de Unit Economics
PCT_OPEX_MARKETING_VENDAS = 0.40  # 40% do OPEX é alocado para Marketing e Vendas
OBRAS_POR_CLIENTE_ANO = 1.5       # Em média, um cliente (construtora) faz 1.5 obras conosco por ano
CHURN_RATE_ANUAL = 0.20           # 20% das construtoras deixam a plataforma por ano
VIDA_UTIL_CLIENTE_ANOS = 1 / CHURN_RATE_ANUAL  # 5 anos


def calcular_unit_economics(despesas):
    """
    Calcula as métricas de Unit Economics por ano.
    CAC = (OPEX de Vendas & Marketing) / Novos Clientes
    LTV = Fee por obra * Obras por ano * Vida útil
    """
    opex_anual = despesas["opex_anual"]
    budget_cac_anual = opex_anual * PCT_OPEX_MARKETING_VENDAS
    
    # LTV de um cliente = (FEE_POR_OBRA * OBRAS_POR_CLIENTE_ANO) * VIDA_UTIL_CLIENTE_ANOS
    ltv = FEE_POR_OBRA * OBRAS_POR_CLIENTE_ANO * VIDA_UTIL_CLIENTE_ANOS
    
    # CAC Blended (Média de todos os canais no ano)
    construtoras_adquiridas_por_ano = np.array([obras / OBRAS_POR_CLIENTE_ANO for obras in OBRAS_POR_ANO])
    
    cac_anual = budget_cac_anual / construtoras_adquiridas_por_ano
    ltv_cac_ratio = ltv / cac_anual
    
    # Payback do CAC (meses)
    receita_mensal_cliente = (FEE_POR_OBRA * OBRAS_POR_CLIENTE_ANO) / 12
    cac_payback_meses = cac_anual / receita_mensal_cliente
    
    return {
        "ltv": ltv,
        "cac_anual": cac_anual,
        "ltv_cac_ratio": ltv_cac_ratio,
        "cac_payback_meses": cac_payback_meses,
        "budget_marketing": budget_cac_anual,
        "construtoras_adquiridas": construtoras_adquiridas_por_ano,
    }

if __name__ == "__main__":
    d = calcular_despesas()
    ue = calcular_unit_economics(d)
    
    print("━" * 60)
    print("UNIT ECONOMICS")
    print("━" * 60)
    print(f"LTV Estimado (Vida útil de {VIDA_UTIL_CLIENTE_ANOS:.0f} anos): R$ {ue['ltv']:,.2f}")
    
    for y in range(HORIZONTE_ANOS):
        print(f"\nAno {y+1}:")
        print(f"  Budget MKT/Vendas: R$ {ue['budget_marketing'][y]:,.2f}")
        print(f"  Construtoras Adq.: {ue['construtoras_adquiridas'][y]:.0f}")
        print(f"  CAC Blended:       R$ {ue['cac_anual'][y]:,.2f}")
        print(f"  LTV / CAC:         {ue['ltv_cac_ratio'][y]:.1f}x")
        print(f"  CAC Payback:       {ue['cac_payback_meses'][y]:.1f} meses")
