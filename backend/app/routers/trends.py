import re
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from models import MarketTrend, Product, TrendStatus, ProductStatus
from app.schemas.trend import MarketTrendCreate, MarketTrendResponse
from app.schemas.product import ProductResponse
from app.services.trend_collector import mine_google_trends, DEFAULT_NICHE_SEEDS

router = APIRouter(prefix="/api/trends", tags=["Market Trends"])

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)

class MiningRequest(BaseModel):
    niche: Optional[str] = None
    keywords: Optional[List[str]] = None
    timeframe: Optional[str] = "today 3-m"

@router.get("", response_model=List[MarketTrendResponse])
def get_trends(
    niche: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("trend_growth_pct", regex="^(trend_growth_pct|relative_interest|created_at)$"),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(MarketTrend)
    if niche and niche != "Todos":
        query = query.filter(MarketTrend.niche == niche)
    if status and status != "Todos":
        query = query.filter(MarketTrend.status == status)

    if sort_by == "trend_growth_pct":
        query = query.order_by(desc(MarketTrend.trend_growth_pct))
    elif sort_by == "relative_interest":
        query = query.order_by(desc(MarketTrend.relative_interest))
    else:
        query = query.order_by(desc(MarketTrend.created_at))

    return query.limit(limit).all()

@router.get("/seeds")
def get_mining_seeds():
    """Retorna as categorias e palavras-chave monitoradas por padrão."""
    return DEFAULT_NICHE_SEEDS

@router.post("/mine")
def trigger_trend_mining(
    request: Optional[MiningRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Executa a coleta e mineração no Google Trends Brasil (BR)
    e grava/atualiza os termos na tabela market_trends do Supabase.
    """
    seeds = None
    if request and request.niche and request.keywords:
        seeds = {request.niche: request.keywords}
    elif request and request.niche and request.niche in DEFAULT_NICHE_SEEDS:
        seeds = {request.niche: DEFAULT_NICHE_SEEDS[request.niche]}

    timeframe = request.timeframe if request and request.timeframe else "today 3-m"

    mined_results = mine_google_trends(db, keywords_by_niche=seeds, timeframe=timeframe)

    return {
        "status": "success",
        "message": f"Mineração concluída! {len(mined_results)} termos processados e salvos no Supabase.",
        "mined_count": len(mined_results),
        "results": mined_results
    }

@router.post("", response_model=MarketTrendResponse)
def create_trend(trend_in: MarketTrendCreate, db: Session = Depends(get_db)):
    db_trend = MarketTrend(**trend_in.model_dump())
    db.add(db_trend)
    db.commit()
    db.refresh(db_trend)
    return db_trend

@router.post("/{trend_id}/convert-to-product", response_model=ProductResponse)
def convert_trend_to_product(trend_id: int, price: float = 27.0, db: Session = Depends(get_db)):
    trend = db.query(MarketTrend).filter(MarketTrend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=404, detail="Tendência não encontrada")

    # Mark trend as APPROVED
    trend.status = TrendStatus.APPROVED

    # Generate initial product linked directly to this trend
    title = f"Apostila/Guia Prático: {trend.keyword.title()}"
    base_slug = slugify(trend.keyword)
    unique_slug = f"{base_slug}-{trend.id}"
    description = f"Infoproduto gerado da tendência '{trend.keyword}' no nicho {trend.niche}. Crescimento registrado: +{trend.trend_growth_pct}%."

    new_product = Product(
        title=title,
        slug=unique_slug,
        description=description,
        niche=trend.niche or "Geral",
        price=price,
        status=ProductStatus.IDEA,
        trend_id=trend.id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return ProductResponse(
        id=new_product.id,
        title=new_product.title,
        slug=new_product.slug,
        niche=new_product.niche,
        description=new_product.description,
        price=float(new_product.price),
        checkout_url=new_product.checkout_url,
        delivery_url=new_product.delivery_url,
        status=new_product.status,
        trend_id=new_product.trend_id,
        created_at=new_product.created_at,
        updated_at=new_product.updated_at,
        total_sales=0,
        total_revenue=0.0
    )

@router.delete("/{trend_id}")
def delete_trend(trend_id: int, db: Session = Depends(get_db)):
    trend = db.query(MarketTrend).filter(MarketTrend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=404, detail="Tendência não encontrada")
    db.delete(trend)
    db.commit()
    return {"message": "Tendência removida com sucesso"}
