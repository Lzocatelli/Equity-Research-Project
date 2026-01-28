#!/usr/bin/env python3
"""
Equity Research Tool
====================
Ferramenta de análise fundamentalista de ações da B3

Autor: Zocatelli
GitHub: https://github.com/Lzocatelli
"""
import sys
import os
from datetime import datetime
from tabulate import tabulate

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import StockFetcher, fetch_multiple_stocks
from analysis.indicators import StockAnalyzer, compare_stocks
from analysis.screener import StockScreener
from visualization.charts import StockCharts, plot_comparison, plot_fundamentals_comparison
import matplotlib.pyplot as plt


def format_number(value, is_percent=False, is_currency=False, is_large=False):
    """Formata números para exibição"""
    if value is None or value == 0:
        return "N/A"
    if is_percent:
        return f"{value * 100:.2f}%"
    if is_currency:
        return f"R$ {value:,.2f}"
    if is_large:
        if abs(value) >= 1e12:
            return f"R$ {value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"R$ {value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"R$ {value/1e6:.2f}M"
    return f"{value:.2f}"


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def analyze_single_stock(ticker: str, save_charts: bool = False):
    """
    Análise completa de uma única ação
    
    Args:
        ticker: Código da ação
        save_charts: Se True, salva os gráficos
    """
    print_header(f"ANÁLISE DE {ticker}")
    
    # Busca dados
    print("\n📊 Buscando dados...")
    stock = StockFetcher(ticker)
    
    # Informações básicas
    print_header("INFORMAÇÕES GERAIS")
    basic = stock.get_basic_info()
    basic_table = [
        ["Ticker", basic['ticker']],
        ["Nome", basic['nome']],
        ["Setor", basic['setor']],
        ["Indústria", basic['industria']],
        ["Preço Atual", format_number(basic['preco_atual'], is_currency=True)],
        ["Market Cap", format_number(basic['market_cap'], is_large=True)],
        ["Volume Médio", f"{basic['volume_medio']:,.0f}"],
    ]
    print(tabulate(basic_table, tablefmt="simple"))
    
    # Múltiplos Fundamentalistas
    print_header("MÚLTIPLOS FUNDAMENTALISTAS")
    fund = stock.get_fundamentals()
    fund_table = [
        ["P/L (Preço/Lucro)", format_number(fund['pl'])],
        ["P/VP (Preço/Valor Patrimonial)", format_number(fund['pvp'])],
        ["LPA (Lucro por Ação)", format_number(fund['lpa'], is_currency=True)],
        ["VPA (Valor Patrimonial por Ação)", format_number(fund['vpa'], is_currency=True)],
        ["Dividend Yield", format_number(fund['dividend_yield'], is_percent=True)],
        ["Payout Ratio", format_number(fund['payout_ratio'], is_percent=True)],
        ["ROE", format_number(fund['roe'], is_percent=True)],
        ["Margem Líquida", format_number(fund['margem_liquida'], is_percent=True)],
        ["Dívida/Patrimônio", format_number(fund['divida_patrimonio'])],
    ]
    print(tabulate(fund_table, tablefmt="simple"))
    
    # Análise de Performance
    print_header("ANÁLISE DE PERFORMANCE (12 MESES)")
    history = stock.get_history(period="2y")
    analyzer = StockAnalyzer(history)
    stats = analyzer.get_summary_stats(period=252)
    
    perf_table = [
        ["Retorno Total (12m)", format_number(stats['retorno_total'], is_percent=True)],
        ["Retorno Anualizado", format_number(stats['retorno_anualizado'], is_percent=True)],
        ["Volatilidade Anual", format_number(stats['volatilidade_anual'], is_percent=True)],
        ["Sharpe Ratio", format_number(stats['sharpe_ratio'])],
        ["Máximo Drawdown", format_number(stats['max_drawdown'], is_percent=True)],
        ["Máxima 52 semanas", format_number(stats['preco_max_52w'], is_currency=True)],
        ["Mínima 52 semanas", format_number(stats['preco_min_52w'], is_currency=True)],
    ]
    print(tabulate(perf_table, tablefmt="simple"))
    
    # Interpretação automática
    print_header("INTERPRETAÇÃO")
    interpretations = []
    
    # P/L
    if fund['pl'] and fund['pl'] > 0:
        if fund['pl'] < 10:
            interpretations.append("✅ P/L baixo (<10): Ação pode estar barata")
        elif fund['pl'] > 25:
            interpretations.append("⚠️  P/L alto (>25): Ação pode estar cara ou mercado espera crescimento")
        else:
            interpretations.append("➖ P/L em faixa neutra (10-25)")
    
    # ROE
    if fund['roe']:
        if fund['roe'] > 0.15:
            interpretations.append("✅ ROE alto (>15%): Boa rentabilidade sobre patrimônio")
        elif fund['roe'] < 0.08:
            interpretations.append("⚠️  ROE baixo (<8%): Baixa rentabilidade")
    
    # Dividend Yield
    if fund['dividend_yield']:
        if fund['dividend_yield'] > 0.06:
            interpretations.append("✅ DY alto (>6%): Boa pagadora de dividendos")
    
    # Performance
    if stats['retorno_total'] > 0.20:
        interpretations.append("✅ Retorno forte (>20%) nos últimos 12 meses")
    elif stats['retorno_total'] < -0.20:
        interpretations.append("⚠️  Queda significativa (>20%) nos últimos 12 meses")
    
    if stats['sharpe_ratio'] > 1:
        interpretations.append("✅ Sharpe Ratio > 1: Bom retorno ajustado ao risco")
    elif stats['sharpe_ratio'] < 0:
        interpretations.append("⚠️  Sharpe Ratio negativo: Retorno abaixo do CDI")
    
    for interp in interpretations:
        print(f"  {interp}")
    
    # Gráficos
    print("\n📈 Gerando gráficos...")
    charts = StockCharts(history, ticker)
    
    output_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    # Gráfico de preço
    fig1 = charts.plot_price(show_ma=[20, 50, 200])
    if save_charts:
        fig1.savefig(os.path.join(output_dir, f'{ticker}_price.png'), dpi=150, bbox_inches='tight')
        print(f"  Salvo: reports/{ticker}_price.png")
    
    # Gráfico de retornos
    fig2 = charts.plot_returns()
    if save_charts:
        fig2.savefig(os.path.join(output_dir, f'{ticker}_returns.png'), dpi=150, bbox_inches='tight')
        print(f"  Salvo: reports/{ticker}_returns.png")
    
    # Gráfico de drawdown
    fig3 = charts.plot_drawdown()
    if save_charts:
        fig3.savefig(os.path.join(output_dir, f'{ticker}_drawdown.png'), dpi=150, bbox_inches='tight')
        print(f"  Salvo: reports/{ticker}_drawdown.png")
    
    return stock, analyzer, charts


def compare_multiple_stocks(tickers: list, save_charts: bool = False):
    """
    Compara múltiplas ações
    
    Args:
        tickers: Lista de tickers
        save_charts: Se True, salva os gráficos
    """
    print_header(f"COMPARAÇÃO: {', '.join(tickers)}")
    
    print("\n📊 Buscando dados...")
    stocks = {}
    histories = {}
    analyzers = {}
    
    for ticker in tickers:
        print(f"  {ticker}...", end=" ")
        try:
            stock = StockFetcher(ticker)
            history = stock.get_history(period="1y")
            stocks[ticker] = stock
            histories[ticker] = history
            analyzers[ticker] = StockAnalyzer(history)
            print("OK")
        except Exception as e:
            print(f"ERRO: {e}")
    
    # Tabela comparativa de fundamentos
    print_header("COMPARAÇÃO DE MÚLTIPLOS")
    data = []
    for ticker, stock in stocks.items():
        fund = stock.get_fundamentals()
        data.append({
            'Ticker': ticker,
            'P/L': format_number(fund['pl']),
            'P/VP': format_number(fund['pvp']),
            'DY': format_number(fund['dividend_yield'], is_percent=True),
            'ROE': format_number(fund['roe'], is_percent=True),
        })
    
    print(tabulate(data, headers='keys', tablefmt='simple'))
    
    # Tabela comparativa de performance
    print_header("COMPARAÇÃO DE PERFORMANCE")
    perf_data = []
    for ticker, analyzer in analyzers.items():
        stats = analyzer.get_summary_stats()
        perf_data.append({
            'Ticker': ticker,
            'Retorno 12m': format_number(stats['retorno_total'], is_percent=True),
            'Volatilidade': format_number(stats['volatilidade_anual'], is_percent=True),
            'Sharpe': format_number(stats['sharpe_ratio']),
            'Max DD': format_number(stats['max_drawdown'], is_percent=True),
        })
    
    print(tabulate(perf_data, headers='keys', tablefmt='simple'))
    
    # Gráfico comparativo
    print("\n📈 Gerando gráfico comparativo...")
    fig = plot_comparison(histories, normalize=True)
    
    if save_charts:
        output_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(output_dir, exist_ok=True)
        filename = '_'.join(tickers) + '_comparison.png'
        fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight')
        print(f"  Salvo: reports/{filename}")
    
    return stocks, analyzers


def run_screener(criteria: dict = None):
    """
    Executa o screener com critérios padrão
    
    Args:
        criteria: Dicionário com critérios de filtro
    """
    print_header("STOCK SCREENER")
    
    # Lista reduzida para demo rápida
    demo_tickers = ['ITUB4', 'BBDC4', 'PETR4', 'VALE3', 'WEGE3', 
                    'ABEV3', 'B3SA3', 'RENT3', 'EQTL3', 'SUZB3']
    
    print(f"\n📊 Analisando {len(demo_tickers)} ações...")
    screener = StockScreener(demo_tickers)
    data = screener.fetch_all_data()
    
    # Value Stocks
    print_header("TOP VALUE STOCKS (Menor P/L)")
    value = screener.value_stocks(top_n=5)
    if not value.empty:
        print(tabulate(
            value[['ticker', 'nome', 'pl', 'pvp', 'dividend_yield']].round(2),
            headers=['Ticker', 'Nome', 'P/L', 'P/VP', 'DY'],
            tablefmt='simple',
            showindex=False
        ))
    
    # Dividend Stocks
    print_header("TOP DIVIDEND STOCKS (Maior DY)")
    dividends = screener.dividend_stocks(top_n=5)
    if not dividends.empty:
        div_display = dividends[['ticker', 'nome', 'dividend_yield', 'payout_ratio']].copy()
        div_display['dividend_yield'] = div_display['dividend_yield'].apply(lambda x: f"{x*100:.2f}%")
        div_display['payout_ratio'] = div_display['payout_ratio'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
        print(tabulate(
            div_display,
            headers=['Ticker', 'Nome', 'DY', 'Payout'],
            tablefmt='simple',
            showindex=False
        ))
    
    # Quality Stocks
    print_header("TOP QUALITY STOCKS (Maior ROE)")
    quality = screener.quality_stocks(top_n=5)
    if not quality.empty:
        qual_display = quality[['ticker', 'nome', 'roe', 'margem_liquida']].copy()
        qual_display['roe'] = qual_display['roe'].apply(lambda x: f"{x*100:.2f}%")
        qual_display['margem_liquida'] = qual_display['margem_liquida'].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
        print(tabulate(
            qual_display,
            headers=['Ticker', 'Nome', 'ROE', 'Margem Líq'],
            tablefmt='simple',
            showindex=False
        ))
    
    return screener


def main():
    """Função principal - demonstração do sistema"""
    print("\n" + "=" * 60)
    print("     EQUITY RESEARCH TOOL - B3")
    print("=" * 60)
    print(f"  Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)
    
    # Menu
    print("\nEscolha uma opção:")
    print("  1. Analisar ação individual")
    print("  2. Comparar múltiplas ações")
    print("  3. Executar screener")
    print("  4. Demo completa (ITUB4)")
    print("  5. Sair")
    
    try:
        choice = input("\nOpção: ").strip()
    except EOFError:
        choice = "4"  # Default para demo
    
    if choice == "1":
        ticker = input("Digite o ticker (ex: ITUB4): ").strip().upper()
        analyze_single_stock(ticker, save_charts=True)
        plt.show()
        
    elif choice == "2":
        tickers_input = input("Digite os tickers separados por vírgula (ex: ITUB4,BBDC4,SANB11): ")
        tickers = [t.strip().upper() for t in tickers_input.split(',')]
        compare_multiple_stocks(tickers, save_charts=True)
        plt.show()
        
    elif choice == "3":
        run_screener()
        
    elif choice == "4":
        # Demo completa
        print("\n🚀 Executando demonstração completa com ITUB4...")
        analyze_single_stock("ITUB4", save_charts=True)
        print("\n" + "=" * 60)
        print("  Comparando ITUB4 com peers do setor bancário...")
        print("=" * 60)
        compare_multiple_stocks(['ITUB4', 'BBDC4', 'BBAS3', 'SANB11'], save_charts=True)
        plt.show()
        
    elif choice == "5":
        print("\nAté mais! 👋")
        return
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
