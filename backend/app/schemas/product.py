from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models import ProductStatus

class ProductBase(BaseModel):
    title: str
    slug: Optional[str] = None
    niche: str = "Geral"
    description: Optional[str] = None
    price: float = 27.00
    checkout_url: Optional[str] = None
    delivery_url: Optional[str] = None
    status: ProductStatus = ProductStatus.IDEA
    trend_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    niche: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    checkout_url: Optional[str] = None
    delivery_url: Optional[str] = None
    status: Optional[ProductStatus] = None
    trend_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_sales: Optional[int] = 0
    total_revenue: Optional[float] = 0.0

    class Config:
        from_attributes = True
