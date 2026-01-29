# 📈 Equity Research Tool

A fundamental analysis tool for stocks with an interactive web interface. Supports both US and Brazilian (B3) stocks.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 About

This project provides a simple, free tool for stock analysis, combining market data with macroeconomic indicators. Perfect for investors who want to:

- Analyze fundamental multiples
- Compare stocks within the same sector
- Calculate fair price using classic methods (Graham, Bazin)
- Contextualize investments with macro data (interest rates, inflation)

---

## 🚀 Features

### 📊 Single Stock Analysis
- Fundamental multiples (P/E, P/B, EV/EBITDA, ROE, etc.)
- Performance metrics (return, volatility, Sharpe, drawdown)
- Interactive charts with candlestick and moving averages
- **Automated valuation** with Graham and Bazin formulas
- **Macroeconomic context** (real-time interest rates for Brazilian stocks)
- **Sector-based interpretation** (compares with sector averages)

### ⚖️ Stock Comparison
- Normalized relative performance (base 100)
- Fundamentals comparison table
- Bar charts by indicator

### 🔍 Stock Screener
- Filters by P/E, Dividend Yield, ROE
- Automatic rankings: Value, Dividend, Quality
- Customizable stock universe

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/Lzocatelli/equity-research.git
cd equity-research

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app_en.py    # English version
streamlit run app.py       # Portuguese version
```

The app will open at `http://localhost:8501`

---

## 📁 Project Structure

```
equity_research/
├── data/
│   ├── __init__.py
│   ├── fetcher.py      # Fetches data via yfinance
│   └── macro.py        # Brazilian Central Bank data (SELIC, IPCA)
├── analysis/
│   ├── __init__.py
│   ├── indicators.py   # Technical indicators and performance
│   ├── screener.py     # Stock screener
│   └── valuation.py    # Graham, Bazin, Gordon DDM
├── visualization/
│   ├── __init__.py
│   └── charts.py       # Matplotlib charts
├── app.py              # Streamlit interface (Portuguese)
├── app_en.py           # Streamlit interface (English)
├── main.py             # CLI (terminal mode)
├── requirements.txt
└── README.md
```

---

## 📖 Indicators Glossary

### Valuation Multiples

| Indicator | Formula | Meaning | Reference |
|-----------|---------|---------|-----------|
| **P/E** | Price ÷ EPS | Years of earnings to "pay" for the stock | < 10 cheap, > 25 expensive* |
| **P/B** | Price ÷ BVPS | Price vs. book value per share | < 1.5 cheap, > 3 expensive |
| **EV/EBITDA** | Enterprise Value ÷ EBITDA | Firm value vs. cash generation | < 6 cheap, > 12 expensive |
| **P/S** | Market Cap ÷ Revenue | Price to sales | < 1 cheap, > 3 expensive |

*Varies by sector: Tech accepts P/E ~25, Banks ~7

### Profitability Indicators

| Indicator | Formula | Meaning | Good |
|-----------|---------|---------|------|
| **ROE** | Net Income ÷ Equity | Return on equity | > 15% |
| **ROA** | Net Income ÷ Assets | Return on total assets | > 5% |
| **Net Margin** | Net Income ÷ Revenue | % of revenue that becomes profit | > 10% |
| **Gross Margin** | Gross Profit ÷ Revenue | Production efficiency | > 30% |

### Dividend Indicators

| Indicator | Formula | Meaning | Good |
|-----------|---------|---------|------|
| **Dividend Yield** | DPS ÷ Price | Dividend return | > 4% |
| **Payout Ratio** | Dividends ÷ Net Income | % of earnings distributed | 30-70% |

### Risk/Return Metrics

| Indicator | Meaning | Reference |
|-----------|---------|-----------|
| **Total Return** | % price change in period | Compare with risk-free rate |
| **Volatility** | Annualized standard deviation | < 25% low, > 40% high |
| **Sharpe Ratio** | (Return - Risk-free) ÷ Volatility | > 1 good, > 2 excellent |
| **Max Drawdown** | Largest peak-to-trough decline | < -20% acceptable |

---

## 💰 Valuation Models

### Graham Formula

Created by Benjamin Graham, Warren Buffett's mentor.

```
Fair Price = √(22.5 × EPS × BVPS)
```

- **EPS**: Earnings per Share (trailing 12 months)
- **BVPS**: Book Value per Share
- **22.5** comes from P/E = 15 and P/B = 1.5 (15 × 1.5)

**Margin of Safety Interpretation:**
| Margin | Classification |
|--------|----------------|
| > 30% | Very cheap |
| 15-30% | Cheap |
| -10% to 15% | Fair price |
| < -10% | Expensive |

### Bazin Formula

Created by Décio Bazin, Brazilian investor focused on dividends.

```
Fair Price = DPS ÷ 0.06
```

- **DPS**: Dividend per Share
- **6%**: Minimum acceptable yield according to Bazin

**When to use:** Mature companies with consistent dividend payments (utilities, banks).

### Gordon Model (DDM)

```
Fair Price = DPS × (1 + g) ÷ (r - g)
```

- **g**: Dividend growth rate
- **r**: Discount rate (required return)

**When to use:** Companies with stable and predictable dividends.

---

## 📊 Sector Benchmarks

The app compares each stock with its sector average:

| Sector | Avg P/E | Avg P/B | Avg DY |
|--------|---------|---------|--------|
| Banks | 7 | 1.0 | 7% |
| Energy | 6 | 1.2 | 10% |
| Technology | 25 | 5.0 | 1% |
| Utilities | 10 | 1.5 | 6% |
| Consumer | 15 | 2.5 | 3% |
| Healthcare | 20 | 3.5 | 2% |

*A P/E of 20 is "expensive" for a bank but "cheap" for a tech company.*

---

## 🛠️ Technologies

- **Python 3.8+**
- **Streamlit** - Web interface
- **yfinance** - Market data
- **Plotly** - Interactive charts
- **pandas/numpy** - Data manipulation
- **requests** - Central Bank API

---

## ⚠️ Limitations

- **yfinance data**: Some metrics may not be available for all stocks
- **Rate Limit**: Yahoo Finance may block too many consecutive requests
- **Not financial advice**: Use as a study tool, not as investment recommendation

---

## 🔜 Roadmap

- [ ] Fundamentus scraping (more complete data for Brazilian stocks)
- [ ] PDF report export
- [ ] Comparison with market indices
- [ ] Simple backtesting strategies
- [ ] Price alerts

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the project
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Zocatelli**
- GitHub: [@Lzocatelli](https://github.com/Lzocatelli)

---

## 📚 References

- Graham, B. - *The Intelligent Investor*
- Bazin, D. - *Faça Fortuna com Ações* (Brazilian classic)
- [Brazilian Central Bank API](https://dadosabertos.bcb.gov.br/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)

---

⭐ If this project was helpful, consider giving it a star!
