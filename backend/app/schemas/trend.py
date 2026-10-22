from typing import Optional, Any, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from models import TrendStatus

class MarketTrendBase(BaseModel):
    keyword: str
    niche: Optional[str] = "Geral"
    source: str = "google_trends"
    relative_interest: int = 0
    trend_growth_pct: Optional[float] = 0.0
    status: TrendStatus = TrendStatus.NEW
    raw_metadata: Optional[Dict[str, Any]] = None

class MarketTrendCreate(MarketTrendBase):
    pass

class MarketTrendResponse(MarketTrendBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
