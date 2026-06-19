# The Ultimate Framework: Modelagem de Viabilidade Financeira (State of the Art)

Este documento não é apenas um guia, mas um **Protocolo Mestre** de arquitetura financeira. Ele detalha como estruturar, codificar e analisar projetos de viabilidade econômica com qualidade institucional (*Venture Capital* / *Investment Banking*), utilizando o poder de processamento do Python.

Este framework pode ser usado como um **Mega-Prompt** para instruir inteligências artificiais a construírem do zero simulações matemáticas complexas que vão muito além de simples planilhas de Fluxo de Caixa.

---

## 1. Arquitetura Modular em Python
Nunca escreva um modelo financeiro em um script único. A modularidade permite debugar, auditar e expandir o modelo para simulações estocásticas. A estrutura State of the Art (SotA) deve ser:

```text
/viabilidade_engine
├── premissas.py            # Variáveis macroeconômicas, taxas, prazos e assumptions
├── mercado.py              # Dimensionamento TAM/SAM/SOM e projeção de leads
├── unit_economics.py       # Dinâmica de LTV, CAC e Payback por cliente
├── receitas.py             # Curva de adoção, churn e faturamento bruto
├── despesas.py             # OPEX (stepped), CAPEX, COGS e gateway fees
├── fluxo_caixa.py          # NCG, Depreciação, Impostos e FCFF (Free Cash Flow to Firm)
├── indicadores.py          # VPL, TIR, Payback e Valor Terminal (Perpetuidade)
├── cenarios_montecarlo.py  # Simulação de Monte Carlo (Estocástica)
├── otimizacao_solver.py    # Algoritmos de Simplex para restrição de capital
├── opcoes_reais.py         # Precificação de estratégias via Árvore Binomial
└── main.py                 # Orquestrador que roda o motor e cospe os resultados
```

---

## 2. A Fundação: Premissas e o Controle do *GIGO*
O erro mais amador em modelagem é o *Garbage In, Garbage Out* (GIGO). Se as premissas são sonhadoras, o modelo é inútil.

### Onde e como buscar indicadores de base:
- **Taxa Livre de Risco (Rf):** Títulos públicos de longo prazo do país. No Brasil, olhe a curva da **NTN-B (Tesouro IPCA+)** ou a projeção da **Selic** (Banco Central / Focus).
- **Equity Risk Premium (ERP) e Country Risk Premium (CRP):** Não invente. Use as tabelas públicas do Professor **Aswath Damodaran (NYU Stern)**.
- **Beta ($\beta$):** Também de Damodaran. Avalie o beta des-alavancado do setor alvo e alavanque conforme a dívida do projeto.
- **WACC (Custo de Capital):** Utilize a fórmula clássica do CAPM ($Ke = Rf + \beta \times (ERP) + Risco\_Especifico$).
  > [!WARNING]
  > **Startups & Venture Capital:** Modelos de estágio *Seed/Early-Stage* devem punir o WACC com um "Prêmio de Mortalidade". O WACC para validação de MVP raramente deve ser menor que **40% a 50% ao ano**.

---

## 3. Dinâmica Operacional e *Unit Economics*
Para prever faturamento, modele a unidade formadora de receita.

- **Fricção e Conversão:** Em B2B, não assuma conversões acima de 3% a 5% em tráfego frio. 
- **O Risco de *Bypass* (Marketplaces):** Nunca assuma retenção de 100% do GMV (Gross Merchandise Volume). Construtoras e fornecedores tentarão transacionar por fora. Assuma *take rates* defensivos.
- **CAC e LTV:** O Custo de Aquisição deve incluir a ineficiência do vendedor e o orçamento de marketing. O LTV deve contemplar o *Churn* (evasão). Uma métrica saudável de LTV/CAC para aprovar investimentos é **> 3x**.

---

## 4. O Fluxo de Caixa Livre (FCFF)
A construção do caixa livre é onde 90% dos modelos erram por simplificação. No Python, use `numpy arrays` para calcular os 5 anos de horizonte de forma matricial.

### Elementos Inegociáveis do FCFF:
1. **Deduções Tributárias:** Receita não é caixa. Abata PIS/COFINS/ISS imediatamente. Use regras de Lucro Presumido ou Real (IRPJ e CSLL).
2. **COGS Ocultos:** Inclua custos de processamento de cartão/split de pagamento (Gateways cobram de 1% a 3%). Isso destrói a Margem Bruta de marketplaces com *take rates* baixos.
3. **Necessidade de Capital de Giro (NCG):** Contas a Receber $\times$ Contas a Pagar. Se você vende parcelado ou o gateway trava o dinheiro por 30 dias, você precisa de caixa para girar.
4. **O "Vale da Morte":** Considere capitalizar os meses pré-operacionais (Onde a receita é zero mas o time está desenvolvendo) dentro do Investimento Inicial (Ano 0).

---

## 5. Avaliação (*Valuation*) e Indicadores
Quando invocar o script de indicadores, exija:
- **Valor Terminal (Perpetuidade):** Projetos não morrem no Ano 5. Calcule o fluxo contínuo via Crescimento de Gordon: $TV = \frac{FCFF_{Ano5} \times (1+g)}{WACC - g}$.
- **TIR (Taxa Interna de Retorno):** Se a TIR > WACC, o modelo para em pé. No Python, use `scipy.optimize.brentq` (uma busca de raízes muito superior ao `np.irr` obsoleto).
- **Payback Descontado:** O tempo que o dinheiro leva para retornar, já corroído pela taxa de desconto.

---

## 6. Blindagem de Risco: O "State of the Art"
Um modelo determinístico (estático) não serve para Diretores Financeiros (CFOs). O Python permite aplicar estatística pesada:

### Programação Linear (O *Solver* de Marketing)
Use o algoritmo *Simplex/Interior Point* (via `scipy.optimize.linprog`) para garantir que o dinheiro projetado no OPEX consegue de fato comprar o número de clientes estimado. O algoritmo busca maximizar clientes sob a restrição do limite financeiro.

### Simulação de Monte Carlo
O futuro não é uma linha reta, é uma distribuição de probabilidades.
1. Configure distribuições (Ex: Normal para WACC, Triangular para Taxa de Conversão).
2. Rode `for i in range(10000)` simulando cenários aleatórios combinados.
3. Plote um histograma com `matplotlib`.
  > [!TIP]
  > O que os investidores querem ver: *Qual a probabilidade do VPL ser menor que zero?* Se o seu Monte Carlo apresentar risco zero, suas premissas estão otimistas demais (GIGO).

### Opções Reais (O Valor da Estratégia)
Use o Modelo Binomial de Cox-Ross-Rubinstein. Projetos possuem "flexibilidade gerencial" que o Fluxo Descontado não captura:
- **Opção de Abandono (Put):** O direito de vender a plataforma/código se as coisas derem errado no Ano 1. *(Nota: para startups sem tração técnica, avalie esse resgate próximo a zero).*
- **Opção de Expansão (Call):** O direito de aportar novo capital (Ex: Série A) e dobrar a operação se os primeiros resultados atingirem o pico da simulação estocástica.

---

## 7. O "Mega-Prompt" (Template para IAs)

Copie o texto abaixo e cole em um LLM (como o próprio Antigravity) sempre que quiser iniciar o planejamento de uma viabilidade extrema para um novo negócio:

> **[INÍCIO DO PROMPT]**
> Atue como um CFO Institucional e Especialista em M&A. Preciso estruturar um modelo de viabilidade econômico-financeira em Python "State of the Art" para o seguinte projeto: `[Descreva o projeto aqui]`.
> 
> A modelagem deve ser modularizada e rigorosamente conservadora, evitando "Garbage In, Garbage Out". Siga este escopo exato:
> 1. Estruture as `premissas.py` baseadas no mercado brasileiro, inferindo dados macroeconômicos (WACC calculado via CAPM com ERP de Damodaran e Prêmio de Mortalidade alto).
> 2. Modele a Receita e a Necessidade de Capital de Giro (NCG) de forma realista (considerando evasão e atraso de recebimentos). Inclua custos cruéis (Gateways de pagamentos) no COGS.
> 3. Crie o `fluxo_caixa.py` projetado em 5 anos, incluindo Valor Terminal via perpetuidade.
> 4. Calcule VPL, TIR e Payback Descontado.
> 5. Implemente um modelo estocástico de Monte Carlo (10.000 iterações) variando no mínimo 2 variáveis de alto impacto.
> 6. Opcional/Diferencial: Aplique Programação Linear para otimização de OPEX ou Teoria de Opções Reais para avaliar a flexibilidade estratégica de expansão.
> 
> Gere toda a arquitetura de módulos Python e os cálculos matriciais com a biblioteca `numpy`.
> **[FIM DO PROMPT]**
