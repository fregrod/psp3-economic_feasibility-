"""
=================================================================
OPÇÕES REAIS — Modelo Binomial (Expansão + Abandono)
=================================================================
Calcula o valor das opções reais usando o modelo binomial
de Cox-Ross-Rubinstein (CRR).

  VPL Estratégico = VPL base + Opção de Expansão + Opção de Abandono
=================================================================
"""
import numpy as np
import math
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    VOLATILIDADE, TAXA_LIVRE_RISCO,
    FATOR_ALTA, FATOR_BAIXA, PROB_NEUTRA_RISCO,
    INVESTIMENTO_EXPANSAO, FATOR_VALOR_EXPANSAO,
    VALOR_RESGATE_ABANDONO,
)


def _arvore_binomial_call(S0, X, u, d, p, rf, n_periodos):
    """
    Precifica uma opção CALL europeia com árvore binomial.

    Parâmetros
    ----------
    S0 : float — valor do ativo subjacente
    X  : float — preço de exercício (custo de expansão)
    u  : float — fator de alta
    d  : float — fator de baixa
    p  : float — probabilidade neutra ao risco
    rf : float — taxa livre de risco (anual)
    n_periodos : int — número de períodos

    Retorna
    -------
    valor_opcao, arvore_S, arvore_C
    """
    discount = math.exp(-rf)

    # Construir árvore de preços do ativo
    arvore_S = np.zeros((n_periodos + 1, n_periodos + 1))
    for i in range(n_periodos + 1):
        for j in range(i + 1):
            arvore_S[j, i] = S0 * (u ** (i - j)) * (d ** j)

    # Payoff no vencimento (Call: max(S - X, 0))
    arvore_C = np.zeros_like(arvore_S)
    for j in range(n_periodos + 1):
        arvore_C[j, n_periodos] = max(arvore_S[j, n_periodos] - X, 0)

    # Backward induction
    for i in range(n_periodos - 1, -1, -1):
        for j in range(i + 1):
            arvore_C[j, i] = (
                p * arvore_C[j, i + 1] + (1 - p) * arvore_C[j + 1, i + 1]
            ) * discount

    return arvore_C[0, 0], arvore_S, arvore_C


def _arvore_binomial_put_americana(S0, X, u, d, p, rf, n_periodos):
    """
    Precifica uma opção PUT americana com árvore binomial.

    Parâmetros
    ----------
    S0 : float — valor do ativo subjacente
    X  : float — valor de resgate (salvage value)
    u, d, p, rf : parâmetros do modelo binomial
    n_periodos : int — número de períodos

    Retorna
    -------
    valor_opcao, arvore_S, arvore_P
    """
    discount = math.exp(-rf)

    # Árvore de preços
    arvore_S = np.zeros((n_periodos + 1, n_periodos + 1))
    for i in range(n_periodos + 1):
        for j in range(i + 1):
            arvore_S[j, i] = S0 * (u ** (i - j)) * (d ** j)

    # Payoff no vencimento (Put: max(X - S, 0))
    arvore_P = np.zeros_like(arvore_S)
    for j in range(n_periodos + 1):
        arvore_P[j, n_periodos] = max(X - arvore_S[j, n_periodos], 0)

    # Backward induction (americana: comparar com exercício antecipado)
    for i in range(n_periodos - 1, -1, -1):
        for j in range(i + 1):
            cont_value = (
                p * arvore_P[j, i + 1] + (1 - p) * arvore_P[j + 1, i + 1]
            ) * discount
            exercise_value = max(X - arvore_S[j, i], 0)
            arvore_P[j, i] = max(cont_value, exercise_value)

    return arvore_P[0, 0], arvore_S, arvore_P


def calcular_opcoes_reais(vpl_base: float, fcl_ano1: float) -> dict:
    """
    Calcula as opções reais do projeto.

    Opção de Expansão (Call):
        Exercício no Ano 2 → entrar em MG e RJ
        Subjacente S0 = 50% do VPL base (valor de ter 2 novos estados)
        Strike X = R$ 2,5M (investimento adicional)
        Períodos = 2 (anos)

    Opção de Abandono (Put americana):
        Se adoção for muito baixa → vender plataforma por R$ 3M
        Subjacente S0 = FCL descontado do Ano 1 (valor em risco)
        Strike X = R$ 3M (valor de resgate)
        Períodos = 2 (anos)
    """
    u = FATOR_ALTA
    d = FATOR_BAIXA
    p = PROB_NEUTRA_RISCO
    rf = TAXA_LIVRE_RISCO

    # ── Opção de Expansão (Call) ───────────────────────────
    # S0 = valor da expansão = 50% do VPL base
    # (2 estados novos ≈ 50% da operação atual em SP)
    s0_expansao = vpl_base * FATOR_VALOR_EXPANSAO
    x_expansao = INVESTIMENTO_EXPANSAO

    valor_expansao, arvore_s_exp, arvore_c_exp = _arvore_binomial_call(
        S0=s0_expansao,
        X=x_expansao,
        u=u, d=d, p=p, rf=rf,
        n_periodos=2,
    )

    # ── Opção de Abandono (Put americana) ──────────────────
    # S0 = FCL do Ano 1 descontado (valor imediato do projeto em risco)
    s0_abandono = fcl_ano1 / (1 + rf / 2)  # desconta meio período
    x_abandono = VALOR_RESGATE_ABANDONO

    valor_abandono, arvore_s_put, arvore_p_put = _arvore_binomial_put_americana(
        S0=s0_abandono,
        X=x_abandono,
        u=u, d=d, p=p, rf=rf,
        n_periodos=2,
    )

    # ── VPL Estratégico ───────────────────────────────────
    vpl_estrategico = vpl_base + valor_expansao + valor_abandono
    pct_sobre_base = (vpl_estrategico / vpl_base - 1)

    return {
        # Parâmetros do modelo
        "volatilidade": VOLATILIDADE,
        "taxa_livre_risco": TAXA_LIVRE_RISCO,
        "fator_alta": u,
        "fator_baixa": d,
        "prob_neutra_risco": p,
        # Expansão
        "s0_expansao": s0_expansao,
        "x_expansao": x_expansao,
        "valor_expansao": valor_expansao,
        "arvore_s_expansao": arvore_s_exp,
        "arvore_c_expansao": arvore_c_exp,
        # Abandono
        "s0_abandono": s0_abandono,
        "x_abandono": x_abandono,
        "valor_abandono": valor_abandono,
        "arvore_s_abandono": arvore_s_put,
        "arvore_p_abandono": arvore_p_put,
        # Consolidado
        "vpl_base": vpl_base,
        "vpl_estrategico": vpl_estrategico,
        "pct_sobre_base": pct_sobre_base,
    }


if __name__ == "__main__":
    from receitas import calcular_receitas
    from despesas import calcular_despesas
    from fluxo_caixa import calcular_fluxo_caixa
    from indicadores import calcular_indicadores

    r = calcular_receitas()
    d = calcular_despesas()
    fc = calcular_fluxo_caixa(r, d)
    ind = calcular_indicadores(fc)

    op = calcular_opcoes_reais(ind["vpl"], fc["fcl"][0])

    print("━" * 60)
    print("OPÇÕES REAIS — Modelo Binomial")
    print("━" * 60)
    print(f"  Volatilidade (σ):       {op['volatilidade']:.0%}")
    print(f"  u = e^σ:                {op['fator_alta']:.4f}")
    print(f"  d = 1/u:                {op['fator_baixa']:.4f}")
    print(f"  p (neutra ao risco):    {op['prob_neutra_risco']:.4f}")
    print()
    print("  ── Opção de Expansão (Call) ──")
    print(f"    S₀ (valor expansão):  R$ {op['s0_expansao']/1e6:,.2f} M")
    print(f"    X  (investimento):    R$ {op['x_expansao']/1e6:,.2f} M")
    print(f"    Valor da opção:       R$ {op['valor_expansao']/1e6:,.3f} M")
    print()
    print("  ── Opção de Abandono (Put americana) ──")
    print(f"    S₀ (valor em risco):  R$ {op['s0_abandono']/1e3:,.1f} k")
    print(f"    X  (resgate):         R$ {op['x_abandono']/1e6:,.2f} M")
    print(f"    Valor da opção:       R$ {op['valor_abandono']/1e6:,.3f} M")
    print()
    print(f"  VPL base:               R$ {op['vpl_base']/1e6:,.2f} M")
    print(f"  + Expansão:             R$ {op['valor_expansao']/1e6:,.3f} M")
    print(f"  + Abandono:             R$ {op['valor_abandono']/1e6:,.3f} M")
    print(f"  = VPL Estratégico:      R$ {op['vpl_estrategico']/1e6:,.2f} M")
    print(f"    (+{op['pct_sobre_base']:.0%} sobre base)")
