"""
Módulo para buscar dados macroeconômicos do Banco Central do Brasil
"""
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict


class MacroData:
    """Classe para buscar indicadores macroeconômicos do BCB"""
    
    BCB_API_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json"
    
    # Códigos das séries do BCB
    SERIES = {
        'selic': 432,           # Taxa SELIC (meta)
        'selic_diaria': 11,     # Taxa SELIC diária
        'ipca': 433,            # IPCA mensal
        'ipca_12m': 13522,      # IPCA acumulado 12 meses
        'igpm': 189,            # IGP-M mensal
        'igpm_12m': 4175,       # IGP-M acumulado 12 meses
        'pib': 4380,            # PIB mensal
        'cambio': 1,            # Dólar PTAX
        'cdi': 12,              # CDI diário
    }
    
    def __init__(self):
        self._cache: Dict[str, dict] = {}
    
    def _fetch_serie(self, codigo: int, n: int = 1) -> Optional[list]:
        """Busca série do BCB"""
        try:
            url = self.BCB_API_URL.format(codigo=codigo, n=n)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar série {codigo}: {e}")
            return None
    
    def get_selic(self) -> Optional[float]:
        """Retorna taxa SELIC atual (% a.a.)"""
        data = self._fetch_serie(self.SERIES['selic'])
        if data and len(data) > 0:
            return float(data[-1]['valor'])
        return None
    
    def get_ipca_12m(self) -> Optional[float]:
        """Retorna IPCA acumulado 12 meses (%)"""
        data = self._fetch_serie(self.SERIES['ipca_12m'])
        if data and len(data) > 0:
            return float(data[-1]['valor'])
        return None
    
    def get_cdi(self) -> Optional[float]:
        """Retorna CDI anualizado aproximado (usa SELIC como proxy)"""
        # CDI ≈ SELIC - 0.10
        selic = self.get_selic()
        if selic:
            return selic - 0.10
        return None
    
    def get_cambio(self) -> Optional[float]:
        """Retorna cotação do dólar (PTAX)"""
        data = self._fetch_serie(self.SERIES['cambio'])
        if data and len(data) > 0:
            return float(data[-1]['valor'])
        return None
    
    def get_all_indicators(self) -> dict:
        """Retorna todos os indicadores principais"""
        return {
            'selic': self.get_selic(),
            'ipca_12m': self.get_ipca_12m(),
            'cdi': self.get_cdi(),
            'cambio': self.get_cambio(),
            'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
    
    def get_historical_selic(self, months: int = 12) -> pd.DataFrame:
        """Retorna histórico da SELIC"""
        data = self._fetch_serie(self.SERIES['selic'], n=months)
        if data:
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = df['valor'].astype(float)
            return df
        return pd.DataFrame()


# Médias setoriais de referência (P/L) - Brasil
# Fonte: Aproximações baseadas em dados históricos do mercado brasileiro
SECTOR_BENCHMARKS = {
    'Financial Services': {'pl_medio': 8, 'pvp_medio': 1.2, 'dy_medio': 0.06},
    'Banks': {'pl_medio': 7, 'pvp_medio': 1.0, 'dy_medio': 0.07},
    'Technology': {'pl_medio': 25, 'pvp_medio': 5.0, 'dy_medio': 0.01},
    'Consumer Cyclical': {'pl_medio': 15, 'pvp_medio': 2.5, 'dy_medio': 0.03},
    'Consumer Defensive': {'pl_medio': 18, 'pvp_medio': 3.0, 'dy_medio': 0.04},
    'Energy': {'pl_medio': 6, 'pvp_medio': 1.2, 'dy_medio': 0.10},
    'Basic Materials': {'pl_medio': 8, 'pvp_medio': 1.5, 'dy_medio': 0.06},
    'Industrials': {'pl_medio': 12, 'pvp_medio': 2.0, 'dy_medio': 0.03},
    'Healthcare': {'pl_medio': 20, 'pvp_medio': 3.5, 'dy_medio': 0.02},
    'Utilities': {'pl_medio': 10, 'pvp_medio': 1.5, 'dy_medio': 0.06},
    'Real Estate': {'pl_medio': 12, 'pvp_medio': 1.0, 'dy_medio': 0.07},
    'Communication Services': {'pl_medio': 15, 'pvp_medio': 2.0, 'dy_medio': 0.04},
}

# Fallback para setores não mapeados
DEFAULT_BENCHMARK = {'pl_medio': 12, 'pvp_medio': 2.0, 'dy_medio': 0.04}


def get_sector_benchmark(sector: str) -> dict:
    """Retorna benchmark do setor"""
    # Tenta match exato primeiro
    if sector in SECTOR_BENCHMARKS:
        return SECTOR_BENCHMARKS[sector]
    
    # Tenta match parcial
    sector_lower = sector.lower()
    for key, value in SECTOR_BENCHMARKS.items():
        if key.lower() in sector_lower or sector_lower in key.lower():
            return value
    
    # Fallback
    return DEFAULT_BENCHMARK


if __name__ == "__main__":
    macro = MacroData()
    print("Indicadores Macroeconômicos:")
    indicators = macro.get_all_indicators()
    for k, v in indicators.items():
        print(f"  {k}: {v}")
