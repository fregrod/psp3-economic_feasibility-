"""
=================================================================
PREMISSAS — Marketplace de Material de Construção
=================================================================
Centraliza todas as constantes, hipóteses e parâmetros do projeto.
Fontes: IBGE, BCB, B3, Damodaran, premissas do modelo financeiro.
=================================================================
"""
import math

# =============================================================
# 1. PREMISSAS DE MERCADO
# =============================================================
TOTAL_OBRAS_ANO_BRASIL = 50_000          # obras formais e informais / ano
PAVIMENTOS_MEDIO_POR_OBRA = 2.85         # pavimentos médios
AREA_POR_PAVIMENTO_M2 = 600             # m² por pavimento (premissa)
CUSTO_MEDIO_M2 = 1_250                  # R$ / m² (custo total da obra)
PCT_CUSTO_MATERIAIS = 0.60              # 60% do custo total = materiais

# --- Cálculos derivados ---
AREA_TOTAL_MEDIA = PAVIMENTOS_MEDIO_POR_OBRA * AREA_POR_PAVIMENTO_M2   # 1.710 m²
GASTO_MATERIAIS_POR_OBRA = (
    AREA_TOTAL_MEDIA * CUSTO_MEDIO_M2 * PCT_CUSTO_MATERIAIS
)  # R$ 1.282.500

# =============================================================
# 2. PREMISSAS DO MARKETPLACE E RISCO DE BYPASS
# =============================================================
FEE_MARKETPLACE = 0.025                 # 2,5% sobre compra intermediada
PCT_TRANSACOES_PLATAFORMA = 0.50        # Assumindo 50% de bypass (fuga de transação) da construtora
FEE_POR_OBRA = GASTO_MATERIAIS_POR_OBRA * FEE_MARKETPLACE * PCT_TRANSACOES_PLATAFORMA  # R$ 16.031,25
TAXA_CONVERSAO = 0.05                   # 5% das obras contatadas convertem (cold outreach / mídia)
DURACAO_OBRA_MESES = 3                  # duração média de uma obra
OBRAS_NOVAS_MES_INICIAL = 8             # obras novas / mês no mês 1

# =============================================================
# 3. CUSTO DE CAPITAL — CAPM  (100% equity, startup sem dívida)
# =============================================================
# Fontes das taxas
IPCA_2025 = 0.0426                      # IBGE
TAXA_LIVRE_RISCO = 0.1475               # BCB / B3 — Selic
EQUITY_RISK_PREMIUM = 0.0423            # Damodaran — ERP Brasil
COUNTRY_RISK_PREMIUM = 0.0324           # Damodaran — CRP Brasil
PREMIO_STARTUP = 0.22                   # Prêmio Seed/Pre-Seed (Mortalidade altíssima)
BETA_ALAVANCADO = 1.17                  # Calculado (setor construção)

# Ke = Rf + β × (ERP + CRP) + Prêmio Startup
CUSTO_EQUITY = (
    TAXA_LIVRE_RISCO
    + BETA_ALAVANCADO * (EQUITY_RISK_PREMIUM + COUNTRY_RISK_PREMIUM)
    + PREMIO_STARTUP
)
# WACC Seed/Early Stage deve operar em ~45% a.a.
WACC = CUSTO_EQUITY

# =============================================================
# 4. HORIZONTE, ESTRUTURA OPERACIONAL E CAPITAL DE GIRO
# =============================================================
HORIZONTE_ANOS = 5
CAPEX_TOTAL = 128_867                   # R$ (jurídico, branding, equip.)
COGS_POR_OBRA_MES = 52.87              # R$ / obra / mês (IA, cloud, NF, WhatsApp)
TAXA_MEIO_PAGAMENTO = 0.010            # 1.0% de Gateway/Split sobre o GMV Transacionado

OPEX_MESES_PRE_OPERACIONAL = 6          # 6 meses de queima de caixa inicial sem receita

PRAZO_RECEBIMENTO_DIAS = 30             # Ciclo financeiro: recebimento médio em 30 dias
PRAZO_PAGAMENTO_DIAS = 15               # Prazo médio de pagamento a fornecedores
PCT_RECEITA_NCG = PRAZO_RECEBIMENTO_DIAS / 360  # % da receita bruta retida em contas a receber

# OPEX mensal por fase — crescimento conforme time
OPEX_MENSAL_FASES = {
    (1, 6):   96_070,    # Time fundador
    (7, 12):  110_000,   # + CS, + analista
    (13, 24): 140_000,   # + comercial, + ops     (média 130–150k)
    (25, 36): 185_000,   # Head de expansão       (média 170–200k)
    (37, 48): 250_000,   # Time MG / RJ           (média 230–270k)
    (49, 60): 345_000,   # Nacional               (média 310–380k)
}

# Premissa de obras atendidas por ano
# ───────────────────────────────────────────────────────────────
# Derivado da estratégia de expansão geográfica + capacidade comercial:
#   Ano 1 →   88 obras  (8 / mês × 11 meses efetivos — ramp-up)
#   Ano 2 →  287 obras  (expansão SP + entrada MG / RJ)
#   Ano 3 →  411 obras  (consolidação MG / RJ)
#   Ano 4 →  658 obras  (expansão regional)
#   Ano 5 → 1264 obras  (escala nacional)
OBRAS_POR_ANO = [88, 287, 411, 658, 1264]

# =============================================================
# 5. PREMISSAS TRIBUTÁRIAS — Lucro Presumido (serviços)
# =============================================================
# Deduções sobre receita bruta
PIS_RATE = 0.0065
COFINS_RATE = 0.03
ISS_RATE = 0.02
DEDUCOES_RECEITA = PIS_RATE + COFINS_RATE + ISS_RATE  # 5,65%

# Imposto de Renda — Lucro Presumido
BASE_PRESUMIDA_SERVICOS = 0.32   # 32% da receita = base de cálculo
ALIQUOTA_IRPJ = 0.15            # 15% normal
ALIQUOTA_IRPJ_ADICIONAL = 0.10  # 10% sobre excedente de R$240k / ano
LIMITE_ADICIONAL_ANUAL = 240_000
ALIQUOTA_CSLL = 0.09            # 9% sobre a base

# =============================================================
# 6. DEPRECIAÇÃO
# =============================================================
DEPRECIACAO_ANUAL = CAPEX_TOTAL / HORIZONTE_ANOS   # linear, 5 anos

# =============================================================
# 7. OPÇÕES REAIS — Modelo Binomial
# =============================================================
VOLATILIDADE = 0.40                                 # σ = 40% (startup)
FATOR_ALTA = math.exp(VOLATILIDADE)                 # u = e^σ ≈ 1,4918
FATOR_BAIXA = 1 / FATOR_ALTA                       # d = 1/u ≈ 0,6703

# Probabilidade neutra ao risco
# p = (e^rf − d) / (u − d)
PROB_NEUTRA_RISCO = (
    (math.exp(TAXA_LIVRE_RISCO) - FATOR_BAIXA)
    / (FATOR_ALTA - FATOR_BAIXA)
)  # ≈ 0,5948

# Opção de Expansão (Call) — MG + RJ no Ano 2
INVESTIMENTO_EXPANSAO = 2_500_000       # R$ 2,5M
FATOR_VALOR_EXPANSAO = 0.50            # expansão ≈ 50% do VPL base

# Opção de Abandono (Put) — liquidação
# Código e IP sem tração não valem nada num cenário de falência para M&A.
VALOR_RESGATE_ABANDONO = 0             # R$ 0M
