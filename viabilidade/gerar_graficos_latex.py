import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

from premissas import HORIZONTE_ANOS
from mercado import calcular_mercado
from receitas import calcular_receitas
from despesas import calcular_despesas
from fluxo_caixa import calcular_fluxo_caixa
from indicadores import calcular_indicadores
from opcoes_reais import calcular_opcoes_reais
from cenarios_sensibilidade import gerar_matriz_sensibilidade, gerar_cenarios, simulacao_monte_carlo
from unit_economics import calcular_unit_economics
from otimizacao_solver import otimizar_mix_marketing

def gerar_graficos():
    # Executa a simulação completa para pegar os dados
    m = calcular_mercado()
    r = calcular_receitas()
    d = calcular_despesas()
    fc = calcular_fluxo_caixa(r, d)
    ind = indicadores = calcular_indicadores(fc)
    op = calcular_opcoes_reais(ind["vpl"], fc["fcl"][0])
    sensibilidade = gerar_matriz_sensibilidade()
    cenarios = gerar_cenarios()
    monte_carlo = simulacao_monte_carlo(n_iter=2000)
    ue = calcular_unit_economics(d)
    solver = otimizar_mix_marketing(ue["budget_marketing"])
    
    # Prepara o diretório
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "relatorio_latex", "figuras")
    os.makedirs(out_dir, exist_ok=True)
    
    anos = np.arange(1, HORIZONTE_ANOS + 1)
    
    # Define o estilo visual global para ficar premium
    plt.style.use('ggplot')
    
    # 1. Gráfico de FCL
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(anos, fc['fcl']/1e6, color='#2ca02c', alpha=0.7, label='FCL Líquido')
    ax.plot(anos, indicadores['fcl_descontado']/1e6, color='#d62728', marker='o', linewidth=2, label='FCL Descontado')
    ax.set_title('Evolução do Fluxo de Caixa Livre (R$ Milhões)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Anos')
    ax.set_ylabel('R$ Milhões')
    ax.set_xticks(anos)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'grafico_fcl.png'), dpi=300)
    plt.close(fig)
    
    # 2. Histograma de Monte Carlo
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(monte_carlo['vpls']/1e6, bins=40, color='#1f77b4', alpha=0.7, edgecolor='black')
    ax.axvline(0, color='red', linestyle='dashed', linewidth=2, label='Break-even (VPL=0)')
    ax.set_title('Simulação de Monte Carlo: Distribuição do VPL', fontsize=14, fontweight='bold')
    ax.set_xlabel('VPL (R$ Milhões)')
    ax.set_ylabel('Frequência Absoluta')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'grafico_monte_carlo.png'), dpi=300)
    plt.close(fig)
    
    # 3. Gráfico de Unit Economics (LTV/CAC)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(anos, ue['ltv_cac_ratio'], color='#9467bd', marker='s', linewidth=2, label='Relação LTV / CAC')
    ax.axhline(3, color='gray', linestyle='dashed', label='Mínimo Aceitável (3x)')
    ax.set_title('Evolução da Eficiência de Aquisição (LTV/CAC)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Anos')
    ax.set_ylabel('Relação Múltipla (x)')
    ax.set_xticks(anos)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'grafico_unit_economics.png'), dpi=300)
    plt.close(fig)
    
    # 4. Receita vs OPEX
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(anos, r['receita_bruta']/1e6, color='#1f77b4', alpha=0.7, label='Receita Bruta')
    ax.plot(anos, d['opex_anual']/1e6, color='#ff7f0e', marker='x', linewidth=2, label='OPEX')
    ax.set_title('Receita Bruta vs OPEX (R$ Milhões)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Anos')
    ax.set_ylabel('R$ Milhões')
    ax.set_xticks(anos)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'grafico_receita_opex.png'), dpi=300)
    plt.close(fig)
    
    # 5. Otimização do Solver (Mix de Marketing)
    fig, ax = plt.subplots(figsize=(8, 5))
    s_ads = [s['mix_google_ads'] for s in solver]
    s_out = [s['mix_outbound'] for s in solver]
    s_evt = [s['mix_feiras'] for s in solver]
    
    ax.bar(anos, s_ads, label='Google Ads', color='#3498db')
    ax.bar(anos, s_out, bottom=s_ads, label='Outbound B2B', color='#2ecc71')
    ax.bar(anos, s_evt, bottom=np.add(s_ads, s_out), label='Feiras', color='#f1c40f')
    ax.plot(anos, ue["construtoras_adquiridas"], color='black', marker='o', linestyle='dashed', label='Meta Original')
    
    ax.set_title('Mix Otimizado de Marketing (Solver) vs Meta Original', fontsize=14, fontweight='bold')
    ax.set_xlabel('Anos')
    ax.set_ylabel('Clientes Adquiridos')
    ax.set_xticks(anos)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'grafico_solver_mix.png'), dpi=300)
    plt.close(fig)

    print("Gráficos salvos com sucesso em relatorio_latex/figuras/")

if __name__ == '__main__':
    gerar_graficos()
