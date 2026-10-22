import uuid
from decimal import Decimal
from typing import Dict, Any
from models import Platform, OrderStatus

def parse_incoming_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses and normalizes webhook payloads from Kiwify, Hotmart, Eduzz, Braip
    into the exact Supabase Order schema.
    """
    # 1. Hotmart Webhook format
    if "data" in payload and isinstance(payload["data"], dict) and ("purchase" in payload["data"] or "product" in payload["data"]):
        data = payload["data"]
        purchase = data.get("purchase", {})
        product = data.get("product", {})
        buyer = data.get("buyer", {})
        price_info = purchase.get("price", {})
        
        status_raw = str(purchase.get("status", "APPROVED")).upper()
        status_map = {
            "APPROVED": OrderStatus.PAID,
            "COMPLETE": OrderStatus.PAID,
            "REFUNDED": OrderStatus.REFUNDED,
            "WAITING_PAYMENT": OrderStatus.WAITING_PAYMENT,
            "CHARGEBACK": OrderStatus.CHARGEBACK,
            "CANCELED": OrderStatus.CANCELED
        }

        gross = 0.0
        if isinstance(price_info, dict) and "value" in price_info:
            gross = float(price_info["value"])
        elif "price" in purchase and isinstance(purchase["price"], (int, float)):
            gross = float(purchase["price"])

        # Hotmart tax usually ~9.9% + R$ 1,00
        net = round(gross * 0.90, 2) if gross > 0 else 0.0

        return {
            "platform": Platform.HOTMART,
            "external_order_id": str(purchase.get("transaction") or f"HOT-{uuid.uuid4().hex[:8]}"),
            "product_name": str(product.get("name", "Infoproduto Hotmart")),
            "product_id": None,
            "gross_amount": Decimal(str(gross)),
            "net_amount": Decimal(str(net)),
            "currency": "BRL",
            "status": status_map.get(status_raw, OrderStatus.PAID),
            "customer_name": buyer.get("name"),
            "customer_email": buyer.get("email"),
            "customer_phone": buyer.get("checkout_phone"),
            "payload_raw": payload
        }

    # 2. Kiwify Webhook format
    if "order_id" in payload or "order_ref" in payload or "Kiwify" in str(payload):
        product_info = payload.get("Product", {})
        customer_info = payload.get("Customer", {})
        commissions = payload.get("Commissions", {})

        gross = 0.0
        if "order_amount" in payload and payload["order_amount"] is not None:
            val = float(payload["order_amount"])
            gross = val / 100.0 if val > 100 else val
        elif "charge_amount" in commissions and commissions["charge_amount"] is not None:
            val = float(commissions["charge_amount"])
            gross = val / 100.0 if val > 100 else val
        elif "gross_amount" in payload or "amount" in payload:
            gross = float(payload.get("gross_amount", payload.get("amount", 27.0)))

        net = gross
        if "my_commission" in commissions and commissions["my_commission"]:
            comm = float(commissions["my_commission"])
            net = comm / 100.0 if comm > 100 else comm
        else:
            net = round(gross * 0.91, 2)

        status_raw = str(payload.get("order_status", "paid")).lower()
        status_map = {
            "paid": OrderStatus.PAID,
            "approved": OrderStatus.PAID,
            "refunded": OrderStatus.REFUNDED,
            "waiting_payment": OrderStatus.WAITING_PAYMENT,
            "chargedback": OrderStatus.CHARGEBACK,
            "canceled": OrderStatus.CANCELED
        }

        return {
            "platform": Platform.KIWIFY,
            "external_order_id": str(payload.get("order_id") or payload.get("order_ref") or payload.get("external_order_id") or f"KWF-{uuid.uuid4().hex[:8]}"),
            "product_name": product_info.get("product_name") or payload.get("product_name", "Infoproduto Kiwify"),
            "product_id": payload.get("product_id"),
            "gross_amount": Decimal(str(round(gross, 2))),
            "net_amount": Decimal(str(round(net, 2))),
            "currency": "BRL",
            "status": status_map.get(status_raw, OrderStatus.PAID),
            "customer_name": customer_info.get("full_name") or payload.get("customer_name"),
            "customer_email": customer_info.get("email") or payload.get("customer_email"),
            "customer_phone": customer_info.get("mobile") or payload.get("customer_phone"),
            "payload_raw": payload
        }

    # 3. Braip Webhook format
    if "type_post" in payload or "trans_key" in payload or "braip" in str(payload).lower():
        status_map = {
            "1": OrderStatus.WAITING_PAYMENT,
            "2": OrderStatus.PAID,
            "3": OrderStatus.CANCELED,
            "4": OrderStatus.REFUNDED,
            "5": OrderStatus.CHARGEBACK
        }
        status_raw = str(payload.get("trans_status", "2"))
        val = float(payload.get("trans_total_value", payload.get("gross_amount", 27.0)))
        return {
            "platform": Platform.BRAIP,
            "external_order_id": str(payload.get("trans_key") or f"BRP-{uuid.uuid4().hex[:8]}"),
            "product_name": payload.get("prod_name", "Infoproduto Braip"),
            "product_id": payload.get("product_id"),
            "gross_amount": Decimal(str(val)),
            "net_amount": Decimal(str(round(val * 0.90, 2))),
            "currency": "BRL",
            "status": status_map.get(status_raw, OrderStatus.PAID),
            "customer_name": payload.get("client_name"),
            "customer_email": payload.get("client_email"),
            "customer_phone": payload.get("client_cel"),
            "payload_raw": payload
        }

    # 4. Eduzz Webhook format
    if "trans_cod" in payload:
        trans_status = payload.get("trans_status")
        val = float(payload.get("trans_value", 27.0))
        return {
            "platform": Platform.EDUZZ,
            "external_order_id": str(payload.get("trans_cod")),
            "product_name": str(payload.get("pro_name", "Infoproduto Eduzz")),
            "product_id": payload.get("product_id"),
            "gross_amount": Decimal(str(val)),
            "net_amount": Decimal(str(round(val * 0.90, 2))),
            "currency": "BRL",
            "status": OrderStatus.PAID if str(trans_status) in ["3", "4", "pago", "paid"] else OrderStatus.WAITING_PAYMENT,
            "customer_name": payload.get("cus_name"),
            "customer_email": payload.get("cus_email"),
            "customer_phone": payload.get("cus_cel"),
            "payload_raw": payload
        }

    # 5. Generic/Test webhook
    raw_platform = str(payload.get("platform", "kiwify")).lower()
    platform_map = {
        "kiwify": Platform.KIWIFY,
        "hotmart": Platform.HOTMART,
        "eduzz": Platform.EDUZZ,
        "braip": Platform.BRAIP
    }
    gross_val = float(payload.get("gross_amount", payload.get("amount", 27.00)))
    
    return {
        "platform": platform_map.get(raw_platform, Platform.OTHER),
        "external_order_id": str(payload.get("external_order_id") or payload.get("transaction_id") or f"TX-{uuid.uuid4().hex[:8].upper()}"),
        "product_name": payload.get("product_name", "Infoproduto Digital"),
        "product_id": payload.get("product_id"),
        "gross_amount": Decimal(str(gross_val)),
        "net_amount": Decimal(str(round(gross_val * 0.91, 2))),
        "currency": "BRL",
        "status": OrderStatus.PAID,
        "customer_name": payload.get("customer_name", "Cliente Teste"),
        "customer_email": payload.get("customer_email", "cliente@teste.com"),
        "customer_phone": payload.get("customer_phone"),
        "payload_raw": payload
    }
