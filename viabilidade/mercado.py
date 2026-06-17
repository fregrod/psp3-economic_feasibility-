"""
=================================================================
MERCADO — Dimensionamento TAM / SAM / SOM
=================================================================
Calcula o tamanho de mercado bottom-up para o marketplace de
material de construção.
=================================================================
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from premissas import (
    TOTAL_OBRAS_ANO_BRASIL, GASTO_MATERIAIS_POR_OBRA,
    AREA_TOTAL_MEDIA, FEE_MARKETPLACE, FEE_POR_OBRA,
    PAVIMENTOS_MEDIO_POR_OBRA, AREA_POR_PAVIMENTO_M2,
    CUSTO_MEDIO_M2, PCT_CUSTO_MATERIAIS,
)


def calcular_mercado():
    """
    Dimensionamento de mercado com abordagem bottom-up.

    Retorna dict com TAM, SAM, SOM e métricas auxiliares.
    """
    # ---------------------------------------------------------
    # 1. TAM — Total Addressable Market
    #    Todos os gastos em materiais de construção / ano no Brasil
    # ---------------------------------------------------------
    tam = TOTAL_OBRAS_ANO_BRASIL * GASTO_MATERIAIS_POR_OBRA
    # → 50.000 × R$ 1.282.500 = R$ 64,125 B

    # ---------------------------------------------------------
    # 2. SAM — Serviceable Addressable Market
    #    20% do TAM — obras formais (construtoras com CNPJ)
    # ---------------------------------------------------------
    pct_obras_formais = 0.20
    sam = tam * pct_obras_formais
    # → R$ 12,825 B

    # ---------------------------------------------------------
    # 3. SOM — Serviceable Obtainable Market
    #    Meta de captura: 5% do TAM em 5 anos
    # ---------------------------------------------------------
    pct_som_sobre_tam = 0.05
    som = tam * pct_som_sobre_tam
    # → R$ 3,206 B

    # ---------------------------------------------------------
    # 4. Potencial de receita (fee) sobre cada camada
    # ---------------------------------------------------------
    fee_potencial_tam = tam * FEE_MARKETPLACE
    fee_potencial_sam = sam * FEE_MARKETPLACE
    fee_potencial_som = som * FEE_MARKETPLACE

    return {
        # Mercado
        "tam": tam,
        "sam": sam,
        "som": som,
        "pct_obras_formais": pct_obras_formais,
        "pct_som_sobre_tam": pct_som_sobre_tam,
        # Métricas por obra
        "area_total_media": AREA_TOTAL_MEDIA,
        "gasto_materiais_por_obra": GASTO_MATERIAIS_POR_OBRA,
        "fee_por_obra": FEE_POR_OBRA,
        # Fee potencial
        "fee_potencial_tam": fee_potencial_tam,
        "fee_potencial_sam": fee_potencial_sam,
        "fee_potencial_som": fee_potencial_som,
    }


# --- Execução direta (para teste) ---
if __name__ == "__main__":
    m = calcular_mercado()
    print("━" * 60)
    print("DIMENSIONAMENTO DE MERCADO")
    print("━" * 60)
    print(f"  Área total média por obra:  {m['area_total_media']:,.0f} m²")
    print(f"  Gasto materiais / obra:     R$ {m['gasto_materiais_por_obra']:,.2f}")
    print(f"  Fee / obra (2,5%):          R$ {m['fee_por_obra']:,.2f}")
    print()
    print(f"  TAM (total):                R$ {m['tam']/1e9:,.1f} B")
    print(f"  SAM (endereçável, 20%):     R$ {m['sam']/1e9:,.1f} B")
    print(f"  SOM (meta 5 anos, 5%):      R$ {m['som']/1e9:,.1f} B")
    print()
    print(f"  Fee pot. TAM:               R$ {m['fee_potencial_tam']/1e9:,.1f} B")
    print(f"  Fee pot. SAM:               R$ {m['fee_potencial_sam']/1e6:,.0f} M")
    print(f"  Fee pot. SOM:               R$ {m['fee_potencial_som']/1e6:,.0f} M")
