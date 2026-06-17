"""
=================================================================
OTIMIZAÇÃO COM SOLVER (PROGRAMAÇÃO LINEAR)
=================================================================
Utiliza o algoritmo Simplex/Interior-Point para encontrar o mix
ótimo de canais de marketing, maximizando o número de clientes
adquiridos respeitando o orçamento anual de marketing e a
capacidade máxima de cada canal.
=================================================================
"""
import sys, os
import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, os.path.dirname(__file__))

from premissas import HORIZONTE_ANOS
from despesas import calcular_despesas
from unit_economics import calcular_unit_economics

# Premissas de Canais de Aquisição (CAC e Limites)
# x1: Google Ads / Digital
# x2: Outbound B2B (Venda Direta)
# x3: Feiras e Eventos do Setor

# Custo de Aquisição (CAC) inflacionado para refletir a nova conversão de 5%
CAC_CANAIS = [4500, 8500, 15000]

# Capacidade máxima de aquisição por canal por ano (escala)
# (Google Ads, Outbound, Feiras)
CAPACIDADE_MAXIMA = [
    [50, 20, 5],     # Ano 1 (ramp-up)
    [150, 80, 20],   # Ano 2
    [250, 150, 40],  # Ano 3
    [400, 250, 60],  # Ano 4
    [600, 400, 100], # Ano 5
]


def otimizar_mix_marketing(budget_marketing_anual):
    """
    Roda um modelo de Programação Linear para cada ano do horizonte.
    
    Função Objetivo: Minimizar -(x1 + x2 + x3) <=> Maximizar (x1 + x2 + x3)
    
    Restrições:
    1. x1*CAC1 + x2*CAC2 + x3*CAC3 <= Budget_Anual
    2. 0 <= x1 <= Cap_x1
    3. 0 <= x2 <= Cap_x2
    4. 0 <= x3 <= Cap_x3
    """
    resultados = []
    
    # Coeficientes da Função Objetivo (Minimizar negativo = Maximizar)
    c = [-1, -1, -1]
    
    # Matriz de restrição de desigualdade (Lado esquerdo)
    # A_ub * x <= b_ub
    A_ub = [CAC_CANAIS]
    
    for y in range(HORIZONTE_ANOS):
        budget = budget_marketing_anual[y]
        b_ub = [budget]
        
        # Limites (bounds) de cada variável (0, capacidade_maxima)
        bounds = [
            (0, CAPACIDADE_MAXIMA[y][0]),
            (0, CAPACIDADE_MAXIMA[y][1]),
            (0, CAPACIDADE_MAXIMA[y][2])
        ]
        
        # Executa o Solver (Simplex / Highs)
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if res.success:
            mix_ideal = np.floor(res.x)
            clientes_maximos = int(np.sum(mix_ideal))
            custo_realizado = np.sum(mix_ideal * CAC_CANAIS)
            
            resultados.append({
                "ano": y + 1,
                "budget_disponivel": budget,
                "budget_utilizado": custo_realizado,
                "clientes_maximos": clientes_maximos,
                "mix_google_ads": int(mix_ideal[0]),
                "mix_outbound": int(mix_ideal[1]),
                "mix_feiras": int(mix_ideal[2]),
                "cac_blended_otimizado": custo_realizado / clientes_maximos if clientes_maximos > 0 else 0
            })
        else:
            raise ValueError(f"Solver falhou no Ano {y+1}")
            
    return resultados


if __name__ == "__main__":
    d = calcular_despesas()
    ue = calcular_unit_economics(d)
    
    print("━" * 60)
    print("PROGRAMAÇÃO LINEAR: OTIMIZAÇÃO DE MIX DE MARKETING")
    print("━" * 60)
    
    resultados_solver = otimizar_mix_marketing(ue["budget_marketing"])
    meta_original = ue["construtoras_adquiridas"]
    
    for r in resultados_solver:
        y = r["ano"] - 1
        print(f"\nAno {r['ano']}:")
        print(f"  Orçamento Disp.:  R$ {r['budget_disponivel']:,.2f}  |  Utilizado: R$ {r['budget_utilizado']:,.2f}")
        print(f"  Meta (Original):  {meta_original[y]:.0f} clientes")
        print(f"  Solver Máximo:    {r['clientes_maximos']} clientes ({(r['clientes_maximos']/meta_original[y])-1:+.1%} vs Meta)")
        print(f"  Mix Ideal:        {r['mix_google_ads']} Google Ads | {r['mix_outbound']} Outbound | {r['mix_feiras']} Feiras")
        print(f"  CAC Otimizado:    R$ {r['cac_blended_otimizado']:,.2f}")
