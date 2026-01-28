"""
Módulo para cálculo de indicadores técnicos e análise de performance
"""
import pandas as pd
import numpy as np
from typing import Optional


class StockAnalyzer:
    """Classe para análise de ações"""
    
    def __init__(self, history: pd.DataFrame):
        """
        Inicializa o analisador com histórico de preços
        
        Args:
            history: DataFrame com colunas OHLCV do yfinance
        """
        self.history = history.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepara os dados calculando retornos"""
        if 'Close' in self.history.columns:
            self.history['returns'] = self.history['Close'].pct_change()
            self.history['log_returns'] = np.log(self.history['Close'] / self.history['Close'].shift(1))
            self.history['cumulative_returns'] = (1 + self.history['returns']).cumprod() - 1
    
    def get_returns(self, period: Optional[int] = None) -> pd.Series:
        """
        Retorna série de retornos diários
        
        Args:
            period: Número de dias (None para todos)
        """
        if period:
            return self.history['returns'].tail(period)
        return self.history['returns']
    
    def total_return(self, period: Optional[int] = None) -> float:
        """Calcula retorno total do período"""
        if period:
            data = self.history['Close'].tail(period + 1)
        else:
            data = self.history['Close']
        
        if len(data) < 2:
            return 0.0
        return (data.iloc[-1] / data.iloc[0]) - 1
    
    def annualized_return(self, period: Optional[int] = None) -> float:
        """Calcula retorno anualizado"""
        total = self.total_return(period)
        days = period if period else len(self.history)
        if days == 0:
            return 0.0
        return (1 + total) ** (252 / days) - 1
    
    def volatility(self, period: int = 252, annualized: bool = True) -> float:
        """
        Calcula volatilidade (desvio padrão dos retornos)
        
        Args:
            period: Janela em dias
            annualized: Se True, anualiza a volatilidade
        """
        returns = self.history['returns'].tail(period).dropna()
        vol = returns.std()
        if annualized:
            vol *= np.sqrt(252)
        return vol
    
    def sharpe_ratio(self, risk_free_rate: float = 0.1075, period: int = 252) -> float:
        """
        Calcula Sharpe Ratio
        
        Args:
            risk_free_rate: Taxa livre de risco anual (default: SELIC ~10.75%)
            period: Período em dias
        """
        ann_return = self.annualized_return(period)
        vol = self.volatility(period)
        if vol == 0:
            return 0.0
        return (ann_return - risk_free_rate) / vol
    
    def max_drawdown(self, period: Optional[int] = None) -> float:
        """Calcula máximo drawdown"""
        if period:
            prices = self.history['Close'].tail(period)
        else:
            prices = self.history['Close']
        
        cummax = prices.cummax()
        drawdown = (prices - cummax) / cummax
        return drawdown.min()
    
    def moving_average(self, window: int = 20) -> pd.Series:
        """Calcula média móvel simples"""
        return self.history['Close'].rolling(window=window).mean()
    
    def add_moving_averages(self, windows: list = [20, 50, 200]):
        """Adiciona múltiplas médias móveis ao DataFrame"""
        for w in windows:
            self.history[f'MA_{w}'] = self.moving_average(w)
    
    def get_summary_stats(self, period: int = 252) -> dict:
        """Retorna resumo estatístico"""
        return {
            'retorno_total': self.total_return(period),
            'retorno_anualizado': self.annualized_return(period),
            'volatilidade_anual': self.volatility(period),
            'sharpe_ratio': self.sharpe_ratio(period=period),
            'max_drawdown': self.max_drawdown(period),
            'preco_atual': self.history['Close'].iloc[-1],
            'preco_max_52w': self.history['Close'].tail(252).max(),
            'preco_min_52w': self.history['Close'].tail(252).min(),
            'volume_medio': self.history['Volume'].tail(period).mean(),
        }


def compare_stocks(analyzers: dict) -> pd.DataFrame:
    """
    Compara múltiplas ações
    
    Args:
        analyzers: Dicionário {ticker: StockAnalyzer}
    
    Returns:
        DataFrame comparativo
    """
    data = []
    for ticker, analyzer in analyzers.items():
        stats = analyzer.get_summary_stats()
        stats['ticker'] = ticker
        data.append(stats)
    
    df = pd.DataFrame(data)
    df.set_index('ticker', inplace=True)
    return df


if __name__ == "__main__":
    # Teste
    import yfinance as yf
    stock = yf.Ticker("ITUB4.SA")
    history = stock.history(period="1y")
    
    analyzer = StockAnalyzer(history)
    print("Resumo estatístico:")
    for k, v in analyzer.get_summary_stats().items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
