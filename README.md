# 📈 Equity Research Tool

Ferramenta de análise fundamentalista de ações da B3 (Bolsa de Valores do Brasil).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Funcionalidades

### Análise Individual
- Informações gerais da empresa (setor, market cap, volume)
- Múltiplos fundamentalistas (P/L, P/VP, ROE, DY)
- Métricas de performance (retorno, volatilidade, Sharpe, drawdown)
- Interpretação automática dos indicadores
- Gráficos de preço com médias móveis

### Comparação de Ações
- Comparação lado a lado de múltiplos
- Performance relativa (base 100)
- Análise de risco/retorno entre ativos

### Stock Screener
- Filtro por critérios fundamentalistas
- Rankings: Value, Dividend, Quality
- Universo customizável de ações

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/Lzocatelli/equity-research.git
cd equity-research

# Instale as dependências
pip install -r requirements.txt
```

## 📊 Uso

### Modo Interativo
```bash
python main.py
```

### Análise Programática
```python
from data.fetcher import StockFetcher
from analysis.indicators import StockAnalyzer
from visualization.charts import StockCharts

# Buscar dados
stock = StockFetcher("ITUB4")
print(stock.get_basic_info())
print(stock.get_fundamentals())

# Análise de performance
history = stock.get_history(period="1y")
analyzer = StockAnalyzer(history)
print(analyzer.get_summary_stats())

# Gráficos
charts = StockCharts(history, "ITUB4")
charts.plot_price(show_ma=[20, 50, 200])
```

### Screener
```python
from analysis.screener import StockScreener

screener = StockScreener()
screener.fetch_all_data()

# Filtrar ações
value_stocks = screener.filter(pl_max=10, pl_min=0, dy_min=0.04)
top_dividends = screener.dividend_stocks(top_n=10)
```

## 📁 Estrutura do Projeto

```
equity_research/
├── data/
│   ├── __init__.py
│   └── fetcher.py          # Busca dados via yfinance
├── analysis/
│   ├── __init__.py
│   ├── indicators.py       # Indicadores técnicos e performance
│   └── screener.py         # Filtro de ações
├── visualization/
│   ├── __init__.py
│   └── charts.py           # Gráficos matplotlib
├── reports/                # Gráficos gerados
├── main.py                 # Script principal
├── requirements.txt
└── README.md
```

## 📈 Indicadores Disponíveis

### Fundamentalistas
| Indicador | Descrição |
|-----------|-----------|
| P/L | Preço / Lucro por Ação |
| P/VP | Preço / Valor Patrimonial |
| ROE | Retorno sobre Patrimônio |
| DY | Dividend Yield |
| Margem Líquida | Lucro Líquido / Receita |

### Performance
| Indicador | Descrição |
|-----------|-----------|
| Retorno Total | Variação percentual do preço |
| Volatilidade | Desvio padrão anualizado |
| Sharpe Ratio | Retorno ajustado ao risco |
| Max Drawdown | Maior queda do topo |

## 🛠️ Tecnologias

- **Python 3.8+**
- **pandas** - Manipulação de dados
- **yfinance** - Dados de mercado
- **matplotlib** - Visualização
- **numpy** - Cálculos numéricos
- **tabulate** - Formatação de tabelas

## 📝 Exemplos de Output

### Análise ITUB4
```
============================================================
  MÚLTIPLOS FUNDAMENTALISTAS
============================================================
P/L (Preço/Lucro)                    7.85
P/VP (Preço/Valor Patrimonial)       1.42
Dividend Yield                       6.25%
ROE                                  18.50%

============================================================
  INTERPRETAÇÃO
============================================================
✅ P/L baixo (<10): Ação pode estar barata
✅ ROE alto (>15%): Boa rentabilidade sobre patrimônio
✅ DY alto (>6%): Boa pagadora de dividendos
```

## 🔜 Roadmap

- [ ] Exportar relatório em PDF
- [ ] Interface web com Streamlit
- [ ] Backtesting de estratégias
- [ ] Integração com dados do Fundamentus
- [ ] Alertas de preço

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 👤 Autor

**Zocatelli**
- GitHub: [@Lzocatelli](https://github.com/Lzocatelli)

---

⭐ Se este projeto foi útil, considere dar uma estrela!
