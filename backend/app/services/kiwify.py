import logging
import httpx
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models import Product, ProductStatus, Platform

logger = logging.getLogger("lowticket-kiwify")

KIWIFY_OAUTH_URL = "https://public-api.kiwify.com/v1/oauth/token"
KIWIFY_API_BASE = "https://public-api.kiwify.com/v1"

class KiwifyService:
    @staticmethod
    async def get_access_token(client_id: str, client_secret: str) -> Dict[str, Any]:
        """Obtém token OAuth 2.0 da Kiwify."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip()
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            try:
                res = await client.post(KIWIFY_OAUTH_URL, data=payload, headers=headers)
                data = res.json()
                if res.status_code != 200:
                    error_msg = data.get("message") or data.get("error") or res.text
                    return {"success": False, "error": f"Erro {res.status_code}: {error_msg}"}
                
                access_token = data.get("access_token")
                return {
                    "success": True, 
                    "access_token": access_token, 
                    "expires_in": data.get("expires_in")
                }
            except Exception as e:
                logger.error(f"Erro ao autenticar com Kiwify: {e}")
                return {"success": False, "error": str(e)}

    @classmethod
    async def test_connection(cls, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Testa se as credenciais da Kiwify são válidas."""
        token_res = await cls.get_access_token(client_id, client_secret)
        if not token_res.get("success"):
            return {
                "connected": False,
                "message": f"Falha na autenticação: {token_res.get('error')}"
            }
        return {
            "connected": True,
            "message": "Conexão com a Kiwify validada com sucesso! API pronta."
        }

    @classmethod
    async def fetch_products(cls, client_id: str, client_secret: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Busca produtos cadastrados na Kiwify."""
        token_res = await cls.get_access_token(client_id, client_secret)
        if not token_res.get("success"):
            return {"success": False, "error": token_res.get("error"), "products": []}

        access_token = token_res["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        if account_id:
            headers["x-kiwify-account-id"] = account_id.strip()
        elif client_id:
            headers["x-kiwify-account-id"] = client_id.strip()

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(f"{KIWIFY_API_BASE}/products", headers=headers)
                if res.status_code != 200:
                    return {
                        "success": False, 
                        "error": f"Erro {res.status_code} da Kiwify: {res.text}", 
                        "products": []
                    }
                
                body = res.json()
                products_raw = body.get("data") or body.get("products") or body
                if not isinstance(products_raw, list):
                    products_raw = []

                cleaned_products = []
                for p in products_raw:
                    # Extrai link de checkout ou URL do produto
                    checkout = p.get("checkout_url") or p.get("url") or p.get("link") or ""
                    price_val = p.get("price") or p.get("amount") or 0.0
                    if isinstance(price_val, (int, float)) and price_val > 1000:
                        # Se veio em centavos (ex: 3700 para R$ 37,00)
                        price_val = price_val / 100.0

                    prod_id = p.get("id")
                    # Se faltou checkout ou preço (comum na listagem resumida da Kiwify API), busca os detalhes do produto
                    if prod_id and (not checkout or price_val == 0.0):
                        try:
                            det_res = await client.get(f"{KIWIFY_API_BASE}/products/{prod_id}", headers=headers)
                            if det_res.status_code == 200:
                                det_data = det_res.json()
                                links = det_data.get("links", [])
                                for lk in links:
                                    if not lk.get("is_sales_page") and lk.get("id"):
                                        checkout = f"https://pay.kiwify.com.br/{lk['id']}"
                                        if lk.get("price") and price_val == 0.0:
                                            price_val = lk.get("price") / 100.0
                                        break
                                if price_val == 0.0 and det_data.get("offers"):
                                    first_offer = det_data["offers"][0]
                                    if first_offer.get("price"):
                                        price_val = first_offer.get("price") / 100.0
                        except Exception as det_err:
                            logger.warning(f"Erro ao buscar detalhes da Kiwify para {prod_id}: {det_err}")

                    cleaned_products.append({
                        "kiwify_id": prod_id,
                        "title": p.get("name") or p.get("title") or "Produto Kiwify",
                        "price": float(price_val),
                        "checkout_url": checkout,
                        "status": p.get("status", "active"),
                        "raw": p
                    })

                return {"success": True, "products": cleaned_products}
            except Exception as e:
                logger.error(f"Erro ao listar produtos da Kiwify: {e}")
                return {"success": False, "error": str(e), "products": []}

    @classmethod
    async def sync_to_database(cls, db: Session, client_id: str, client_secret: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Sincroniza produtos da Kiwify diretamente para o Kanban do Supabase."""
        fetch_res = await cls.fetch_products(client_id, client_secret, account_id)
        if not fetch_res.get("success"):
            return fetch_res

        kiwify_products = fetch_res["products"]
        created_count = 0
        updated_count = 0

        for kp in kiwify_products:
            title = kp["title"].strip()
            checkout = kp["checkout_url"]
            price = Decimal(str(kp["price"]))

            # Procura por título correspondente ou URL
            existing = db.query(Product).filter(
                (Product.title.ilike(title)) | 
                (Product.checkout_url == checkout)
            ).first()

            if existing:
                # Atualiza link de checkout se não tiver
                if checkout:
                    existing.checkout_url = checkout
                    if existing.status == ProductStatus.IDEA:
                        existing.status = ProductStatus.READY
                if price > 0 and (existing.price == 0 or existing.price is None or existing.price == Decimal("37.00")):
                    existing.price = price
                updated_count += 1
            else:
                # Dedução inteligente do nicho baseado no título
                lower_t = title.lower()
                if any(k in lower_t for k in ["colorir", "desenho", "criança", "infantil", "fauna", "amigurumi", "artesanato"]):
                    inferred_niche = "Infantil & Hobbies"
                elif any(k in lower_t for k in ["concurso", "oab", "enem", "prova", "apostila"]):
                    inferred_niche = "Concursos & Carreiras"
                elif any(k in lower_t for k in ["finan", "invest", "renda", "dinheiro", "planilha"]):
                    inferred_niche = "Finanças & Produtividade"
                elif any(k in lower_t for k in ["saude", "dieta", "emagrec", "treino"]):
                    inferred_niche = "Saúde & Bem-estar"
                else:
                    inferred_niche = "Geral"

                slug = title.lower().replace(" ", "-").replace("/", "-")
                new_prod = Product(
                    title=title,
                    slug=slug[:100],
                    niche=inferred_niche,
                    price=price if price > 0 else Decimal("9.90"),
                    checkout_url=checkout if checkout else None,
                    status=ProductStatus.READY if checkout else ProductStatus.IDEA
                )
                db.add(new_prod)
                created_count += 1

        db.commit()
        return {
            "success": True,
            "total_found": len(kiwify_products),
            "created_count": created_count,
            "updated_count": updated_count,
            "products": kiwify_products
        }
