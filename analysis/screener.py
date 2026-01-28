"""
Módulo de Screener - Filtro de ações por critérios fundamentalistas
"""
import pandas as pd
from typing import Optional, List, Dict, Any
from data.fetcher import StockFetcher


class StockScreener:
    """Screener para filtrar ações por critérios"""
    
    # Lista de ações populares da B3 para screening
    DEFAULT_UNIVERSE = [
        # Bancos
        'ITUB4', 'BBDC4', 'BBAS3', 'SANB11', 'BPAC11',
        # Energia
        'ELET3', 'ELET6', 'ENGI11', 'EQTL3', 'CPFE3',
        # Petróleo e Gás
        'PETR4', 'PETR3', 'PRIO3', 'CSAN3', 'UGPA3',
        # Mineração
        'VALE3', 'CSNA3', 'GGBR4', 'USIM5',
        # Varejo
        'MGLU3', 'LREN3', 'AMER3', 'VIIA3', 'PETZ3',
        # Consumo
        'ABEV3', 'JBSS3', 'BRFS3', 'MDIA3', 'NTCO3',
        # Saúde
        'RDOR3', 'HAPV3', 'FLRY3', 'QUAL3',
        # Telecom/Tech
        'VIVT3', 'TIMS3', 'TOTS3', 'LWSA3',
        # Outros
        'B3SA3', 'RENT3', 'RAIL3', 'SUZB3', 'WEGE3'
    ]
    
    def __init__(self, tickers: Optional[List[str]] = None):
        """
        Inicializa o screener
        
        Args:
            tickers: Lista de tickers para análise (None usa DEFAULT_UNIVERSE)
        """
        self.tickers = tickers or self.DEFAULT_UNIVERSE
        self.data: Optional[pd.DataFrame] = None
    
    def fetch_all_data(self, verbose: bool = True) -> pd.DataFrame:
        """
        Busca dados de todas as ações
        
        Args:
            verbose: Se True, mostra progresso
        """
        records = []
        failed = []
        
        for i, ticker in enumerate(self.tickers):
            if verbose:
                print(f"[{i+1}/{len(self.tickers)}] Buscando {ticker}...", end=" ")
            
            try:
                stock = StockFetcher(ticker)
                basic = stock.get_basic_info()
                fundamentals = stock.get_fundamentals()
                
                record = {**basic, **fundamentals}
                records.append(record)
                
                if verbose:
                    print("OK")
            except Exception as e:
                failed.append(ticker)
                if verbose:
                    print(f"ERRO: {e}")
        
        self.data = pd.DataFrame(records)
        
        if verbose and failed:
            print(f"\nFalha ao buscar: {', '.join(failed)}")
        
        return self.data
    
    def filter(self, 
               pl_max: Optional[float] = None,
               pl_min: Optional[float] = None,
               pvp_max: Optional[float] = None,
               pvp_min: Optional[float] = None,
               dy_min: Optional[float] = None,
               roe_min: Optional[float] = None,
               market_cap_min: Optional[float] = None,
               setor: Optional[str] = None) -> pd.DataFrame:
        """
        Filtra ações por critérios
        
        Args:
            pl_max: P/L máximo
            pl_min: P/L mínimo (para excluir negativos)
            pvp_max: P/VP máximo
            pvp_min: P/VP mínimo
            dy_min: Dividend Yield mínimo (em decimal, ex: 0.05 = 5%)
            roe_min: ROE mínimo (em decimal)
            market_cap_min: Market Cap mínimo
            setor: Filtrar por setor (busca parcial)
        
        Returns:
            DataFrame filtrado
        """
        if self.data is None:
            raise ValueError("Execute fetch_all_data() primeiro")
        
        df = self.data.copy()
        
        if pl_max is not None:
            df = df[df['pl'] <= pl_max]
        if pl_min is not None:
            df = df[df['pl'] >= pl_min]
        if pvp_max is not None:
            df = df[df['pvp'] <= pvp_max]
        if pvp_min is not None:
            df = df[df['pvp'] >= pvp_min]
        if dy_min is not None:
            df = df[df['dividend_yield'] >= dy_min]
        if roe_min is not None:
            df = df[df['roe'] >= roe_min]
        if market_cap_min is not None:
            df = df[df['market_cap'] >= market_cap_min]
        if setor is not None:
            df = df[df['setor'].str.contains(setor, case=False, na=False)]
        
        return df
    
    def rank_by(self, column: str, ascending: bool = True, top_n: int = 10) -> pd.DataFrame:
        """
        Rankeia ações por uma coluna
        
        Args:
            column: Coluna para ordenar
            ascending: Ordem crescente
            top_n: Número de resultados
        """
        if self.data is None:
            raise ValueError("Execute fetch_all_data() primeiro")
        
        df = self.data.copy()
        df = df[df[column].notna() & (df[column] != 0)]
        return df.sort_values(column, ascending=ascending).head(top_n)
    
    def value_stocks(self, top_n: int = 10) -> pd.DataFrame:
        """Retorna ações 'valor' (P/L baixo, DY alto)"""
        if self.data is None:
            raise ValueError("Execute fetch_all_data() primeiro")
        
        df = self.data.copy()
        # Filtra P/L positivo e razoável
        df = df[(df['pl'] > 0) & (df['pl'] < 20)]
        # Ordena por P/L (menor melhor)
        return df.sort_values('pl', ascending=True).head(top_n)
    
    def dividend_stocks(self, top_n: int = 10) -> pd.DataFrame:
        """Retorna maiores pagadoras de dividendos"""
        if self.data is None:
            raise ValueError("Execute fetch_all_data() primeiro")
        
        df = self.data.copy()
        df = df[df['dividend_yield'] > 0]
        return df.sort_values('dividend_yield', ascending=False).head(top_n)
    
    def quality_stocks(self, top_n: int = 10) -> pd.DataFrame:
        """Retorna ações de qualidade (ROE alto)"""
        if self.data is None:
            raise ValueError("Execute fetch_all_data() primeiro")
        
        df = self.data.copy()
        df = df[df['roe'] > 0]
        return df.sort_values('roe', ascending=False).head(top_n)


if __name__ == "__main__":
    # Teste rápido com poucas ações
    screener = StockScreener(['ITUB4', 'BBDC4', 'PETR4', 'VALE3', 'WEGE3'])
    data = screener.fetch_all_data()
    print("\nDados coletados:")
    print(data[['ticker', 'nome', 'pl', 'pvp', 'dividend_yield', 'roe']])
