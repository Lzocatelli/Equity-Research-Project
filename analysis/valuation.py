"""
Módulo de Valuation - Cálculo de Preço Justo
============================================
Implementa modelos clássicos de valuation:
- Fórmula de Graham
- Fórmula de Bazin
- Modelo de Gordon (DDM simplificado)
"""
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class ValuationResult:
    """Resultado de uma análise de valuation"""
    metodo: str
    preco_justo: Optional[float]
    preco_atual: float
    margem_seguranca: Optional[float]  # % de desconto/prêmio
    recomendacao: str  # "BARATO", "JUSTO", "CARO"
    explicacao: str


def graham_formula(lpa: float, vpa: float, taxa_livre_risco: float = 0.1075) -> Optional[float]:
    """
    Fórmula de Benjamin Graham para Preço Justo
    
    Fórmula original: √(22.5 × LPA × VPA)
    
    O 22.5 vem de P/L = 15 e P/VP = 1.5 (15 × 1.5 = 22.5)
    
    Ajuste para Brasil: Considera taxa livre de risco maior
    Multiplicador ajustado = 22.5 × (4.4% / taxa_atual)
    
    Args:
        lpa: Lucro por Ação (últimos 12 meses)
        vpa: Valor Patrimonial por Ação
        taxa_livre_risco: Taxa livre de risco (SELIC)
    
    Returns:
        Preço justo calculado ou None se dados inválidos
    """
    if not lpa or not vpa or lpa <= 0 or vpa <= 0:
        return None
    
    # Multiplicador original de Graham
    multiplicador = 22.5
    
    # Ajuste para ambiente de juros altos (Brasil)
    # Graham usava 4.4% como referência (bonds AAA da época)
    # Ajustamos proporcionalmente
    if taxa_livre_risco and taxa_livre_risco > 0:
        ajuste = min(0.044 / (taxa_livre_risco / 100), 1.0)  # Limita o ajuste
        multiplicador = multiplicador * ajuste
    
    preco_justo = (multiplicador * lpa * vpa) ** 0.5
    return preco_justo


def graham_formula_original(lpa: float, vpa: float) -> Optional[float]:
    """
    Fórmula de Graham ORIGINAL (sem ajuste)
    √(22.5 × LPA × VPA)
    """
    if not lpa or not vpa or lpa <= 0 or vpa <= 0:
        return None
    return (22.5 * lpa * vpa) ** 0.5


def bazin_formula(dpa: float, yield_minimo: float = 0.06) -> Optional[float]:
    """
    Fórmula de Décio Bazin para Preço Justo
    
    Bazin acreditava que uma ação só vale a pena se pagar
    pelo menos 6% de dividend yield.
    
    Fórmula: Preço Justo = DPA / Yield Mínimo
    
    Args:
        dpa: Dividendo por Ação (últimos 12 meses)
        yield_minimo: Yield mínimo aceitável (padrão 6%)
    
    Returns:
        Preço justo calculado ou None se dados inválidos
    """
    if not dpa or dpa <= 0 or yield_minimo <= 0:
        return None
    
    return dpa / yield_minimo


def gordon_ddm(dpa: float, taxa_crescimento: float = 0.05, 
               taxa_desconto: float = 0.12) -> Optional[float]:
    """
    Modelo de Gordon (Dividend Discount Model simplificado)
    
    Fórmula: P = DPA × (1 + g) / (r - g)
    
    Args:
        dpa: Dividendo por Ação atual
        taxa_crescimento: Taxa de crescimento perpétuo dos dividendos (g)
        taxa_desconto: Taxa de desconto/retorno exigido (r)
    
    Returns:
        Preço justo ou None
    """
    if not dpa or dpa <= 0:
        return None
    if taxa_desconto <= taxa_crescimento:
        return None  # Modelo não funciona se g >= r
    
    return dpa * (1 + taxa_crescimento) / (taxa_desconto - taxa_crescimento)


def calcular_margem_seguranca(preco_justo: float, preco_atual: float) -> float:
    """Calcula margem de segurança (% de desconto)"""
    if not preco_justo or preco_justo == 0:
        return 0
    return (preco_justo - preco_atual) / preco_justo


def classificar_preco(margem: float) -> str:
    """Classifica o preço baseado na margem de segurança"""
    if margem >= 0.30:
        return "MUITO BARATO"
    elif margem >= 0.15:
        return "BARATO"
    elif margem >= -0.10:
        return "JUSTO"
    elif margem >= -0.30:
        return "CARO"
    else:
        return "MUITO CARO"


def analisar_valuation(preco_atual: float, lpa: float, vpa: float, 
                        dpa: float, selic: float = 10.75) -> Dict[str, ValuationResult]:
    """
    Realiza análise completa de valuation usando múltiplos métodos
    
    Args:
        preco_atual: Preço atual da ação
        lpa: Lucro por Ação
        vpa: Valor Patrimonial por Ação
        dpa: Dividendo por Ação
        selic: Taxa SELIC atual
    
    Returns:
        Dicionário com resultados de cada método
    """
    resultados = {}
    
    # 1. Graham Original
    pj_graham = graham_formula_original(lpa, vpa)
    if pj_graham:
        margem = calcular_margem_seguranca(pj_graham, preco_atual)
        resultados['graham'] = ValuationResult(
            metodo="Graham (Original)",
            preco_justo=pj_graham,
            preco_atual=preco_atual,
            margem_seguranca=margem,
            recomendacao=classificar_preco(margem),
            explicacao=f"√(22.5 × LPA × VPA) = √(22.5 × {lpa:.2f} × {vpa:.2f})"
        )
    
    # 2. Graham Ajustado (para juros brasileiros)
    pj_graham_adj = graham_formula(lpa, vpa, selic)
    if pj_graham_adj:
        margem = calcular_margem_seguranca(pj_graham_adj, preco_atual)
        resultados['graham_ajustado'] = ValuationResult(
            metodo="Graham (Ajustado BR)",
            preco_justo=pj_graham_adj,
            preco_atual=preco_atual,
            margem_seguranca=margem,
            recomendacao=classificar_preco(margem),
            explicacao=f"Fórmula ajustada para SELIC de {selic:.2f}%"
        )
    
    # 3. Bazin
    pj_bazin = bazin_formula(dpa)
    if pj_bazin:
        margem = calcular_margem_seguranca(pj_bazin, preco_atual)
        resultados['bazin'] = ValuationResult(
            metodo="Bazin (DY 6%)",
            preco_justo=pj_bazin,
            preco_atual=preco_atual,
            margem_seguranca=margem,
            recomendacao=classificar_preco(margem),
            explicacao=f"DPA / 6% = {dpa:.2f} / 0.06"
        )
    
    # 4. Gordon DDM (se tiver dividendos)
    if dpa and dpa > 0:
        # Estima taxa de desconto como SELIC + prêmio de risco (5%)
        taxa_desconto = (selic / 100) + 0.05
        pj_gordon = gordon_ddm(dpa, taxa_crescimento=0.03, taxa_desconto=taxa_desconto)
        if pj_gordon:
            margem = calcular_margem_seguranca(pj_gordon, preco_atual)
            resultados['gordon'] = ValuationResult(
                metodo="Gordon DDM",
                preco_justo=pj_gordon,
                preco_atual=preco_atual,
                margem_seguranca=margem,
                recomendacao=classificar_preco(margem),
                explicacao=f"DPA × (1+g) / (r-g), com g=3% e r={taxa_desconto*100:.1f}%"
            )
    
    return resultados


if __name__ == "__main__":
    # Teste com ITUB4 (valores aproximados)
    resultado = analisar_valuation(
        preco_atual=32.50,
        lpa=4.15,
        vpa=22.80,
        dpa=1.50,
        selic=10.75
    )
    
    print("Análise de Valuation - ITUB4")
    print("=" * 50)
    for nome, val in resultado.items():
        print(f"\n{val.metodo}:")
        print(f"  Preço Justo: R$ {val.preco_justo:.2f}")
        print(f"  Margem de Segurança: {val.margem_seguranca*100:.1f}%")
        print(f"  Recomendação: {val.recomendacao}")
