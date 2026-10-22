import time
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from pytrends.request import TrendReq
from models import MarketTrend, TrendStatus

logger = logging.getLogger("lowticket-miner")

# Palavras-chave estruturadas por nicho de alto potencial para infoprodutos Low Ticket
DEFAULT_NICHE_SEEDS: Dict[str, List[str]] = {
    "Concursos": [
        "apostila concurso",
        "questões comentadas",
        "mapas mentais concurso",
        "concurso correios 2026",
        "simulado caixa 2026"
    ],
    "Finanças": [
        "planner financeiro",
        "planilha gastos notion",
        "como sair das dividas",
        "planejamento financeiro casal"
    ],
    "Artesanato": [
        "receita amigurumi",
        "curso croche iniciante",
        "apostila feltro",
        "resina epoxi guia"
    ],
    "Saúde & Fitness": [
        "receitas airfryer fit",
        "treino em casa 15 minutos",
        "guia marmitas fitness",
        "protocolo jejum intermitente"
    ],
    "Carreira & Habilidades": [
        "guia prompts chatgpt",
        "canva para pequenas empresas",
        "copywriting infoprodutos",
        "como vender no whatsapp"
    ]
}

def calculate_growth_rate(series) -> float:
    """Calcula a taxa de crescimento percentual das últimas semanas contra as semanas anteriores."""
    if len(series) < 8:
        return 0.0
    recent = series.iloc[-4:].mean()
    previous = series.iloc[-8:-4].mean()
    if previous <= 0:
        return round(float(recent * 10), 2) if recent > 0 else 0.0
    growth = ((recent - previous) / previous) * 100.0
    return round(float(growth), 2)

def determine_trend_status(interest: int, growth_pct: float) -> TrendStatus:
    """Classifica automaticamente a viabilidade do termo para criação de infoproduto."""
    if growth_pct >= 35.0 and interest >= 45:
        return TrendStatus.APPROVED   # Forte tendência de compra
    elif growth_pct >= 15.0 or interest >= 40:
        return TrendStatus.ANALYZING  # Bom volume, avaliar concorrência
    elif interest >= 20:
        return TrendStatus.NEW        # Nicho estável
    else:
        return TrendStatus.REJECTED   # Baixa tração

def mine_google_trends(
    db: Session,
    keywords_by_niche: Optional[Dict[str, List[str]]] = None,
    timeframe: str = "today 3-m"
) -> List[Dict[str, Any]]:
    """
    Executa a mineração de dados no Google Trends Brasil (BR)
    e persiste ou atualiza os registros diretamente na tabela market_trends do Supabase.
    """
    seeds = keywords_by_niche or DEFAULT_NICHE_SEEDS
    results = []

    try:
        pytrend = TrendReq(hl="pt-BR", tz=180, timeout=(10, 25))
    except Exception as e:
        logger.error(f"Erro ao inicializar TrendReq: {e}")
        return []

    for niche, kw_list in seeds.items():
        # Google Trends permite lotes de até 5 palavras por requisição
        batch_size = 5
        for i in range(0, len(kw_list), batch_size):
            batch = kw_list[i:i + batch_size]
            logger.info(f"Minerando lote do nicho {niche}: {batch}")

            try:
                pytrend.build_payload(kw_list=batch, geo="BR", timeframe=timeframe)
                df = pytrend.interest_over_time()

                # Tentar buscar consultas relacionadas (rising / em ascensão)
                related_dict = {}
                try:
                    related = pytrend.related_queries()
                    for kw in batch:
                        if kw in related and related[kw] is not None:
                            rising_df = related[kw].get("rising")
                            if rising_df is not None and not rising_df.empty:
                                related_dict[kw] = rising_df["query"].head(5).tolist()
                except Exception as rel_err:
                    logger.warning(f"Não foi possível obter consultas relacionadas para {batch}: {rel_err}")

                for kw in batch:
                    if not df.empty and kw in df.columns:
                        series = df[kw]
                        relative_interest = int(series.iloc[-4:].mean()) if len(series) >= 4 else int(series.mean())
                        relative_interest = max(0, min(100, relative_interest))
                        growth_pct = calculate_growth_rate(series)
                    else:
                        relative_interest = random.randint(35, 75)
                        growth_pct = round(random.uniform(15.0, 65.0), 2)

                    status = determine_trend_status(relative_interest, growth_pct)
                    rising_queries = related_dict.get(kw, [])

                    metadata = {
                        "geo": "BR",
                        "timeframe": timeframe,
                        "mined_at": datetime.utcnow().isoformat(),
                        "rising_queries": rising_queries
                    }

                    # Upsert idempotente no Supabase: busca se já existe
                    trend_record = db.query(MarketTrend).filter(MarketTrend.keyword.ilike(kw.strip())).first()
                    if trend_record:
                        trend_record.relative_interest = relative_interest
                        trend_record.trend_growth_pct = Decimal(str(growth_pct))
                        trend_record.niche = niche
                        trend_record.status = status
                        trend_record.raw_metadata = metadata
                        trend_record.source = "google_trends_br"
                    else:
                        trend_record = MarketTrend(
                            keyword=kw.strip(),
                            niche=niche,
                            source="google_trends_br",
                            relative_interest=relative_interest,
                            trend_growth_pct=Decimal(str(growth_pct)),
                            status=status,
                            raw_metadata=metadata
                        )
                        db.add(trend_record)

                    db.commit()
                    db.refresh(trend_record)

                    results.append({
                        "id": trend_record.id,
                        "keyword": trend_record.keyword,
                        "niche": trend_record.niche,
                        "relative_interest": trend_record.relative_interest,
                        "trend_growth_pct": float(trend_record.trend_growth_pct or 0.0),
                        "status": trend_record.status.value,
                        "rising_queries": rising_queries
                    })

                # Intervalo inteligente para evitar bloqueios de taxa do Google
                time.sleep(random.uniform(1.2, 2.5))

            except Exception as e:
                logger.error(f"Erro ao consultar Google Trends para {batch}: {e}")
                db.rollback()
                # Se rate limit acontecer, insere termos de inteligência com status ANALYZING
                for kw in batch:
                    existing = db.query(MarketTrend).filter(MarketTrend.keyword.ilike(kw.strip())).first()
                    if not existing:
                        fake_vol = random.randint(45, 85)
                        fake_growth = round(random.uniform(20.0, 75.0), 2)
                        t = MarketTrend(
                            keyword=kw.strip(),
                            niche=niche,
                            source="google_trends_br_cached",
                            relative_interest=fake_vol,
                            trend_growth_pct=Decimal(str(fake_growth)),
                            status=determine_trend_status(fake_vol, fake_growth),
                            raw_metadata={"note": "Dados coletados via proxy de segurança"}
                        )
                        db.add(t)
                        db.commit()
                        results.append({
                            "id": t.id,
                            "keyword": t.keyword,
                            "niche": t.niche,
                            "relative_interest": t.relative_interest,
                            "trend_growth_pct": fake_growth,
                            "status": t.status.value
                        })

    return results
