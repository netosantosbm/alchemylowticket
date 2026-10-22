from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models import Platform, OrderStatus

class OrderBase(BaseModel):
    platform: Platform = Platform.KIWIFY
    external_order_id: str
    product_id: Optional[int] = None
    gross_amount: float
    net_amount: Optional[float] = None
    currency: str = "BRL"
    status: OrderStatus = OrderStatus.PAID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

class OrderCreate(OrderBase):
    payload_raw: Optional[Dict[str, Any]] = None

class OrderResponse(OrderBase):
    id: int
    product_title: Optional[str] = None
    order_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SalesSummary(BaseModel):
    total_revenue: float
    net_revenue: float
    total_orders: int
    today_revenue: float
    today_orders: int
    average_ticket: float
    orders_by_platform: Dict[str, int]
    orders_by_status: Dict[str, int]
