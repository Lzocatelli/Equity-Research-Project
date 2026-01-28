"""
Módulo de visualização - Gráficos para análise de ações
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional, List, Dict
import warnings
warnings.filterwarnings('ignore')

# Configuração de estilo
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


class StockCharts:
    """Classe para gerar gráficos de ações"""
    
    COLORS = {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e', 
        'positive': '#2ecc71',
        'negative': '#e74c3c',
        'neutral': '#95a5a6',
        'ma_20': '#e74c3c',
        'ma_50': '#f39c12',
        'ma_200': '#9b59b6',
    }
    
    def __init__(self, history: pd.DataFrame, ticker: str = ""):
        """
        Inicializa com histórico de preços
        
        Args:
            history: DataFrame com OHLCV
            ticker: Nome do ticker para títulos
        """
        self.history = history.copy()
        self.ticker = ticker
    
    def plot_price(self, 
                   show_volume: bool = True,
                   show_ma: List[int] = [20, 50],
                   save_path: Optional[str] = None) -> plt.Figure:
        """
        Gráfico de preço com volume
        
        Args:
            show_volume: Mostrar volume no subplot inferior
            show_ma: Lista de períodos de médias móveis
            save_path: Caminho para salvar (None = não salva)
        """
        if show_volume:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                            gridspec_kw={'height_ratios': [3, 1]})
        else:
            fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))
        
        # Preço
        ax1.plot(self.history.index, self.history['Close'], 
                 color=self.COLORS['primary'], linewidth=1.5, label='Preço')
        
        # Médias móveis
        for period in show_ma:
            ma = self.history['Close'].rolling(period).mean()
            color = self.COLORS.get(f'ma_{period}', self.COLORS['secondary'])
            ax1.plot(self.history.index, ma, 
                     color=color, linewidth=1, linestyle='--', 
                     label=f'MM{period}', alpha=0.8)
        
        ax1.set_title(f'{self.ticker} - Histórico de Preços', fontweight='bold')
        ax1.set_ylabel('Preço (R$)')
        ax1.legend(loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        # Volume
        if show_volume:
            colors = [self.COLORS['positive'] if c >= o else self.COLORS['negative'] 
                      for c, o in zip(self.history['Close'], self.history['Open'])]
            ax2.bar(self.history.index, self.history['Volume'], color=colors, alpha=0.7)
            ax2.set_ylabel('Volume')
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax2.yaxis.set_major_formatter(lambda x, p: f'{x/1e6:.1f}M')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig
    
    def plot_returns(self, period: int = 252, save_path: Optional[str] = None) -> plt.Figure:
        """
        Gráfico de retornos acumulados
        
        Args:
            period: Período em dias
            save_path: Caminho para salvar
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        data = self.history.tail(period).copy()
        returns = data['Close'].pct_change()
        cum_returns = (1 + returns).cumprod() - 1
        
        # Retorno acumulado
        ax1.fill_between(data.index, cum_returns * 100, 
                         where=cum_returns >= 0, color=self.COLORS['positive'], alpha=0.5)
        ax1.fill_between(data.index, cum_returns * 100, 
                         where=cum_returns < 0, color=self.COLORS['negative'], alpha=0.5)
        ax1.plot(data.index, cum_returns * 100, color=self.COLORS['primary'], linewidth=1.5)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_title(f'{self.ticker} - Retorno Acumulado', fontweight='bold')
        ax1.set_ylabel('Retorno (%)')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
        
        # Distribuição de retornos
        ax2.hist(returns.dropna() * 100, bins=50, color=self.COLORS['primary'], 
                 alpha=0.7, edgecolor='white')
        ax2.axvline(x=returns.mean() * 100, color=self.COLORS['negative'], 
                    linestyle='--', label=f'Média: {returns.mean()*100:.2f}%')
        ax2.set_title(f'{self.ticker} - Distribuição de Retornos Diários', fontweight='bold')
        ax2.set_xlabel('Retorno Diário (%)')
        ax2.set_ylabel('Frequência')
        ax2.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig
    
    def plot_drawdown(self, period: int = 252, save_path: Optional[str] = None) -> plt.Figure:
        """
        Gráfico de drawdown
        
        Args:
            period: Período em dias
            save_path: Caminho para salvar
        """
        fig, ax = plt.subplots(figsize=(12, 5))
        
        data = self.history.tail(period).copy()
        cummax = data['Close'].cummax()
        drawdown = (data['Close'] - cummax) / cummax * 100
        
        ax.fill_between(data.index, drawdown, color=self.COLORS['negative'], alpha=0.5)
        ax.plot(data.index, drawdown, color=self.COLORS['negative'], linewidth=1)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Marca o máximo drawdown
        min_dd = drawdown.min()
        min_dd_date = drawdown.idxmin()
        ax.scatter([min_dd_date], [min_dd], color='red', s=100, zorder=5)
        ax.annotate(f'Max DD: {min_dd:.1f}%', xy=(min_dd_date, min_dd),
                    xytext=(10, -20), textcoords='offset points',
                    fontsize=10, color='red')
        
        ax.set_title(f'{self.ticker} - Drawdown', fontweight='bold')
        ax.set_ylabel('Drawdown (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig


def plot_comparison(histories: Dict[str, pd.DataFrame], 
                    normalize: bool = True,
                    save_path: Optional[str] = None) -> plt.Figure:
    """
    Compara performance de múltiplas ações
    
    Args:
        histories: Dicionário {ticker: DataFrame}
        normalize: Se True, normaliza para base 100
        save_path: Caminho para salvar
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for ticker, history in histories.items():
        prices = history['Close']
        if normalize:
            prices = prices / prices.iloc[0] * 100
        ax.plot(history.index, prices, linewidth=1.5, label=ticker)
    
    title = 'Comparação de Performance'
    if normalize:
        title += ' (Base 100)'
    ax.set_title(title, fontweight='bold')
    ax.set_ylabel('Preço' if not normalize else 'Base 100')
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_fundamentals_comparison(data: pd.DataFrame, 
                                  metrics: List[str] = ['pl', 'pvp', 'roe', 'dividend_yield'],
                                  save_path: Optional[str] = None) -> plt.Figure:
    """
    Gráfico de barras comparando múltiplos fundamentalistas
    
    Args:
        data: DataFrame com métricas por ticker
        metrics: Lista de métricas para plotar
        save_path: Caminho para salvar
    """
    n_metrics = len(metrics)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    labels_map = {
        'pl': 'P/L',
        'pvp': 'P/VP',
        'roe': 'ROE (%)',
        'dividend_yield': 'Dividend Yield (%)',
        'margem_liquida': 'Margem Líquida (%)'
    }
    
    for i, metric in enumerate(metrics[:4]):
        ax = axes[i]
        values = data[metric].copy()
        
        # Converte para percentual se necessário
        if metric in ['roe', 'dividend_yield', 'margem_liquida']:
            values = values * 100
        
        colors = [StockCharts.COLORS['primary'] if v >= 0 else StockCharts.COLORS['negative'] 
                  for v in values]
        
        bars = ax.bar(data['ticker'], values, color=colors, alpha=0.8)
        ax.set_title(labels_map.get(metric, metric), fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # Adiciona valores nas barras
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(f'{val:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    
    plt.suptitle('Comparação de Múltiplos Fundamentalistas', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


if __name__ == "__main__":
    import yfinance as yf
    
    # Teste
    stock = yf.Ticker("ITUB4.SA")
    history = stock.history(period="1y")
    
    charts = StockCharts(history, "ITUB4")
    charts.plot_price(show_ma=[20, 50, 200])
    plt.show()
