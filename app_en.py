"""
Equity Research Tool - Streamlit App
=====================================
Web interface for stock analysis (B3 - Brazilian Stock Exchange)
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import StockFetcher
from data.macro import MacroData, get_sector_benchmark
from analysis.indicators import StockAnalyzer
from analysis.screener import StockScreener
from analysis.valuation import analisar_valuation, graham_formula_original, bazin_formula

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Equity Research Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
    }
    .positive { color: #2ecc71; }
    .negative { color: #e74c3c; }
    .neutral { color: #95a5a6; }
    .big-font { font-size: 24px !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
@st.cache_data(ttl=600)  # 10 minute cache
def fetch_stock_data(ticker: str, period: str = "1y"):
    """Fetch stock data with cache"""
    try:
        stock = StockFetcher(ticker)
        basic = stock.get_basic_info()
        fundamentals = stock.get_fundamentals()
        history = stock.get_history(period=period)
        return basic, fundamentals, history
    except Exception as e:
        if 'rate' in str(e).lower() or 'limit' in str(e).lower():
            raise Exception(f"Yahoo Finance rate limit. Please wait 1-2 minutes and try again.")
        raise e


@st.cache_data(ttl=600)
def fetch_multiple_stocks_data(tickers: list, period: str = "1y"):
    """Fetch data for multiple stocks with delay to avoid rate limit"""
    import time
    data = {}
    for i, ticker in enumerate(tickers):
        try:
            if i > 0:
                time.sleep(0.5)
            stock = StockFetcher(ticker)
            data[ticker] = {
                'basic': stock.get_basic_info(),
                'fundamentals': stock.get_fundamentals(),
                'history': stock.get_history(period=period)
            }
        except Exception as e:
            if 'rate' in str(e).lower() or 'limit' in str(e).lower():
                st.warning(f"Rate limit reached. Please wait...")
                time.sleep(5)
                try:
                    stock = StockFetcher(ticker)
                    data[ticker] = {
                        'basic': stock.get_basic_info(),
                        'fundamentals': stock.get_fundamentals(),
                        'history': stock.get_history(period=period)
                    }
                except:
                    st.warning(f"Could not fetch {ticker}")
            else:
                st.warning(f"Error fetching {ticker}: {e}")
    return data


@st.cache_data(ttl=3600)  # 1 hour cache for macro data
def fetch_macro_data():
    """Fetch macroeconomic indicators from BCB"""
    try:
        macro = MacroData()
        return macro.get_all_indicators()
    except Exception as e:
        return {'selic': 10.75, 'ipca_12m': 4.5, 'cdi': 10.65, 'cambio': 5.0, 'error': str(e)}


def format_number(value, prefix="", suffix="", decimals=2):
    """Format number for display"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if abs(value) >= 1e12:
        return f"{prefix}{value/1e12:.{decimals}f}T{suffix}"
    elif abs(value) >= 1e9:
        return f"{prefix}{value/1e9:.{decimals}f}B{suffix}"
    elif abs(value) >= 1e6:
        return f"{prefix}{value/1e6:.{decimals}f}M{suffix}"
    else:
        return f"{prefix}{value:,.{decimals}f}{suffix}"


def format_percent(value):
    """Format percentage"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value * 100:.2f}%"


def get_color(value, threshold_good=0, threshold_bad=0, invert=False):
    """Return color based on value"""
    if value is None:
        return "neutral"
    if invert:
        return "negative" if value > threshold_bad else "positive" if value < threshold_good else "neutral"
    return "positive" if value > threshold_good else "negative" if value < threshold_bad else "neutral"


def create_price_chart(history: pd.DataFrame, ticker: str, show_ma: list = [20, 50]):
    """Create interactive price chart with Plotly"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} - Price', 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=history.index,
            open=history['Open'],
            high=history['High'],
            low=history['Low'],
            close=history['Close'],
            name='OHLC'
        ),
        row=1, col=1
    )
    
    # Moving averages
    colors = {20: '#e74c3c', 50: '#f39c12', 200: '#9b59b6'}
    for period in show_ma:
        ma = history['Close'].rolling(period).mean()
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=ma,
                mode='lines',
                name=f'MA{period}',
                line=dict(color=colors.get(period, '#1f77b4'), width=1)
            ),
            row=1, col=1
        )
    
    # Volume
    colors_vol = ['#2ecc71' if c >= o else '#e74c3c' 
                  for c, o in zip(history['Close'], history['Open'])]
    fig.add_trace(
        go.Bar(
            x=history.index,
            y=history['Volume'],
            marker_color=colors_vol,
            name='Volume',
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_returns_chart(history: pd.DataFrame, ticker: str):
    """Create cumulative returns chart"""
    returns = history['Close'].pct_change()
    cum_returns = (1 + returns).cumprod() - 1
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=history.index,
        y=cum_returns * 100,
        mode='lines',
        fill='tozeroy',
        name='Cumulative Return',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title=f'{ticker} - Cumulative Return',
        yaxis_title='Return (%)',
        template='plotly_white',
        height=400
    )
    
    return fig


def create_comparison_chart(histories: dict, normalize: bool = True):
    """Create comparison chart for multiple stocks"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, (ticker, history) in enumerate(histories.items()):
        prices = history['Close']
        if normalize:
            prices = prices / prices.iloc[0] * 100
        
        fig.add_trace(go.Scatter(
            x=history.index,
            y=prices,
            mode='lines',
            name=ticker,
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    
    title = 'Performance Comparison' + (' (Base 100)' if normalize else '')
    fig.update_layout(
        title=title,
        yaxis_title='Base 100' if normalize else 'Price',
        template='plotly_white',
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_fundamentals_chart(data: pd.DataFrame, metric: str, title: str):
    """Create bar chart for fundamentals comparison"""
    fig = go.Figure()
    
    colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in data[metric]]
    
    fig.add_trace(go.Bar(
        x=data['ticker'],
        y=data[metric],
        marker_color=colors,
        text=[f'{v:.2f}' for v in data[metric]],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=400
    )
    
    return fig


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("📈 Equity Research")
    st.markdown("---")
    
    # Page selection
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📊 Single Stock", "⚖️ Compare Stocks", "🔍 Screener"],
        index=0
    )
    
    st.markdown("---")
    
    # Period
    period_options = {
        "1 month": "1mo",
        "3 months": "3mo",
        "6 months": "6mo",
        "1 year": "1y",
        "2 years": "2y",
        "5 years": "5y"
    }
    selected_period = st.selectbox(
        "Analysis period",
        options=list(period_options.keys()),
        index=3  # Default: 1 year
    )
    period = period_options[selected_period]
    
    st.markdown("---")
    st.markdown("**Popular tickers:**")
    st.code("AAPL, MSFT, GOOGL, AMZN\nITUB4.SA, PETR4.SA, VALE3.SA")
    
    st.markdown("---")
    if st.button("🔄 Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
    st.caption("Use if you receive rate limit errors")
    
    st.markdown("---")
    st.caption("Developed by Zocatelli")
    st.caption("[GitHub](https://github.com/Lzocatelli)")


# ============================================================
# PAGES
# ============================================================

# HOME
if page == "🏠 Home":
    st.title("📈 Equity Research Tool")
    st.markdown("### Fundamental analysis tool for stocks")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Single Stock Analysis")
        st.markdown("""
        - Fundamental multiples
        - Performance metrics
        - Interactive charts
        - Automated valuation
        """)
    
    with col2:
        st.markdown("### ⚖️ Compare Stocks")
        st.markdown("""
        - Relative performance
        - Multiples comparison
        - Risk/return analysis
        - Comparative charts
        """)
    
    with col3:
        st.markdown("### 🔍 Screener")
        st.markdown("""
        - Fundamental filters
        - Automatic rankings
        - Value, Dividend, Quality
        - Customizable universe
        """)
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### 🚀 Quick Analysis")
    quick_ticker = st.text_input("Enter a ticker for quick analysis:", value="AAPL").upper()
    
    if st.button("Analyze", type="primary"):
        with st.spinner(f"Fetching data for {quick_ticker}..."):
            try:
                basic, fund, history = fetch_stock_data(quick_ticker, period)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Price", f"${basic['preco_atual']:.2f}" if '.SA' not in quick_ticker else f"R$ {basic['preco_atual']:.2f}")
                col2.metric("P/E", f"{fund['pl']:.2f}" if fund['pl'] else "N/A")
                col3.metric("Div Yield", format_percent(fund['dividend_yield']))
                col4.metric("ROE", format_percent(fund['roe']))
                
                st.plotly_chart(create_price_chart(history, quick_ticker), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error fetching {quick_ticker}: {e}")


# SINGLE STOCK ANALYSIS
elif page == "📊 Single Stock":
    st.title("📊 Single Stock Analysis")
    
    ticker = st.text_input("Enter ticker:", value="AAPL").upper()
    
    if st.button("Analyze", type="primary") or ticker:
        with st.spinner(f"Loading data for {ticker}..."):
            try:
                basic, fund, history = fetch_stock_data(ticker, period)
                analyzer = StockAnalyzer(history)
                stats = analyzer.get_summary_stats()
                
                # Detect currency
                is_brazilian = '.SA' in ticker or ticker.endswith('.SA')
                currency = "R$" if is_brazilian else "$"
                
                # Header with basic info
                st.markdown(f"## {basic['nome']}")
                st.markdown(f"**Sector:** {basic['setor']} | **Industry:** {basic['industria']}")
                
                st.markdown("---")
                
                # Main metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                col1.metric(
                    "Current Price",
                    f"{currency} {basic['preco_atual']:.2f}",
                    f"{stats['retorno_total']*100:.1f}% ({selected_period})"
                )
                col2.metric("Market Cap", format_number(basic['market_cap'], prefix=f"{currency} "))
                col3.metric("P/E", f"{fund['pl']:.2f}" if fund['pl'] else "N/A")
                col4.metric("P/B", f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A")
                col5.metric("Dividend Yield", format_percent(fund['dividend_yield']))
                
                st.markdown("---")
                
                # Fetch macro data for context
                macro_data = fetch_macro_data()
                
                # Tabs
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "📈 Charts", "📋 Fundamentals", "📊 Performance", 
                    "💰 Valuation", "🌍 Macro Context", "💡 Interpretation"
                ])
                
                with tab1:
                    # Moving averages selector
                    ma_options = st.multiselect(
                        "Moving Averages:",
                        [20, 50, 100, 200],
                        default=[20, 50]
                    )
                    
                    st.plotly_chart(
                        create_price_chart(history, ticker, ma_options),
                        use_container_width=True
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(create_returns_chart(history, ticker), use_container_width=True)
                    
                    with col2:
                        # Drawdown chart
                        cummax = history['Close'].cummax()
                        drawdown = (history['Close'] - cummax) / cummax * 100
                        
                        fig_dd = go.Figure()
                        fig_dd.add_trace(go.Scatter(
                            x=history.index,
                            y=drawdown,
                            fill='tozeroy',
                            fillcolor='rgba(231, 76, 60, 0.3)',
                            line=dict(color='#e74c3c'),
                            name='Drawdown'
                        ))
                        fig_dd.update_layout(
                            title=f'{ticker} - Drawdown',
                            yaxis_title='Drawdown (%)',
                            template='plotly_white',
                            height=400
                        )
                        st.plotly_chart(fig_dd, use_container_width=True)
                
                with tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Valuation Multiples")
                        fund_data = {
                            "Indicator": ["P/E", "P/B", "EV/EBITDA", "P/S"],
                            "Value": [
                                f"{fund['pl']:.2f}" if fund['pl'] else "N/A",
                                f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A",
                                f"{fund['ev_ebitda']:.2f}" if fund.get('ev_ebitda') else "N/A",
                                f"{fund['psr']:.2f}" if fund.get('psr') else "N/A"
                            ]
                        }
                        st.table(pd.DataFrame(fund_data))
                    
                    with col2:
                        st.markdown("### Profitability")
                        rent_data = {
                            "Indicator": ["ROE", "ROA", "Net Margin", "Gross Margin", "Dividend Yield", "Payout"],
                            "Value": [
                                format_percent(fund['roe']),
                                format_percent(fund.get('roa')),
                                format_percent(fund['margem_liquida']),
                                format_percent(fund.get('margem_bruta')),
                                format_percent(fund['dividend_yield']),
                                format_percent(fund['payout_ratio'])
                            ]
                        }
                        st.table(pd.DataFrame(rent_data))
                    
                    st.markdown("### Financial Data")
                    col1, col2 = st.columns(2)
                    with col1:
                        fin_data = {
                            "Item": ["EPS", "Book Value/Share", "Total Revenue", "Net Income"],
                            "Value": [
                                f"{currency} {fund['lpa']:.2f}" if fund['lpa'] else "N/A",
                                f"{currency} {fund['vpa']:.2f}" if fund['vpa'] else "N/A",
                                format_number(fund['receita_total'], prefix=f"{currency} "),
                                format_number(fund['lucro_liquido'], prefix=f"{currency} ")
                            ]
                        }
                        st.table(pd.DataFrame(fin_data))
                    with col2:
                        fin_data2 = {
                            "Item": ["EBITDA", "Enterprise Value", "Debt/Equity"],
                            "Value": [
                                format_number(fund.get('ebitda'), prefix=f"{currency} "),
                                format_number(fund.get('enterprise_value'), prefix=f"{currency} "),
                                f"{fund['divida_patrimonio']:.2f}" if fund.get('divida_patrimonio') else "N/A"
                            ]
                        }
                        st.table(pd.DataFrame(fin_data2))
                
                with tab3:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Total Return", format_percent(stats['retorno_total']))
                    col2.metric("Annualized Return", format_percent(stats['retorno_anualizado']))
                    col3.metric("Volatility", format_percent(stats['volatilidade_anual']))
                    col4.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Max Drawdown", format_percent(stats['max_drawdown']))
                    col2.metric("52w High", f"{currency} {stats['preco_max_52w']:.2f}")
                    col3.metric("52w Low", f"{currency} {stats['preco_min_52w']:.2f}")
                    col4.metric("Avg Volume", format_number(stats['volume_medio']))
                    
                    # Returns distribution
                    returns = history['Close'].pct_change().dropna() * 100
                    fig_hist = px.histogram(
                        returns,
                        nbins=50,
                        title="Daily Returns Distribution",
                        labels={'value': 'Return (%)', 'count': 'Frequency'}
                    )
                    fig_hist.add_vline(x=returns.mean(), line_dash="dash", line_color="red",
                                       annotation_text=f"Mean: {returns.mean():.2f}%")
                    fig_hist.update_layout(template='plotly_white', showlegend=False)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with tab4:
                    st.markdown("### 💰 Valuation - Fair Price")
                    
                    # Get sector benchmark for normalized DY
                    benchmark = get_sector_benchmark(basic['setor'])
                    
                    # Calculate DPA (Dividend per Share)
                    dpa = 0
                    if fund['dividend_yield'] and basic['preco_atual']:
                        dpa = fund['dividend_yield'] * basic['preco_atual']
                    
                    selic = macro_data.get('selic', 10.75) or 10.75
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Graham Formula")
                        st.markdown("""
                        **√(22.5 × EPS × BVPS)**
                        
                        Benjamin Graham, Warren Buffett's mentor, created this formula 
                        to find stocks with margin of safety.
                        """)
                        
                        pj_graham = graham_formula_original(fund['lpa'], fund['vpa'])
                        if pj_graham:
                            margem = (pj_graham - basic['preco_atual']) / pj_graham * 100
                            
                            st.metric(
                                "Fair Price (Graham)",
                                f"{currency} {pj_graham:.2f}",
                                f"{margem:.1f}% {'discount' if margem > 0 else 'premium'}"
                            )
                            
                            if margem >= 30:
                                st.success("🟢 VERY CHEAP - High margin of safety")
                            elif margem >= 15:
                                st.success("🟢 CHEAP - Good margin of safety")
                            elif margem >= -10:
                                st.info("🟡 FAIR PRICE")
                            else:
                                st.warning("🔴 EXPENSIVE - Above fair price")
                        else:
                            st.warning("Insufficient data (negative or unavailable EPS/BVPS)")
                    
                    with col2:
                        st.markdown("#### Bazin Formula")
                        st.markdown("""
                        **DPS / 6%**
                        
                        Décio Bazin, Brazilian investor, argued that 
                        a stock is only worth buying with minimum 6% dividend yield.
                        """)
                        
                        # Check if DY is abnormally high (extraordinary dividend)
                        dy_atual = fund['dividend_yield'] or 0
                        dy_extraordinario = dy_atual > 0.15  # DY > 15% is suspicious
                        
                        if dy_extraordinario and dy_atual > 0:
                            st.warning(f"""
                            ⚠️ **DY of {dy_atual*100:.1f}% seems extraordinary!**
                            
                            Probably includes special dividends (extra payouts, reserve distribution).
                            Bazin assumes **recurring and sustainable** dividends.
                            """)
                            
                            # Calculate with real DY (distorted)
                            pj_bazin_real = bazin_formula(dpa)
                            
                            # Suggest normalized DY based on sector
                            dy_normalizado = benchmark.get('dy_medio', 0.06)
                            dpa_normalizado = dy_normalizado * basic['preco_atual']
                            pj_bazin_normalizado = bazin_formula(dpa_normalizado)
                            
                            st.markdown(f"**Using normalized sector DY ({dy_normalizado*100:.0f}%):**")
                            
                            if pj_bazin_normalizado:
                                margem = (pj_bazin_normalizado - basic['preco_atual']) / pj_bazin_normalizado * 100
                                
                                st.metric(
                                    "Fair Price (Bazin Normalized)",
                                    f"{currency} {pj_bazin_normalizado:.2f}",
                                    f"{margem:.1f}% {'discount' if margem > 0 else 'premium'}"
                                )
                                
                                if margem >= 30:
                                    st.success("🟢 VERY CHEAP for dividends (normalized)")
                                elif margem >= 15:
                                    st.success("🟢 CHEAP for dividends (normalized)")
                                elif margem >= -10:
                                    st.info("🟡 FAIR PRICE for dividends (normalized)")
                                else:
                                    st.warning("🔴 DY below 6% at current price (normalized)")
                            
                            # Show distorted value for reference
                            with st.expander("View calculation with current DY (distorted)"):
                                st.caption(f"Current DPS: {currency} {dpa:.2f} | Fair Price: {currency} {pj_bazin_real:.2f}")
                                st.caption("This value is inflated by non-recurring dividends.")
                        
                        else:
                            # Normal DY - use standard calculation
                            pj_bazin = bazin_formula(dpa)
                            if pj_bazin:
                                margem = (pj_bazin - basic['preco_atual']) / pj_bazin * 100
                                
                                st.metric(
                                    "Fair Price (Bazin)",
                                    f"{currency} {pj_bazin:.2f}",
                                    f"{margem:.1f}% {'discount' if margem > 0 else 'premium'}"
                                )
                                
                                if margem >= 30:
                                    st.success("🟢 VERY CHEAP for dividends")
                                elif margem >= 15:
                                    st.success("🟢 CHEAP for dividends")
                                elif margem >= -10:
                                    st.info("🟡 FAIR PRICE for dividends")
                                else:
                                    st.warning("🔴 DY below 6% at current price")
                            else:
                                st.warning("Company doesn't pay dividends or data unavailable")
                    
                    # Summary
                    st.markdown("---")
                    st.markdown("#### 📊 Data used in calculation")
                    calc_data = {
                        "Variable": ["EPS", "BVPS", "DPS (estimated)", "Current Price", "Risk-free Rate"],
                        "Value": [
                            f"{currency} {fund['lpa']:.2f}" if fund['lpa'] else "N/A",
                            f"{currency} {fund['vpa']:.2f}" if fund['vpa'] else "N/A",
                            f"{currency} {dpa:.2f}" if dpa else "N/A",
                            f"{currency} {basic['preco_atual']:.2f}",
                            f"{selic:.2f}%" if is_brazilian else "~5%"
                        ]
                    }
                    st.table(pd.DataFrame(calc_data))
                    
                    st.caption("⚠️ These models are simplified. Use as reference, not as investment advice.")
                
                with tab5:
                    st.markdown("### 🌍 Macroeconomic Context")
                    
                    if is_brazilian:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        selic = macro_data.get('selic')
                        ipca = macro_data.get('ipca_12m')
                        cdi = macro_data.get('cdi')
                        cambio = macro_data.get('cambio')
                        
                        col1.metric("SELIC", f"{selic:.2f}%" if selic else "N/A")
                        col2.metric("IPCA 12m", f"{ipca:.2f}%" if ipca else "N/A")
                        col3.metric("CDI", f"{cdi:.2f}%" if cdi else "N/A")
                        col4.metric("USD/BRL", f"R$ {cambio:.2f}" if cambio else "N/A")
                        
                        st.markdown("---")
                        
                        st.markdown("#### 📈 Investment Impact")
                        
                        # Real interest rate
                        if selic and ipca:
                            juro_real = ((1 + selic/100) / (1 + ipca/100) - 1) * 100
                            st.metric("Real Interest Rate", f"{juro_real:.2f}%", 
                                      "Return above inflation" if juro_real > 0 else "Return below inflation")
                        
                        # Sharpe analysis considering CDI
                        st.markdown("---")
                        st.markdown("#### 🎯 Sharpe Ratio in Context")
                        
                        if cdi:
                            st.markdown(f"""
                            The **Sharpe Ratio** of **{stats['sharpe_ratio']:.2f}** considers SELIC of **{selic:.2f}%** as risk-free rate.
                            
                            **Interpretation:**
                            """)
                            
                            retorno_anual = stats['retorno_anualizado'] * 100
                            
                            if retorno_anual > selic:
                                st.success(f"""
                                ✅ **Return ({retorno_anual:.1f}%) > SELIC ({selic:.1f}%)**
                                
                                The stock outperformed fixed income in the period. Risk premium was rewarded.
                                """)
                            else:
                                st.warning(f"""
                                ⚠️ **Return ({retorno_anual:.1f}%) < SELIC ({selic:.1f}%)**
                                
                                Fixed income would have been better in the period. Consider if risk was worth it.
                                """)
                    else:
                        st.info("Macro context is currently available for Brazilian stocks only. For US stocks, consider the Fed Funds Rate (~5.25-5.50%) as the risk-free rate benchmark.")
                        
                        st.markdown("#### 🎯 Sharpe Ratio Interpretation")
                        st.markdown(f"""
                        The **Sharpe Ratio** of **{stats['sharpe_ratio']:.2f}** measures risk-adjusted return.
                        
                        - **> 1.0**: Good risk-adjusted return
                        - **> 2.0**: Excellent risk-adjusted return
                        - **< 0**: Underperformed risk-free rate
                        """)
                    
                    # Sector sensitivity
                    st.markdown("---")
                    st.markdown("#### 🏦 Sector Sensitivity")
                    
                    setor = basic['setor']
                    
                    sensibilidade_juros = {
                        'Financial Services': ('High', 'Banks benefit from high rates (spread)'),
                        'Banks': ('High', 'Banking spread increases with high rates'),
                        'Real Estate': ('High negative', 'High rates make financing expensive'),
                        'Utilities': ('Medium', 'Predictable revenue, but debt sensitive to rates'),
                        'Consumer Cyclical': ('High negative', 'Consumption drops with expensive credit'),
                        'Technology': ('Medium negative', 'Valuations compress with high rates'),
                        'Consumer Defensive': ('Low', 'Inelastic demand'),
                        'Energy': ('Low', 'Commodities follow their own cycle'),
                        'Basic Materials': ('Low', 'More tied to global cycle'),
                    }
                    
                    if setor in sensibilidade_juros:
                        sens, explicacao = sensibilidade_juros[setor]
                        st.info(f"**{setor}** — Interest rate sensitivity: **{sens}**\n\n{explicacao}")
                    else:
                        st.info(f"Sector: {setor}")
                
                with tab6:
                    st.markdown("### 💡 Automated Interpretation")
                    
                    # Get sector benchmark
                    setor = basic['setor']
                    benchmark = get_sector_benchmark(setor)
                    
                    st.markdown(f"**Sector:** {setor}")
                    st.markdown(f"**Sector benchmark:** Average P/E ~{benchmark['pl_medio']}, Average P/B ~{benchmark['pvp_medio']}, Average DY ~{benchmark['dy_medio']*100:.1f}%")
                    
                    st.markdown("---")
                    
                    interpretations = []
                    
                    # P/E compared with sector
                    if fund['pl'] and fund['pl'] > 0:
                        pl_vs_setor = fund['pl'] / benchmark['pl_medio']
                        if pl_vs_setor < 0.7:
                            interpretations.append(("✅", "P/E below sector", 
                                f"P/E of {fund['pl']:.1f} is {(1-pl_vs_setor)*100:.0f}% below sector average ({benchmark['pl_medio']})"))
                        elif pl_vs_setor > 1.5:
                            interpretations.append(("⚠️", "P/E above sector", 
                                f"P/E of {fund['pl']:.1f} is {(pl_vs_setor-1)*100:.0f}% above sector average ({benchmark['pl_medio']})"))
                        else:
                            interpretations.append(("➖", "P/E aligned with sector", 
                                f"P/E of {fund['pl']:.1f} close to sector average ({benchmark['pl_medio']})"))
                    elif fund['pl'] and fund['pl'] < 0:
                        interpretations.append(("🔴", "Negative P/E", "Company with loss in the period"))
                    
                    # P/B compared with sector
                    if fund['pvp'] and fund['pvp'] > 0:
                        pvp_vs_setor = fund['pvp'] / benchmark['pvp_medio']
                        if pvp_vs_setor < 0.7:
                            interpretations.append(("✅", "P/B below sector", 
                                f"P/B of {fund['pvp']:.2f} suggests book value discount"))
                        elif pvp_vs_setor > 1.5:
                            interpretations.append(("⚠️", "P/B above sector", 
                                f"P/B of {fund['pvp']:.2f} may indicate overvaluation"))
                    
                    # ROE
                    if fund['roe']:
                        if fund['roe'] > 0.20:
                            interpretations.append(("✅", "Excellent ROE (>20%)", "High return on equity"))
                        elif fund['roe'] > 0.15:
                            interpretations.append(("✅", "Good ROE (>15%)", "Good return on equity"))
                        elif fund['roe'] < 0.08:
                            interpretations.append(("⚠️", "Low ROE (<8%)", "Low profitability"))
                    
                    # DY compared with sector
                    if fund['dividend_yield']:
                        dy_vs_setor = fund['dividend_yield'] / benchmark['dy_medio'] if benchmark['dy_medio'] > 0 else 1
                        if dy_vs_setor > 1.5:
                            interpretations.append(("✅", "DY above sector", 
                                f"Dividend Yield of {fund['dividend_yield']*100:.2f}% above sector average"))
                        if fund['dividend_yield'] > 0.08:
                            interpretations.append(("✅", "Very high DY (>8%)", "Excellent dividend payer"))
                    
                    # Performance vs risk-free
                    risk_free = (macro_data.get('selic', 10.75) or 10.75) if is_brazilian else 5.0
                    if stats['retorno_anualizado'] > risk_free/100:
                        interpretations.append(("✅", "Beat risk-free rate", 
                            f"Return of {stats['retorno_anualizado']*100:.1f}% exceeded risk-free ({risk_free:.1f}%)"))
                    elif stats['retorno_total'] < -0.20:
                        interpretations.append(("⚠️", "Significant decline", 
                            f"Stock dropped {abs(stats['retorno_total'])*100:.1f}% in the period"))
                    
                    # Sharpe
                    if stats['sharpe_ratio'] > 1.5:
                        interpretations.append(("✅", "Excellent Sharpe (>1.5)", "Great risk-adjusted return"))
                    elif stats['sharpe_ratio'] > 1:
                        interpretations.append(("✅", "Good Sharpe (>1)", "Good risk-adjusted return"))
                    elif stats['sharpe_ratio'] < 0:
                        interpretations.append(("⚠️", "Negative Sharpe", "Return below risk-free rate"))
                    
                    # Volatility
                    if stats['volatilidade_anual'] > 0.50:
                        interpretations.append(("⚠️", "High volatility (>50%)", "High risk stock"))
                    elif stats['volatilidade_anual'] < 0.25:
                        interpretations.append(("✅", "Low volatility (<25%)", "Defensive stock"))
                    
                    for emoji, title, desc in interpretations:
                        st.markdown(f"{emoji} **{title}** — {desc}")
                    
                    if not interpretations:
                        st.info("Insufficient data for automated interpretation.")
                
            except Exception as e:
                st.error(f"Error analyzing {ticker}: {e}")
                st.exception(e)


# COMPARE STOCKS
elif page == "⚖️ Compare Stocks":
    st.title("⚖️ Compare Stocks")
    
    # Ticker input
    tickers_input = st.text_input(
        "Enter tickers separated by comma:",
        value="AAPL, MSFT, GOOGL, AMZN"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    
    if len(tickers) < 2:
        st.warning("Enter at least 2 tickers to compare.")
    else:
        if st.button("Compare", type="primary"):
            with st.spinner("Loading data..."):
                try:
                    data = fetch_multiple_stocks_data(tickers, period)
                    
                    if len(data) < 2:
                        st.error("Could not load enough data.")
                    else:
                        # Performance chart
                        histories = {t: d['history'] for t, d in data.items()}
                        st.plotly_chart(
                            create_comparison_chart(histories, normalize=True),
                            use_container_width=True
                        )
                        
                        # Fundamentals comparison table
                        st.markdown("### 📋 Fundamentals Comparison")
                        
                        # Detect currency
                        first_ticker = list(data.keys())[0]
                        is_brazilian = '.SA' in first_ticker
                        currency = "R$" if is_brazilian else "$"
                        
                        comp_data = []
                        for ticker, d in data.items():
                            fund = d['fundamentals']
                            basic = d['basic']
                            analyzer = StockAnalyzer(d['history'])
                            stats = analyzer.get_summary_stats()
                            
                            comp_data.append({
                                'Ticker': ticker,
                                'Price': f"{currency} {basic['preco_atual']:.2f}",
                                'P/E': f"{fund['pl']:.2f}" if fund['pl'] else "N/A",
                                'P/B': f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A",
                                'DY': format_percent(fund['dividend_yield']),
                                'ROE': format_percent(fund['roe']),
                                'Return': format_percent(stats['retorno_total']),
                                'Volatility': format_percent(stats['volatilidade_anual']),
                                'Sharpe': f"{stats['sharpe_ratio']:.2f}"
                            })
                        
                        df_comp = pd.DataFrame(comp_data)
                        st.dataframe(df_comp, use_container_width=True, hide_index=True)
                        
                        # Comparative bar charts
                        st.markdown("### 📊 Visual Comparison")
                        
                        metrics_data = []
                        for ticker, d in data.items():
                            fund = d['fundamentals']
                            metrics_data.append({
                                'ticker': ticker,
                                'pl': fund['pl'] if fund['pl'] else 0,
                                'pvp': fund['pvp'] if fund['pvp'] else 0,
                                'dy': (fund['dividend_yield'] or 0) * 100,
                                'roe': (fund['roe'] or 0) * 100
                            })
                        
                        df_metrics = pd.DataFrame(metrics_data)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_pl = px.bar(df_metrics, x='ticker', y='pl', title='P/E Ratio',
                                           color='pl', color_continuous_scale='RdYlGn_r')
                            fig_pl.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_pl, use_container_width=True)
                        
                        with col2:
                            fig_roe = px.bar(df_metrics, x='ticker', y='roe', title='ROE (%)',
                                            color='roe', color_continuous_scale='RdYlGn')
                            fig_roe.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_roe, use_container_width=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_pvp = px.bar(df_metrics, x='ticker', y='pvp', title='P/B Ratio',
                                            color='pvp', color_continuous_scale='RdYlGn_r')
                            fig_pvp.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_pvp, use_container_width=True)
                        
                        with col2:
                            fig_dy = px.bar(df_metrics, x='ticker', y='dy', title='Dividend Yield (%)',
                                           color='dy', color_continuous_scale='RdYlGn')
                            fig_dy.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_dy, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.exception(e)


# SCREENER
elif page == "🔍 Screener":
    st.title("🔍 Stock Screener")
    
    st.markdown("Filter stocks by fundamental criteria.")
    
    # Stock universe
    default_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 
                       'TSLA', 'JPM', 'V', 'JNJ', 'WMT', 'PG',
                       'UNH', 'HD', 'BAC', 'XOM', 'PFE', 'KO']
    
    with st.expander("⚙️ Configure stock universe"):
        tickers_input = st.text_area(
            "Tickers (one per line or comma-separated):",
            value=", ".join(default_tickers)
        )
        tickers = [t.strip().upper() for t in tickers_input.replace('\n', ',').split(',') if t.strip()]
    
    st.markdown("### 🎯 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pl_range = st.slider("P/E", 0.0, 50.0, (0.0, 25.0))
        use_pl = st.checkbox("Apply P/E filter", value=True)
    
    with col2:
        dy_min = st.slider("Minimum Dividend Yield (%)", 0.0, 15.0, 0.0)
        use_dy = st.checkbox("Apply DY filter", value=False)
    
    with col3:
        roe_min = st.slider("Minimum ROE (%)", 0.0, 40.0, 0.0)
        use_roe = st.checkbox("Apply ROE filter", value=False)
    
    if st.button("🔍 Run Screener", type="primary"):
        with st.spinner(f"Analyzing {len(tickers)} stocks..."):
            try:
                # Fetch data
                progress_bar = st.progress(0)
                results = []
                
                for i, ticker in enumerate(tickers):
                    try:
                        stock = StockFetcher(ticker)
                        basic = stock.get_basic_info()
                        fund = stock.get_fundamentals()
                        
                        results.append({
                            'ticker': ticker,
                            'name': basic['nome'],
                            'sector': basic['setor'],
                            'price': basic['preco_atual'],
                            'pl': fund['pl'],
                            'pvp': fund['pvp'],
                            'dy': fund['dividend_yield'],
                            'roe': fund['roe'],
                            'margin': fund['margem_liquida']
                        })
                    except:
                        pass
                    
                    progress_bar.progress((i + 1) / len(tickers))
                
                df = pd.DataFrame(results)
                
                # Apply filters
                if use_pl and not df.empty:
                    df = df[(df['pl'] >= pl_range[0]) & (df['pl'] <= pl_range[1]) & (df['pl'] > 0)]
                if use_dy and not df.empty:
                    df = df[df['dy'] >= dy_min / 100]
                if use_roe and not df.empty:
                    df = df[df['roe'] >= roe_min / 100]
                
                st.success(f"Found {len(df)} stocks matching criteria.")
                
                if not df.empty:
                    # Format for display
                    df_display = df.copy()
                    df_display['price'] = df_display['price'].apply(lambda x: f"${x:.2f}" if x else "N/A")
                    df_display['pl'] = df_display['pl'].apply(lambda x: f"{x:.2f}" if x else "N/A")
                    df_display['pvp'] = df_display['pvp'].apply(lambda x: f"{x:.2f}" if x else "N/A")
                    df_display['dy'] = df_display['dy'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    df_display['roe'] = df_display['roe'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    df_display['margin'] = df_display['margin'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    
                    df_display.columns = ['Ticker', 'Name', 'Sector', 'Price', 'P/E', 'P/B', 'DY', 'ROE', 'Net Margin']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Rankings
                    st.markdown("---")
                    st.markdown("### 🏆 Rankings")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**💰 Lowest P/E (Value)**")
                        value = df[df['pl'] > 0].nsmallest(5, 'pl')[['ticker', 'pl']]
                        value['pl'] = value['pl'].apply(lambda x: f"{x:.2f}")
                        st.dataframe(value, hide_index=True)
                    
                    with col2:
                        st.markdown("**💵 Highest DY (Dividends)**")
                        div = df[df['dy'] > 0].nlargest(5, 'dy')[['ticker', 'dy']]
                        div['dy'] = div['dy'].apply(lambda x: f"{x*100:.2f}%")
                        st.dataframe(div, hide_index=True)
                    
                    with col3:
                        st.markdown("**⭐ Highest ROE (Quality)**")
                        qual = df[df['roe'] > 0].nlargest(5, 'roe')[['ticker', 'roe']]
                        qual['roe'] = qual['roe'].apply(lambda x: f"{x*100:.2f}%")
                        st.dataframe(qual, hide_index=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
