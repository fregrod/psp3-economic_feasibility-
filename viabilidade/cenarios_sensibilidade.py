"""
=================================================================
CENÁRIOS E SENSIBILIDADE
=================================================================
Calcula a Análise de Sensibilidade (WACC vs Conversão)
e projeta 3 Cenários (Pessimista, Base, Otimista).
=================================================================
"""
import numpy as np
import copy
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    WACC, TAXA_CONVERSAO, FEE_MARKETPLACE,
)
from mercado import calcular_mercado
from receitas import calcular_receitas
from despesas import calcular_despesas
from fluxo_caixa import calcular_fluxo_caixa
from indicadores import calcular_indicadores


def recalcular_vpl_com_novas_premissas(
    nova_conversao=None,
    novo_wacc=None,
    novo_fee=None,
):
    """
    Função auxiliar que injeta premissas temporárias nos
    módulos e recalcula o VPL. 
    Para não poluir o global, injeta no namespace apropriado
    ou calcula as deltas.
    
    A Taxa de Conversão afeta a quantidade de Obras.
    Como a Base é 30%, o fator é nova_conversao / 30%.
    """
    import premissas
    import receitas
    import indicadores
    import mercado
    
    fator_conversao = 1.0
    if nova_conversao is not None:
        fator_conversao = nova_conversao / premissas.TAXA_CONVERSAO

    # Salva original
    obras_originais = premissas.OBRAS_POR_ANO.copy()
    wacc_original = indicadores.WACC
    fee_rec_original = receitas.FEE_MARKETPLACE
    fee_mer_original = mercado.FEE_MARKETPLACE
    
    # Aplica
    # Modifica a lista in-place para afetar quem importou a referência
    premissas.OBRAS_POR_ANO[:] = [int(o * fator_conversao) for o in obras_originais]
    
    if novo_wacc is not None:
        indicadores.WACC = novo_wacc
    if novo_fee is not None:
        receitas.FEE_MARKETPLACE = novo_fee
        mercado.FEE_MARKETPLACE = novo_fee
        
    try:
        r = receitas.calcular_receitas()
        d = calcular_despesas()
        fc = calcular_fluxo_caixa(r, d)
        ind = indicadores.calcular_indicadores(fc)
        vpl = ind["vpl"]
        margem = fc["margem_ebitda"][-1] # Margem do último ano
        payback = ind["payback_meses"]
    finally:
        # Restaura
        premissas.OBRAS_POR_ANO[:] = obras_originais
        indicadores.WACC = wacc_original
        receitas.FEE_MARKETPLACE = fee_rec_original
        mercado.FEE_MARKETPLACE = fee_mer_original
        
    return vpl, margem, payback


def gerar_matriz_sensibilidade():
    """
    Varia WACC e Taxa de Conversão para encontrar o VPL.
    """
    wacc_range = np.linspace(WACC - 0.10, WACC + 0.10, 5)  # 5 steps
    conv_range = np.linspace(TAXA_CONVERSAO - 0.15, TAXA_CONVERSAO + 0.15, 5)
    
    matriz_vpl = np.zeros((len(wacc_range), len(conv_range)))
    
    for i, w in enumerate(wacc_range):
        for j, c in enumerate(conv_range):
            vpl, _, _ = recalcular_vpl_com_novas_premissas(nova_conversao=c, novo_wacc=w)
            matriz_vpl[i, j] = vpl
            
    return wacc_range, conv_range, matriz_vpl


def gerar_cenarios():
    """
    Gera 3 cenários de projeto.
    """
    cenarios = [
        # Cenário Pessimista
        # Conversão mais espremida (3%) e desconto agressivo (WACC + 10%)
        {"nome": "Pessimista", "conversao": 0.03, "wacc": WACC + 0.10},
        
        # Cenário Base (como configurado no premissas.py)
        {"nome": "Base", "conversao": TAXA_CONVERSAO, "wacc": WACC},
        
        # Cenário Otimista
        # Tração se prova excelente (8%) e risco diminui (WACC - 10%)
        {"nome": "Otimista", "conversao": 0.08, "wacc": WACC - 0.10},
    ]
    
    resultados = []
    for c in cenarios:
        vpl, margem, payback = recalcular_vpl_com_novas_premissas(
            nova_conversao=c["conversao"], 
            novo_wacc=c["wacc"]
        )
        resultados.append({
            "nome": c["nome"],
            "conversao": c["conversao"],
            "wacc": c["wacc"],
            "vpl": vpl,
            "margem_ano5": margem,
            "payback": payback
        })
        
    return resultados


def simulacao_monte_carlo(n_iter=2000):
    """
    Simulação de Monte Carlo para Análise de Risco Estocástica.
    Sorteia valores para WACC e Taxa de Conversão baseado em distribuições
    probabilísticas e calcula o VPL para cada cenário.
    """
    np.random.seed(42)  # Para reprodutibilidade
    
    # WACC: Distribuição Normal (Média = WACC base, Desvio = 2%)
    wacc_sims = np.random.normal(loc=WACC, scale=0.02, size=n_iter)
    wacc_sims = np.clip(wacc_sims, 0.10, 0.70)
    
    # 2. Amostragem da Taxa de Conversão (Distribuição Triangular: min 2%, moda 5%, max 8%)
    # Reflete a dura realidade do cold outreach B2B
    conv_samples = np.random.triangular(0.02, 0.05, 0.08, n_iter)
    
    vpls = np.zeros(n_iter)
    
    for i in range(n_iter):
        vpl, _, _ = recalcular_vpl_com_novas_premissas(
            nova_conversao=conv_samples[i], 
            novo_wacc=wacc_sims[i]
        )
        vpls[i] = vpl
        
    probabilidade_sucesso = np.sum(vpls > 0) / n_iter
    vpl_medio = np.mean(vpls)
    
    return {
        "vpls": vpls,
        "probabilidade_sucesso": probabilidade_sucesso,
        "vpl_medio": vpl_medio,
        "n_iter": n_iter,
    }

if __name__ == "__main__":
    print("━" * 60)
    print("ANÁLISE DE CENÁRIOS")
    print("━" * 60)
    cenarios = gerar_cenarios()
    for c in cenarios:
        print(f"Cenário {c['nome']}:")
        print(f"  Conversão: {c['conversao']:.0%} | Fee: {c['fee']:.1%}")
        print(f"  VPL: R$ {c['vpl']/1e6:.2f} M")
        print(f"  Margem Y5: {c['margem_ano5']:.1%}")
        print(f"  Payback: {c['payback']:.1f} meses")
        print()
