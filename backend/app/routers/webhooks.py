import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from models import Order, Product, OrderStatus, Platform
from app.services.webhook_parser import parse_incoming_webhook

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks Ingestion"])

@router.post("/order")
async def receive_order_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Universal webhook receiver for Kiwify, Hotmart, Eduzz, Braip.
    Stores and associates orders directly with Supabase Product models.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corpo da requisição deve ser um JSON válido")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload inválido")

    # Normalize incoming payload
    order_data = parse_incoming_webhook(payload)
    ext_id = order_data["external_order_id"]

    # Idempotency check: see if order already exists
    existing_order = db.query(Order).filter(Order.external_order_id == ext_id).first()
    if existing_order:
        existing_order.status = order_data["status"]
        if order_data.get("gross_amount"):
            existing_order.gross_amount = order_data["gross_amount"]
        if order_data.get("net_amount"):
            existing_order.net_amount = order_data["net_amount"]
        existing_order.payload_raw = order_data.get("payload_raw")
        db.commit()
        db.refresh(existing_order)
        return {
            "status": "updated",
            "message": "Pedido existente atualizado no Supabase",
            "order_id": existing_order.id,
            "external_order_id": existing_order.external_order_id
        }

    # Match Product by ID or title
    matched_product = None
    if order_data.get("product_id"):
        matched_product = db.query(Product).filter(Product.id == order_data["product_id"]).first()

    if not matched_product and order_data.get("product_name"):
        clean_name = order_data["product_name"].strip().lower()
        matched_product = db.query(Product).filter(Product.title.ilike(f"%{clean_name}%")).first()

    product_id = matched_product.id if matched_product else order_data.get("product_id")

    new_order = Order(
        platform=order_data["platform"],
        external_order_id=ext_id,
        product_id=product_id,
        gross_amount=order_data["gross_amount"],
        net_amount=order_data.get("net_amount"),
        currency=order_data.get("currency", "BRL"),
        status=order_data["status"],
        customer_name=order_data.get("customer_name"),
        customer_email=order_data.get("customer_email"),
        customer_phone=order_data.get("customer_phone"),
        payload_raw=order_data.get("payload_raw")
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "status": "success",
        "message": f"Venda processada com sucesso via {order_data['platform'].value.title()}",
        "order": {
            "id": new_order.id,
            "platform": new_order.platform.value,
            "external_order_id": new_order.external_order_id,
            "product_id": new_order.product_id,
            "gross_amount": float(new_order.gross_amount),
            "net_amount": float(new_order.net_amount) if new_order.net_amount else None,
            "status": new_order.status.value,
            "customer_name": new_order.customer_name,
            "customer_email": new_order.customer_email
        }
    }

@router.post("/simulate")
def simulate_purchase(
    platform: str = "kiwify",
    amount: float = 27.90,
    product_title: str = "Planner Financeiro Definitivo Notion + Planilha",
    customer_name: str = "Mariana Silva",
    customer_email: str = "mariana.silva@email.com",
    db: Session = Depends(get_db)
):
    """
    Helper endpoint to generate realistic simulated webhook events.
    """
    tx_id = f"SIM-{platform[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"

    if platform.lower() == "kiwify":
        payload = {
            "order_id": tx_id,
            "order_status": "paid",
            "order_amount": int(amount * 100),
            "Product": {
                "product_name": product_title,
                "product_id": "kwf_prod_101"
            },
            "Customer": {
                "full_name": customer_name,
                "email": customer_email,
                "mobile": "+5511999998888"
            },
            "Commissions": {
                "charge_amount": int(amount * 100),
                "my_commission": int(amount * 91)
            }
        }
    elif platform.lower() == "hotmart":
        payload = {
            "data": {
                "purchase": {
                    "transaction": tx_id,
                    "status": "APPROVED",
                    "price": {"value": amount}
                },
                "product": {"name": product_title},
                "buyer": {
                    "name": customer_name,
                    "email": customer_email,
                    "checkout_phone": "+5521988887777"
                }
            }
        }
    else:
        payload = {
            "external_order_id": tx_id,
            "platform": platform,
            "product_name": product_title,
            "gross_amount": amount,
            "status": "paid",
            "customer_name": customer_name,
            "customer_email": customer_email
        }

    order_data = parse_incoming_webhook(payload)
    
    # Check matching product
    matched_product = db.query(Product).filter(Product.title.ilike(f"%{product_title.strip()}%")).first()

    order = Order(
        platform=order_data["platform"],
        external_order_id=order_data["external_order_id"],
        product_id=matched_product.id if matched_product else None,
        gross_amount=order_data["gross_amount"],
        net_amount=order_data.get("net_amount"),
        currency="BRL",
        status=order_data["status"],
        customer_name=order_data.get("customer_name"),
        customer_email=order_data.get("customer_email"),
        customer_phone=order_data.get("customer_phone"),
        payload_raw=order_data.get("payload_raw")
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "status": "simulated",
        "message": f"Simulação de venda criada via {platform.title()}",
        "order": {
            "id": order.id,
            "platform": order.platform.value,
            "external_order_id": order.external_order_id,
            "product_title": matched_product.title if matched_product else product_title,
            "gross_amount": float(order.gross_amount),
            "net_amount": float(order.net_amount) if order.net_amount else None,
            "status": order.status.value,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email
        }
    }
