# 📈 Equity Research Tool

Ferramenta de análise fundamentalista de ações da B3 (Bolsa de Valores do Brasil) com interface web interativa.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Sobre o Projeto

Este projeto nasceu da necessidade de ter uma ferramenta simples e gratuita para análise de ações brasileiras, combinando dados de mercado com indicadores macroeconômicos. É ideal para investidores que querem:

- Analisar múltiplos fundamentalistas de empresas
- Comparar ações do mesmo setor
- Calcular preço justo usando métodos clássicos (Graham, Bazin)
- Contextualizar investimentos com dados macro (SELIC, IPCA)

---

## 🚀 Funcionalidades

### 📊 Análise Individual
- Múltiplos fundamentalistas (P/L, P/VP, EV/EBITDA, ROE, etc)
- Métricas de performance (retorno, volatilidade, Sharpe, drawdown)
- Gráficos interativos com candlestick e médias móveis
- **Valuation automatizado** com Graham e Bazin
- **Contexto macroeconômico** (SELIC, IPCA, CDI em tempo real)
- **Interpretação por setor** (compara com média setorial)

### ⚖️ Comparação de Ações
- Performance relativa normalizada (base 100)
- Tabela comparativa de fundamentos
- Gráficos de barras por indicador

### 🔍 Stock Screener
- Filtros por P/L, Dividend Yield, ROE
- Rankings automáticos: Value, Dividend, Quality
- Universo customizável de ações

---

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/Lzocatelli/equity-research.git
cd equity-research

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# Execute o app
streamlit run app.py
```

O app abrirá em `http://localhost:8501`

---

## 📁 Estrutura do Projeto

```
equity_research/
├── data/
│   ├── __init__.py
│   ├── fetcher.py      # Busca dados via yfinance
│   └── macro.py        # Dados do Banco Central (SELIC, IPCA)
├── analysis/
│   ├── __init__.py
│   ├── indicators.py   # Indicadores técnicos e performance
│   ├── screener.py     # Filtro de ações
│   └── valuation.py    # Graham, Bazin, Gordon DDM
├── visualization/
│   ├── __init__.py
│   └── charts.py       # Gráficos matplotlib
├── app.py              # Interface Streamlit
├── main.py             # CLI (modo terminal)
├── requirements.txt
└── README.md
```

---

## 📖 Glossário de Indicadores

### Múltiplos de Valuation

| Indicador | Fórmula | O que significa | Referência |
|-----------|---------|-----------------|------------|
| **P/L** | Preço ÷ LPA | Quantos anos de lucro para "pagar" a ação | < 10 barato, > 25 caro* |
| **P/VP** | Preço ÷ VPA | Preço vs patrimônio líquido por ação | < 1.5 barato, > 3 caro |
| **EV/EBITDA** | Enterprise Value ÷ EBITDA | Valor da firma vs geração de caixa | < 6 barato, > 12 caro |
| **PSR** | Market Cap ÷ Receita | Preço sobre vendas | < 1 barato, > 3 caro |

*Varia por setor: Tech aceita P/L ~25, Bancos ~7

### Indicadores de Rentabilidade

| Indicador | Fórmula | O que significa | Bom |
|-----------|---------|-----------------|-----|
| **ROE** | Lucro Líquido ÷ Patrimônio | Retorno sobre capital próprio | > 15% |
| **ROA** | Lucro Líquido ÷ Ativos | Retorno sobre ativos totais | > 5% |
| **Margem Líquida** | Lucro ÷ Receita | % da receita que vira lucro | > 10% |
| **Margem Bruta** | Lucro Bruto ÷ Receita | Eficiência na produção | > 30% |

### Indicadores de Dividendos

| Indicador | Fórmula | O que significa | Bom |
|-----------|---------|-----------------|-----|
| **Dividend Yield (DY)** | DPA ÷ Preço | Retorno em dividendos | > 6% |
| **Payout Ratio** | Dividendos ÷ Lucro | % do lucro distribuído | 30-70% |

### Métricas de Risco/Retorno

| Indicador | O que significa | Referência |
|-----------|-----------------|------------|
| **Retorno Total** | Variação % do preço no período | Compare com CDI |
| **Volatilidade** | Desvio padrão anualizado dos retornos | < 25% baixa, > 40% alta |
| **Sharpe Ratio** | (Retorno - CDI) ÷ Volatilidade | > 1 bom, > 2 excelente |
| **Max Drawdown** | Maior queda do topo ao fundo | < -20% aceitável |

---

## 💰 Modelos de Valuation

### Fórmula de Graham

Criada por Benjamin Graham, mentor de Warren Buffett.

```
Preço Justo = √(22.5 × LPA × VPA)
```

- **LPA**: Lucro por Ação (últimos 12 meses)
- **VPA**: Valor Patrimonial por Ação
- **22.5** vem de P/L = 15 e P/VP = 1.5 (15 × 1.5)

**Interpretação da Margem de Segurança:**
| Margem | Classificação |
|--------|---------------|
| > 30% | Muito barato |
| 15-30% | Barato |
| -10% a 15% | Preço justo |
| < -10% | Caro |

### Fórmula de Bazin

Criada por Décio Bazin, investidor brasileiro focado em dividendos.

```
Preço Justo = DPA ÷ 0.06
```

- **DPA**: Dividendo por Ação
- **6%**: Yield mínimo aceitável segundo Bazin

**Quando usar:** Empresas maduras e boas pagadoras de dividendos (utilities, bancos).

### Modelo de Gordon (DDM)

```
Preço Justo = DPA × (1 + g) ÷ (r - g)
```

- **g**: Taxa de crescimento dos dividendos
- **r**: Taxa de desconto (retorno exigido)

**Quando usar:** Empresas com dividendos estáveis e previsíveis.

---

## 🌍 Contexto Macroeconômico

O app busca dados em tempo real da API do Banco Central:

| Indicador | O que é | Impacto |
|-----------|---------|---------|
| **SELIC** | Taxa básica de juros | Referência para custo de oportunidade |
| **IPCA** | Inflação oficial | Corrói retornos reais |
| **CDI** | Taxa interbancária (~SELIC) | Benchmark de renda fixa |
| **Juro Real** | SELIC - IPCA | Retorno real da renda fixa |

### Por que isso importa?

- **Sharpe negativo?** Compare com a SELIC. Se a ação rendeu menos que a renda fixa, o risco não compensou.
- **SELIC alta?** Setores como varejo e imobiliário sofrem (crédito caro).
- **SELIC alta?** Bancos podem se beneficiar (spread maior).

---

## 📊 Benchmarks Setoriais

O app compara cada ação com a média do seu setor:

| Setor | P/L Médio | P/VP Médio | DY Médio |
|-------|-----------|------------|----------|
| Bancos | 7 | 1.0 | 7% |
| Energia | 6 | 1.2 | 10% |
| Tecnologia | 25 | 5.0 | 1% |
| Utilities | 10 | 1.5 | 6% |
| Consumo | 15 | 2.5 | 3% |
| Saúde | 20 | 3.5 | 2% |

*Um P/L de 20 é "caro" para um banco, mas "barato" para uma empresa de tecnologia.*

---

## 🛠️ Tecnologias

- **Python 3.8+**
- **Streamlit** - Interface web
- **yfinance** - Dados de mercado
- **Plotly** - Gráficos interativos
- **pandas/numpy** - Manipulação de dados
- **requests** - API do Banco Central

---

## ⚠️ Limitações

- **Dados do yfinance**: Algumas métricas podem não estar disponíveis para ações brasileiras
- **Rate Limit**: Yahoo Finance pode bloquear muitas requisições seguidas
- **Não é recomendação**: Use como ferramenta de estudo, não como conselho de investimento

---

## 🔜 Roadmap

- [ ] Scraping do Fundamentus (dados mais completos para B3)
- [ ] Exportar relatório em PDF
- [ ] Comparação com Ibovespa e CDI nos gráficos
- [ ] Backtesting de estratégias simples
- [ ] Alertas de preço

---

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork
2. Criar uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abrir um Pull Request

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 👤 Autor

**Zocatelli**
- GitHub: [@Lzocatelli](https://github.com/Lzocatelli)

---

## 📚 Referências

- Graham, B. - *O Investidor Inteligente*
- Bazin, D. - *Faça Fortuna com Ações*
- [API do Banco Central](https://dadosabertos.bcb.gov.br/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)

---

⭐ Se este projeto foi útil, considere dar uma estrela!
