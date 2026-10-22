from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from models import MarketTrend
from app.services.meta_ads import meta_ads_service

router = APIRouter(prefix="/api/competitors", tags=["Competitor & Meta Ads Intelligence"])

@router.get("/analyze")
async def analyze_competitor_ads(
    keyword: str = Query(..., description="Termo ou infoproduto para analisar"),
    niche: Optional[str] = Query("Geral", description="Nicho do produto")
):
    """
    Analisa os anúncios ativos na Biblioteca de Anúncios da Meta para o termo pesquisado.
    """
    analysis = await meta_ads_service.analyze_keyword_ads(keyword, niche)
    return analysis

@router.post("/analyze-trend/{trend_id}")
async def analyze_and_attach_to_trend(
    trend_id: int,
    db: Session = Depends(get_db)
):
    """
    Executa a análise de concorrência da Meta para uma tendência existente
    e salva o resultado nos metadados da tabela market_trends do Supabase.
    """
    trend = db.query(MarketTrend).filter(MarketTrend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=404, detail="Tendência não encontrada")

    analysis = await meta_ads_service.analyze_keyword_ads(trend.keyword, trend.niche or "Geral")

    # Attach to raw_metadata
    current_meta = trend.raw_metadata or {}
    current_meta["meta_ads_intelligence"] = analysis
    trend.raw_metadata = current_meta

    db.commit()
    db.refresh(trend)

    return {
        "status": "success",
        "trend_id": trend.id,
        "keyword": trend.keyword,
        "ad_intelligence": analysis
    }
