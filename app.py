"""
Equity Research Tool - Streamlit App
=====================================
Interface web para análise de ações da B3
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

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import StockFetcher
from data.macro import MacroData, get_sector_benchmark
from analysis.indicators import StockAnalyzer
from analysis.screener import StockScreener
from analysis.valuation import analisar_valuation, graham_formula_original, bazin_formula

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Equity Research Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
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
# FUNÇÕES AUXILIARES
# ============================================================
@st.cache_data(ttl=600)  # Cache por 10 minutos
def fetch_stock_data(ticker: str, period: str = "1y"):
    """Busca dados da ação com cache"""
    try:
        stock = StockFetcher(ticker)
        basic = stock.get_basic_info()
        fundamentals = stock.get_fundamentals()
        history = stock.get_history(period=period)
        return basic, fundamentals, history
    except Exception as e:
        if 'rate' in str(e).lower() or 'limit' in str(e).lower():
            raise Exception(f"Rate limit do Yahoo Finance. Aguarde 1-2 minutos e tente novamente.")
        raise e


@st.cache_data(ttl=600)
def fetch_multiple_stocks_data(tickers: list, period: str = "1y"):
    """Busca dados de múltiplas ações com delay para evitar rate limit"""
    import time
    data = {}
    for i, ticker in enumerate(tickers):
        try:
            # Delay entre requisições para evitar rate limit
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
                st.warning(f"Rate limit atingido. Aguarde um momento...")
                time.sleep(5)
                try:
                    stock = StockFetcher(ticker)
                    data[ticker] = {
                        'basic': stock.get_basic_info(),
                        'fundamentals': stock.get_fundamentals(),
                        'history': stock.get_history(period=period)
                    }
                except:
                    st.warning(f"Não foi possível buscar {ticker}")
            else:
                st.warning(f"Erro ao buscar {ticker}: {e}")
    return data


@st.cache_data(ttl=3600)  # Cache de 1 hora para dados macro
def fetch_macro_data():
    """Busca indicadores macroeconômicos do BCB"""
    try:
        macro = MacroData()
        return macro.get_all_indicators()
    except Exception as e:
        return {'selic': 10.75, 'ipca_12m': 4.5, 'cdi': 10.65, 'cambio': 5.0, 'erro': str(e)}


def format_number(value, prefix="", suffix="", decimals=2):
    """Formata número para exibição"""
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
    """Formata percentual"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value * 100:.2f}%"


def get_color(value, threshold_good=0, threshold_bad=0, invert=False):
    """Retorna cor baseada no valor"""
    if value is None:
        return "neutral"
    if invert:
        return "negative" if value > threshold_bad else "positive" if value < threshold_good else "neutral"
    return "positive" if value > threshold_good else "negative" if value < threshold_bad else "neutral"


def create_price_chart(history: pd.DataFrame, ticker: str, show_ma: list = [20, 50]):
    """Cria gráfico de preço interativo com Plotly"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} - Preço', 'Volume')
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
    
    # Médias móveis
    colors = {20: '#e74c3c', 50: '#f39c12', 200: '#9b59b6'}
    for period in show_ma:
        ma = history['Close'].rolling(period).mean()
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=ma,
                mode='lines',
                name=f'MM{period}',
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
    """Cria gráfico de retornos acumulados"""
    returns = history['Close'].pct_change()
    cum_returns = (1 + returns).cumprod() - 1
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=history.index,
        y=cum_returns * 100,
        mode='lines',
        fill='tozeroy',
        name='Retorno Acumulado',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title=f'{ticker} - Retorno Acumulado',
        yaxis_title='Retorno (%)',
        template='plotly_white',
        height=400
    )
    
    return fig


def create_comparison_chart(histories: dict, normalize: bool = True):
    """Cria gráfico comparativo de múltiplas ações"""
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
    
    title = 'Comparação de Performance' + (' (Base 100)' if normalize else '')
    fig.update_layout(
        title=title,
        yaxis_title='Base 100' if normalize else 'Preço (R$)',
        template='plotly_white',
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_fundamentals_chart(data: pd.DataFrame, metric: str, title: str):
    """Cria gráfico de barras para comparação de fundamentos"""
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
    
    # Seleção de página
    page = st.radio(
        "Navegação",
        ["🏠 Home", "📊 Análise Individual", "⚖️ Comparar Ações", "🔍 Screener"],
        index=0
    )
    
    st.markdown("---")
    
    # Período
    period_options = {
        "1 mês": "1mo",
        "3 meses": "3mo",
        "6 meses": "6mo",
        "1 ano": "1y",
        "2 anos": "2y",
        "5 anos": "5y"
    }
    selected_period = st.selectbox(
        "Período de análise",
        options=list(period_options.keys()),
        index=3  # Default: 1 ano
    )
    period = period_options[selected_period]
    
    st.markdown("---")
    st.markdown("**Ações populares:**")
    st.code("ITUB4, BBDC4, PETR4, VALE3\nWEGE3, ABEV3, B3SA3, RENT3")
    
    st.markdown("---")
    st.caption("Desenvolvido por Zocatelli")
    st.caption("[GitHub](https://github.com/Lzocatelli)")
    
    st.markdown("---")
    if st.button("🔄 Limpar Cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")
    st.caption("Use se receber erro de rate limit")


# ============================================================
# PÁGINAS
# ============================================================

# HOME
if page == "🏠 Home":
    st.title("📈 Equity Research Tool")
    st.markdown("### Ferramenta de análise fundamentalista de ações da B3")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Análise Individual")
        st.markdown("""
        - Múltiplos fundamentalistas
        - Métricas de performance
        - Gráficos interativos
        - Interpretação automática
        """)
    
    with col2:
        st.markdown("### ⚖️ Comparar Ações")
        st.markdown("""
        - Performance relativa
        - Comparação de múltiplos
        - Análise risco/retorno
        - Gráficos comparativos
        """)
    
    with col3:
        st.markdown("### 🔍 Screener")
        st.markdown("""
        - Filtros por fundamentos
        - Rankings automáticos
        - Value, Dividend, Quality
        - Universo customizável
        """)
    
    st.markdown("---")
    
    # Quick stats de mercado
    st.markdown("### 🚀 Análise Rápida")
    quick_ticker = st.text_input("Digite um ticker para análise rápida:", value="ITUB4").upper()
    
    if st.button("Analisar", type="primary"):
        with st.spinner(f"Buscando dados de {quick_ticker}..."):
            try:
                basic, fund, history = fetch_stock_data(quick_ticker, period)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Preço", f"R$ {basic['preco_atual']:.2f}")
                col2.metric("P/L", f"{fund['pl']:.2f}" if fund['pl'] else "N/A")
                col3.metric("DY", format_percent(fund['dividend_yield']))
                col4.metric("ROE", format_percent(fund['roe']))
                
                st.plotly_chart(create_price_chart(history, quick_ticker), use_container_width=True)
                
            except Exception as e:
                st.error(f"Erro ao buscar {quick_ticker}: {e}")


# ANÁLISE INDIVIDUAL
elif page == "📊 Análise Individual":
    st.title("📊 Análise Individual")
    
    ticker = st.text_input("Digite o ticker:", value="ITUB4").upper()
    
    if st.button("Analisar", type="primary") or ticker:
        with st.spinner(f"Carregando dados de {ticker}..."):
            try:
                basic, fund, history = fetch_stock_data(ticker, period)
                analyzer = StockAnalyzer(history)
                stats = analyzer.get_summary_stats()
                
                # Header com info básica
                st.markdown(f"## {basic['nome']}")
                st.markdown(f"**Setor:** {basic['setor']} | **Indústria:** {basic['industria']}")
                
                st.markdown("---")
                
                # Métricas principais
                col1, col2, col3, col4, col5 = st.columns(5)
                
                col1.metric(
                    "Preço Atual",
                    f"R$ {basic['preco_atual']:.2f}",
                    f"{stats['retorno_total']*100:.1f}% ({selected_period})"
                )
                col2.metric("Market Cap", format_number(basic['market_cap'], prefix="R$ "))
                col3.metric("P/L", f"{fund['pl']:.2f}" if fund['pl'] else "N/A")
                col4.metric("P/VP", f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A")
                col5.metric("Dividend Yield", format_percent(fund['dividend_yield']))
                
                st.markdown("---")
                
                # Busca dados macro para contexto
                macro_data = fetch_macro_data()
                
                # Tabs
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "📈 Gráficos", "📋 Fundamentos", "📊 Performance", 
                    "💰 Valuation", "🌍 Contexto Macro", "💡 Interpretação"
                ])
                
                with tab1:
                    # Seletor de médias móveis
                    ma_options = st.multiselect(
                        "Médias Móveis:",
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
                        st.markdown("### Múltiplos de Valuation")
                        fund_data = {
                            "Indicador": ["P/L", "P/VP", "EV/EBITDA", "PSR"],
                            "Valor": [
                                f"{fund['pl']:.2f}" if fund['pl'] else "N/A",
                                f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A",
                                f"{fund['ev_ebitda']:.2f}" if fund.get('ev_ebitda') else "N/A",
                                f"{fund['psr']:.2f}" if fund.get('psr') else "N/A"
                            ]
                        }
                        st.table(pd.DataFrame(fund_data))
                    
                    with col2:
                        st.markdown("### Rentabilidade")
                        rent_data = {
                            "Indicador": ["ROE", "ROA", "Margem Líquida", "Margem Bruta", "Dividend Yield", "Payout"],
                            "Valor": [
                                format_percent(fund['roe']),
                                format_percent(fund.get('roa')),
                                format_percent(fund['margem_liquida']),
                                format_percent(fund.get('margem_bruta')),
                                format_percent(fund['dividend_yield']),
                                format_percent(fund['payout_ratio'])
                            ]
                        }
                        st.table(pd.DataFrame(rent_data))
                    
                    st.markdown("### Dados Financeiros")
                    col1, col2 = st.columns(2)
                    with col1:
                        fin_data = {
                            "Item": ["LPA", "VPA", "Receita Total", "Lucro Líquido"],
                            "Valor": [
                                f"R$ {fund['lpa']:.2f}" if fund['lpa'] else "N/A",
                                f"R$ {fund['vpa']:.2f}" if fund['vpa'] else "N/A",
                                format_number(fund['receita_total'], prefix="R$ "),
                                format_number(fund['lucro_liquido'], prefix="R$ ")
                            ]
                        }
                        st.table(pd.DataFrame(fin_data))
                    with col2:
                        fin_data2 = {
                            "Item": ["EBITDA", "Enterprise Value", "Dívida/Patrimônio"],
                            "Valor": [
                                format_number(fund.get('ebitda'), prefix="R$ "),
                                format_number(fund.get('enterprise_value'), prefix="R$ "),
                                f"{fund['divida_patrimonio']:.2f}" if fund.get('divida_patrimonio') else "N/A"
                            ]
                        }
                        st.table(pd.DataFrame(fin_data2))
                
                with tab3:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Retorno Total", format_percent(stats['retorno_total']))
                    col2.metric("Retorno Anualizado", format_percent(stats['retorno_anualizado']))
                    col3.metric("Volatilidade", format_percent(stats['volatilidade_anual']))
                    col4.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Max Drawdown", format_percent(stats['max_drawdown']))
                    col2.metric("Máx 52 sem", f"R$ {stats['preco_max_52w']:.2f}")
                    col3.metric("Mín 52 sem", f"R$ {stats['preco_min_52w']:.2f}")
                    col4.metric("Vol. Médio", format_number(stats['volume_medio']))
                    
                    # Distribuição de retornos
                    returns = history['Close'].pct_change().dropna() * 100
                    fig_hist = px.histogram(
                        returns,
                        nbins=50,
                        title="Distribuição de Retornos Diários",
                        labels={'value': 'Retorno (%)', 'count': 'Frequência'}
                    )
                    fig_hist.add_vline(x=returns.mean(), line_dash="dash", line_color="red",
                                       annotation_text=f"Média: {returns.mean():.2f}%")
                    fig_hist.update_layout(template='plotly_white', showlegend=False)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with tab4:
                    st.markdown("### 💰 Valuation - Preço Justo")
                    
                    # Busca benchmark do setor para DY normalizado
                    benchmark = get_sector_benchmark(basic['setor'])
                    
                    # Calcula DPA (Dividendo por Ação) se tiver DY e preço
                    dpa = 0
                    if fund['dividend_yield'] and basic['preco_atual']:
                        dpa = fund['dividend_yield'] * basic['preco_atual']
                    
                    selic = macro_data.get('selic', 10.75) or 10.75
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Fórmula de Graham")
                        st.markdown("""
                        **√(22.5 × LPA × VPA)**
                        
                        Benjamin Graham, mentor de Warren Buffett, criou esta fórmula 
                        para encontrar ações com margem de segurança.
                        """)
                        
                        pj_graham = graham_formula_original(fund['lpa'], fund['vpa'])
                        if pj_graham:
                            margem = (pj_graham - basic['preco_atual']) / pj_graham * 100
                            
                            st.metric(
                                "Preço Justo (Graham)",
                                f"R$ {pj_graham:.2f}",
                                f"{margem:.1f}% {'desconto' if margem > 0 else 'prêmio'}"
                            )
                            
                            if margem >= 30:
                                st.success("🟢 MUITO BARATO - Margem de segurança alta")
                            elif margem >= 15:
                                st.success("🟢 BARATO - Boa margem de segurança")
                            elif margem >= -10:
                                st.info("🟡 PREÇO JUSTO")
                            else:
                                st.warning("🔴 CARO - Acima do preço justo")
                        else:
                            st.warning("Dados insuficientes (LPA ou VPA negativo/indisponível)")
                    
                    with col2:
                        st.markdown("#### Fórmula de Bazin")
                        st.markdown("""
                        **DPA / 6%**
                        
                        Décio Bazin, investidor brasileiro, defendia que 
                        uma ação só vale a pena com DY mínimo de 6%.
                        """)
                        
                        # Verifica se DY está anormalmente alto (dividendo extraordinário)
                        dy_atual = fund['dividend_yield'] or 0
                        dy_extraordinario = dy_atual > 0.15  # DY > 15% é suspeito
                        
                        if dy_extraordinario and dy_atual > 0:
                            st.warning(f"""
                            ⚠️ **DY de {dy_atual*100:.1f}% parece extraordinário!**
                            
                            Provavelmente inclui dividendos especiais (JCP extra, distribuição de reservas).
                            Bazin assume dividendos **recorrentes e sustentáveis**.
                            """)
                            
                            # Calcula com DY real (distorcido)
                            pj_bazin_real = bazin_formula(dpa)
                            
                            # Sugere DY normalizado baseado no setor
                            dy_normalizado = benchmark.get('dy_medio', 0.06)
                            dpa_normalizado = dy_normalizado * basic['preco_atual']
                            pj_bazin_normalizado = bazin_formula(dpa_normalizado)
                            
                            st.markdown(f"**Usando DY normalizado do setor ({dy_normalizado*100:.0f}%):**")
                            
                            if pj_bazin_normalizado:
                                margem = (pj_bazin_normalizado - basic['preco_atual']) / pj_bazin_normalizado * 100
                                
                                st.metric(
                                    "Preço Justo (Bazin Normalizado)",
                                    f"R$ {pj_bazin_normalizado:.2f}",
                                    f"{margem:.1f}% {'desconto' if margem > 0 else 'prêmio'}"
                                )
                                
                                if margem >= 30:
                                    st.success("🟢 MUITO BARATO para dividendos (normalizado)")
                                elif margem >= 15:
                                    st.success("🟢 BARATO para dividendos (normalizado)")
                                elif margem >= -10:
                                    st.info("🟡 PREÇO JUSTO para dividendos (normalizado)")
                                else:
                                    st.warning("🔴 DY abaixo de 6% no preço atual (normalizado)")
                            
                            # Mostra o valor distorcido para referência
                            with st.expander("Ver cálculo com DY atual (distorcido)"):
                                st.caption(f"DPA atual: R$ {dpa:.2f} | Preço Justo: R$ {pj_bazin_real:.2f}")
                                st.caption("Este valor está inflado por dividendos não-recorrentes.")
                        
                        else:
                            # DY normal - usa cálculo padrão
                            pj_bazin = bazin_formula(dpa)
                            if pj_bazin:
                                margem = (pj_bazin - basic['preco_atual']) / pj_bazin * 100
                                
                                st.metric(
                                    "Preço Justo (Bazin)",
                                    f"R$ {pj_bazin:.2f}",
                                    f"{margem:.1f}% {'desconto' if margem > 0 else 'prêmio'}"
                                )
                                
                                if margem >= 30:
                                    st.success("🟢 MUITO BARATO para dividendos")
                                elif margem >= 15:
                                    st.success("🟢 BARATO para dividendos")
                                elif margem >= -10:
                                    st.info("🟡 PREÇO JUSTO para dividendos")
                                else:
                                    st.warning("🔴 DY abaixo de 6% no preço atual")
                            else:
                                st.warning("Empresa não paga dividendos ou dados indisponíveis")
                    
                    # Resumo
                    st.markdown("---")
                    st.markdown("#### 📊 Dados utilizados no cálculo")
                    calc_data = {
                        "Variável": ["LPA", "VPA", "DPA (estimado)", "Preço Atual", "SELIC"],
                        "Valor": [
                            f"R$ {fund['lpa']:.2f}" if fund['lpa'] else "N/A",
                            f"R$ {fund['vpa']:.2f}" if fund['vpa'] else "N/A",
                            f"R$ {dpa:.2f}" if dpa else "N/A",
                            f"R$ {basic['preco_atual']:.2f}",
                            f"{selic:.2f}%"
                        ]
                    }
                    st.table(pd.DataFrame(calc_data))
                    
                    st.caption("⚠️ Estes modelos são simplificados. Use como referência, não como recomendação de investimento.")
                
                with tab5:
                    st.markdown("### 🌍 Contexto Macroeconômico")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    selic = macro_data.get('selic')
                    ipca = macro_data.get('ipca_12m')
                    cdi = macro_data.get('cdi')
                    cambio = macro_data.get('cambio')
                    
                    col1.metric("SELIC", f"{selic:.2f}%" if selic else "N/A")
                    col2.metric("IPCA 12m", f"{ipca:.2f}%" if ipca else "N/A")
                    col3.metric("CDI", f"{cdi:.2f}%" if cdi else "N/A")
                    col4.metric("Dólar", f"R$ {cambio:.2f}" if cambio else "N/A")
                    
                    st.markdown("---")
                    
                    st.markdown("#### 📈 Impacto no Investimento")
                    
                    # Juro real
                    if selic and ipca:
                        juro_real = ((1 + selic/100) / (1 + ipca/100) - 1) * 100
                        st.metric("Juro Real", f"{juro_real:.2f}%", 
                                  "Retorno acima da inflação" if juro_real > 0 else "Retorno abaixo da inflação")
                    
                    # Análise do Sharpe considerando CDI
                    st.markdown("---")
                    st.markdown("#### 🎯 Sharpe Ratio em Contexto")
                    
                    if cdi:
                        st.markdown(f"""
                        O **Sharpe Ratio** de **{stats['sharpe_ratio']:.2f}** considera a SELIC de **{selic:.2f}%** como taxa livre de risco.
                        
                        **Interpretação:**
                        """)
                        
                        retorno_anual = stats['retorno_anualizado'] * 100
                        
                        if retorno_anual > selic:
                            st.success(f"""
                            ✅ **Retorno ({retorno_anual:.1f}%) > SELIC ({selic:.1f}%)**
                            
                            A ação superou a renda fixa no período. O prêmio de risco foi recompensado.
                            """)
                        else:
                            st.warning(f"""
                            ⚠️ **Retorno ({retorno_anual:.1f}%) < SELIC ({selic:.1f}%)**
                            
                            A renda fixa teria sido melhor no período. Considere se o risco valeu a pena.
                            """)
                    
                    # Setor e sensibilidade a juros
                    st.markdown("---")
                    st.markdown("#### 🏦 Sensibilidade Setorial")
                    
                    setor = basic['setor']
                    
                    sensibilidade_juros = {
                        'Financial Services': ('Alta', 'Bancos se beneficiam de juros altos (spread)'),
                        'Banks': ('Alta', 'Spread bancário aumenta com SELIC alta'),
                        'Real Estate': ('Alta negativa', 'Juros altos encarecem financiamentos'),
                        'Utilities': ('Média', 'Receitas previsíveis, mas dívida sensível a juros'),
                        'Consumer Cyclical': ('Alta negativa', 'Consumo cai com crédito caro'),
                        'Technology': ('Média negativa', 'Valuations comprimem com juros altos'),
                        'Consumer Defensive': ('Baixa', 'Demanda inelástica'),
                        'Energy': ('Baixa', 'Commodities seguem ciclo próprio'),
                        'Basic Materials': ('Baixa', 'Mais ligado a ciclo global'),
                    }
                    
                    if setor in sensibilidade_juros:
                        sens, explicacao = sensibilidade_juros[setor]
                        st.info(f"**{setor}** — Sensibilidade a juros: **{sens}**\n\n{explicacao}")
                    else:
                        st.info(f"Setor: {setor}")
                
                with tab6:
                    st.markdown("### 💡 Interpretação Automática")
                    
                    # Busca benchmark do setor
                    setor = basic['setor']
                    benchmark = get_sector_benchmark(setor)
                    
                    st.markdown(f"**Setor:** {setor}")
                    st.markdown(f"**Referência setorial:** P/L médio ~{benchmark['pl_medio']}, P/VP médio ~{benchmark['pvp_medio']}, DY médio ~{benchmark['dy_medio']*100:.1f}%")
                    
                    st.markdown("---")
                    
                    interpretations = []
                    
                    # P/L comparado com setor
                    if fund['pl'] and fund['pl'] > 0:
                        pl_vs_setor = fund['pl'] / benchmark['pl_medio']
                        if pl_vs_setor < 0.7:
                            interpretations.append(("✅", "P/L abaixo do setor", 
                                f"P/L de {fund['pl']:.1f} está {(1-pl_vs_setor)*100:.0f}% abaixo da média do setor ({benchmark['pl_medio']})"))
                        elif pl_vs_setor > 1.5:
                            interpretations.append(("⚠️", "P/L acima do setor", 
                                f"P/L de {fund['pl']:.1f} está {(pl_vs_setor-1)*100:.0f}% acima da média do setor ({benchmark['pl_medio']})"))
                        else:
                            interpretations.append(("➖", "P/L alinhado ao setor", 
                                f"P/L de {fund['pl']:.1f} próximo à média do setor ({benchmark['pl_medio']})"))
                    elif fund['pl'] and fund['pl'] < 0:
                        interpretations.append(("🔴", "P/L negativo", "Empresa com prejuízo no período"))
                    
                    # P/VP comparado com setor
                    if fund['pvp'] and fund['pvp'] > 0:
                        pvp_vs_setor = fund['pvp'] / benchmark['pvp_medio']
                        if pvp_vs_setor < 0.7:
                            interpretations.append(("✅", "P/VP abaixo do setor", 
                                f"P/VP de {fund['pvp']:.2f} sugere desconto patrimonial"))
                        elif pvp_vs_setor > 1.5:
                            interpretations.append(("⚠️", "P/VP acima do setor", 
                                f"P/VP de {fund['pvp']:.2f} pode indicar sobrevalorização"))
                    
                    # ROE
                    if fund['roe']:
                        if fund['roe'] > 0.20:
                            interpretations.append(("✅", "ROE excelente (>20%)", "Alta rentabilidade sobre patrimônio"))
                        elif fund['roe'] > 0.15:
                            interpretations.append(("✅", "ROE bom (>15%)", "Boa rentabilidade sobre patrimônio"))
                        elif fund['roe'] < 0.08:
                            interpretations.append(("⚠️", "ROE baixo (<8%)", "Baixa rentabilidade"))
                    
                    # DY comparado com setor
                    if fund['dividend_yield']:
                        dy_vs_setor = fund['dividend_yield'] / benchmark['dy_medio'] if benchmark['dy_medio'] > 0 else 1
                        if dy_vs_setor > 1.5:
                            interpretations.append(("✅", "DY acima do setor", 
                                f"Dividend Yield de {fund['dividend_yield']*100:.2f}% acima da média setorial"))
                        if fund['dividend_yield'] > 0.08:
                            interpretations.append(("✅", "DY muito alto (>8%)", "Excelente pagadora de dividendos"))
                    
                    # Performance vs CDI
                    selic = macro_data.get('selic', 10.75) or 10.75
                    if stats['retorno_anualizado'] > selic/100:
                        interpretations.append(("✅", "Bateu o CDI", 
                            f"Retorno de {stats['retorno_anualizado']*100:.1f}% superou a SELIC ({selic:.1f}%)"))
                    elif stats['retorno_total'] < -0.20:
                        interpretations.append(("⚠️", "Queda significativa", 
                            f"Ação caiu {abs(stats['retorno_total'])*100:.1f}% no período"))
                    
                    # Sharpe
                    if stats['sharpe_ratio'] > 1.5:
                        interpretations.append(("✅", "Sharpe excelente (>1.5)", "Ótimo retorno ajustado ao risco"))
                    elif stats['sharpe_ratio'] > 1:
                        interpretations.append(("✅", "Sharpe bom (>1)", "Bom retorno ajustado ao risco"))
                    elif stats['sharpe_ratio'] < 0:
                        interpretations.append(("⚠️", "Sharpe negativo", "Retorno inferior ao CDI"))
                    
                    # Volatilidade
                    if stats['volatilidade_anual'] > 0.50:
                        interpretations.append(("⚠️", "Alta volatilidade (>50%)", "Ação com alto risco"))
                    elif stats['volatilidade_anual'] < 0.25:
                        interpretations.append(("✅", "Baixa volatilidade (<25%)", "Ação defensiva"))
                    
                    for emoji, title, desc in interpretations:
                        st.markdown(f"{emoji} **{title}** — {desc}")
                    
                    if not interpretations:
                        st.info("Dados insuficientes para interpretação automática.")
                
            except Exception as e:
                st.error(f"Erro ao analisar {ticker}: {e}")
                st.exception(e)


# COMPARAR AÇÕES
elif page == "⚖️ Comparar Ações":
    st.title("⚖️ Comparar Ações")
    
    # Input de tickers
    tickers_input = st.text_input(
        "Digite os tickers separados por vírgula:",
        value="ITUB4, BBDC4, BBAS3, SANB11"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    
    if len(tickers) < 2:
        st.warning("Digite pelo menos 2 tickers para comparar.")
    else:
        if st.button("Comparar", type="primary"):
            with st.spinner("Carregando dados..."):
                try:
                    data = fetch_multiple_stocks_data(tickers, period)
                    
                    if len(data) < 2:
                        st.error("Não foi possível carregar dados suficientes.")
                    else:
                        # Gráfico de performance
                        histories = {t: d['history'] for t, d in data.items()}
                        st.plotly_chart(
                            create_comparison_chart(histories, normalize=True),
                            use_container_width=True
                        )
                        
                        # Tabela comparativa de fundamentos
                        st.markdown("### 📋 Comparação de Fundamentos")
                        
                        comp_data = []
                        for ticker, d in data.items():
                            fund = d['fundamentals']
                            basic = d['basic']
                            analyzer = StockAnalyzer(d['history'])
                            stats = analyzer.get_summary_stats()
                            
                            comp_data.append({
                                'Ticker': ticker,
                                'Preço': f"R$ {basic['preco_atual']:.2f}",
                                'P/L': f"{fund['pl']:.2f}" if fund['pl'] else "N/A",
                                'P/VP': f"{fund['pvp']:.2f}" if fund['pvp'] else "N/A",
                                'DY': format_percent(fund['dividend_yield']),
                                'ROE': format_percent(fund['roe']),
                                'Retorno': format_percent(stats['retorno_total']),
                                'Volatilidade': format_percent(stats['volatilidade_anual']),
                                'Sharpe': f"{stats['sharpe_ratio']:.2f}"
                            })
                        
                        df_comp = pd.DataFrame(comp_data)
                        st.dataframe(df_comp, use_container_width=True, hide_index=True)
                        
                        # Gráficos de barras comparativos
                        st.markdown("### 📊 Comparação Visual")
                        
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
                            fig_pl = px.bar(df_metrics, x='ticker', y='pl', title='P/L',
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
                            fig_pvp = px.bar(df_metrics, x='ticker', y='pvp', title='P/VP',
                                            color='pvp', color_continuous_scale='RdYlGn_r')
                            fig_pvp.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_pvp, use_container_width=True)
                        
                        with col2:
                            fig_dy = px.bar(df_metrics, x='ticker', y='dy', title='Dividend Yield (%)',
                                           color='dy', color_continuous_scale='RdYlGn')
                            fig_dy.update_layout(template='plotly_white', showlegend=False)
                            st.plotly_chart(fig_dy, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
                    st.exception(e)


# SCREENER
elif page == "🔍 Screener":
    st.title("🔍 Stock Screener")
    
    st.markdown("Filtre ações da B3 por critérios fundamentalistas.")
    
    # Lista de ações para screening
    default_tickers = ['ITUB4', 'BBDC4', 'BBAS3', 'PETR4', 'VALE3', 'WEGE3', 
                       'ABEV3', 'B3SA3', 'RENT3', 'EQTL3', 'SUZB3', 'JBSS3',
                       'ELET3', 'PRIO3', 'RADL3', 'RAIL3', 'VIVT3', 'TOTS3']
    
    with st.expander("⚙️ Configurar universo de ações"):
        tickers_input = st.text_area(
            "Tickers (um por linha ou separados por vírgula):",
            value=", ".join(default_tickers)
        )
        tickers = [t.strip().upper() for t in tickers_input.replace('\n', ',').split(',') if t.strip()]
    
    st.markdown("### 🎯 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pl_range = st.slider("P/L", 0.0, 50.0, (0.0, 20.0))
        use_pl = st.checkbox("Aplicar filtro P/L", value=True)
    
    with col2:
        dy_min = st.slider("Dividend Yield mínimo (%)", 0.0, 15.0, 0.0)
        use_dy = st.checkbox("Aplicar filtro DY", value=False)
    
    with col3:
        roe_min = st.slider("ROE mínimo (%)", 0.0, 40.0, 0.0)
        use_roe = st.checkbox("Aplicar filtro ROE", value=False)
    
    if st.button("🔍 Executar Screener", type="primary"):
        with st.spinner(f"Analisando {len(tickers)} ações..."):
            try:
                # Busca dados
                progress_bar = st.progress(0)
                results = []
                
                for i, ticker in enumerate(tickers):
                    try:
                        stock = StockFetcher(ticker)
                        basic = stock.get_basic_info()
                        fund = stock.get_fundamentals()
                        
                        results.append({
                            'ticker': ticker,
                            'nome': basic['nome'],
                            'setor': basic['setor'],
                            'preco': basic['preco_atual'],
                            'pl': fund['pl'],
                            'pvp': fund['pvp'],
                            'dy': fund['dividend_yield'],
                            'roe': fund['roe'],
                            'margem': fund['margem_liquida']
                        })
                    except:
                        pass
                    
                    progress_bar.progress((i + 1) / len(tickers))
                
                df = pd.DataFrame(results)
                
                # Aplica filtros
                if use_pl and not df.empty:
                    df = df[(df['pl'] >= pl_range[0]) & (df['pl'] <= pl_range[1]) & (df['pl'] > 0)]
                if use_dy and not df.empty:
                    df = df[df['dy'] >= dy_min / 100]
                if use_roe and not df.empty:
                    df = df[df['roe'] >= roe_min / 100]
                
                st.success(f"Encontradas {len(df)} ações que atendem aos critérios.")
                
                if not df.empty:
                    # Formata para exibição
                    df_display = df.copy()
                    df_display['preco'] = df_display['preco'].apply(lambda x: f"R$ {x:.2f}" if x else "N/A")
                    df_display['pl'] = df_display['pl'].apply(lambda x: f"{x:.2f}" if x else "N/A")
                    df_display['pvp'] = df_display['pvp'].apply(lambda x: f"{x:.2f}" if x else "N/A")
                    df_display['dy'] = df_display['dy'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    df_display['roe'] = df_display['roe'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    df_display['margem'] = df_display['margem'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
                    
                    df_display.columns = ['Ticker', 'Nome', 'Setor', 'Preço', 'P/L', 'P/VP', 'DY', 'ROE', 'Margem Líq']
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Rankings
                    st.markdown("---")
                    st.markdown("### 🏆 Rankings")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**💰 Menor P/L (Value)**")
                        value = df[df['pl'] > 0].nsmallest(5, 'pl')[['ticker', 'pl']]
                        value['pl'] = value['pl'].apply(lambda x: f"{x:.2f}")
                        st.dataframe(value, hide_index=True)
                    
                    with col2:
                        st.markdown("**💵 Maior DY (Dividendos)**")
                        div = df[df['dy'] > 0].nlargest(5, 'dy')[['ticker', 'dy']]
                        div['dy'] = div['dy'].apply(lambda x: f"{x*100:.2f}%")
                        st.dataframe(div, hide_index=True)
                    
                    with col3:
                        st.markdown("**⭐ Maior ROE (Qualidade)**")
                        qual = df[df['roe'] > 0].nlargest(5, 'roe')[['ticker', 'roe']]
                        qual['roe'] = qual['roe'].apply(lambda x: f"{x*100:.2f}%")
                        st.dataframe(qual, hide_index=True)
                
            except Exception as e:
                st.error(f"Erro: {e}")
                st.exception(e)
