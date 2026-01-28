"""
Módulo para buscar dados de ações usando yfinance
"""
import yfinance as yf
import pandas as pd
import time
import random
from datetime import datetime, timedelta


def retry_on_rate_limit(max_retries=3, base_delay=2):
    """Decorator para retry em caso de rate limit"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'rate' in error_msg or 'limit' in error_msg or 'too many' in error_msg:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            time.sleep(delay)
                            continue
                    raise e
            return func(*args, **kwargs)
        return wrapper
    return decorator


class StockFetcher:
    """Classe para buscar dados de ações da B3"""
    
    def __init__(self, ticker: str):
        """
        Inicializa o fetcher com um ticker
        
        Args:
            ticker: Código da ação (ex: 'ITUB4' ou 'ITUB4.SA')
        """
        # Adiciona .SA se não tiver (padrão B3 no Yahoo Finance)
        self.ticker = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        self.stock = yf.Ticker(self.ticker)
        self._info = None
        self._history = None
    
    @property
    def info(self) -> dict:
        """Retorna informações gerais da ação (com cache)"""
        if self._info is None:
            self._info = self._fetch_info()
        return self._info
    
    @retry_on_rate_limit(max_retries=3, base_delay=2)
    def _fetch_info(self) -> dict:
        """Busca info com retry"""
        return self.stock.info
    
    def get_history(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Busca histórico de preços
        
        Args:
            period: Período ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Intervalo ('1d', '1wk', '1mo')
        
        Returns:
            DataFrame com OHLCV
        """
        self._history = self.stock.history(period=period, interval=interval)
        return self._history
    
    def get_current_price(self) -> float:
        """Retorna o preço atual"""
        return self.info.get('currentPrice') or self.info.get('regularMarketPrice', 0)
    
    def get_basic_info(self) -> dict:
        """Retorna informações básicas formatadas"""
        info = self.info
        return {
            'ticker': self.ticker.replace('.SA', ''),
            'nome': info.get('shortName', 'N/A'),
            'setor': info.get('sector', 'N/A'),
            'industria': info.get('industry', 'N/A'),
            'preco_atual': self.get_current_price(),
            'moeda': info.get('currency', 'BRL'),
            'market_cap': info.get('marketCap', 0),
            'volume_medio': info.get('averageVolume', 0),
        }
    
    def get_fundamentals(self) -> dict:
        """Retorna dados fundamentalistas"""
        info = self.info
        
        # EV/EBITDA - tenta pegar direto, senão calcula
        ev_ebitda = info.get('enterpriseToEbitda')
        if not ev_ebitda:
            ev = info.get('enterpriseValue')
            ebitda = info.get('ebitda')
            if ev and ebitda and ebitda != 0:
                ev_ebitda = ev / ebitda
        
        # PSR (Price to Sales) - tenta pegar direto, senão calcula
        psr = info.get('priceToSalesTrailing12Months')
        if not psr:
            market_cap = info.get('marketCap')
            revenue = info.get('totalRevenue')
            if market_cap and revenue and revenue != 0:
                psr = market_cap / revenue
        
        return {
            'preco': self.get_current_price(),
            'lpa': info.get('trailingEps', 0),  # Lucro por ação
            'vpa': info.get('bookValue', 0),     # Valor patrimonial por ação
            'pl': info.get('trailingPE', 0),     # P/L
            'pvp': info.get('priceToBook', 0),   # P/VP
            'ev_ebitda': ev_ebitda,              # EV/EBITDA
            'psr': psr,                          # Price to Sales
            'dividend_yield': info.get('dividendYield', 0),
            'payout_ratio': info.get('payoutRatio', 0),
            'roe': info.get('returnOnEquity', 0),
            'roa': info.get('returnOnAssets', 0),
            'margem_liquida': info.get('profitMargins', 0),
            'margem_bruta': info.get('grossMargins', 0),
            'margem_operacional': info.get('operatingMargins', 0),
            'divida_patrimonio': info.get('debtToEquity', 0),
            'receita_total': info.get('totalRevenue', 0),
            'lucro_liquido': info.get('netIncomeToCommon', 0),
            'ebitda': info.get('ebitda', 0),
            'enterprise_value': info.get('enterpriseValue', 0),
        }


def fetch_multiple_stocks(tickers: list) -> dict:
    """
    Busca dados de múltiplas ações
    
    Args:
        tickers: Lista de tickers
    
    Returns:
        Dicionário com StockFetcher para cada ticker
    """
    return {ticker: StockFetcher(ticker) for ticker in tickers}


if __name__ == "__main__":
    # Teste rápido
    stock = StockFetcher("ITUB4")
    print("Info básica:", stock.get_basic_info())
    print("\nFundamentos:", stock.get_fundamentals())
