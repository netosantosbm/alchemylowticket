from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from models import Product, AppSetting
from app.services.ai_copywriter import ai_copywriter

router = APIRouter(prefix="/api/ai-ads", tags=["AI Ad & Copy Generator"])

class GenerateAdRequest(BaseModel):
    product_id: Optional[int] = None
    product_title: Optional[str] = None
    niche: Optional[str] = "Geral"
    price: Optional[float] = 27.0
    competitor_offer: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = "Direto ao ponto, empático e de alta conversão"
    save_to_product: Optional[bool] = False

class SaveKeyRequest(BaseModel):
    provider: str  # "openai" or "gemini"
    api_key: str

@router.get("/settings")
def get_ai_settings(db: Session = Depends(get_db)):
    """Retorna o status de configuração das APIs de IA."""
    openai_setting = db.query(AppSetting).filter(AppSetting.key == "openai_api_key").first()
    gemini_setting = db.query(AppSetting).filter(AppSetting.key == "gemini_api_key").first()

    has_openai = bool(openai_setting and openai_setting.value)
    has_gemini = bool(gemini_setting and gemini_setting.value)

    return {
        "has_openai_key": has_openai,
        "has_gemini_key": has_gemini,
        "active_engine": "OpenAI GPT-4o-mini" if has_openai else ("Google Gemini 1.5" if has_gemini else "Motor Neural Direto (Nativo)")
    }

@router.post("/settings/key")
def save_ai_api_key(req: SaveKeyRequest, db: Session = Depends(get_db)):
    """Salva a chave de API da OpenAI ou Google Gemini no banco Supabase."""
    provider_clean = req.provider.lower().strip()
    key_name = f"{provider_clean}_api_key"

    if provider_clean not in ["openai", "gemini"]:
        raise HTTPException(status_code=400, detail="Provedor inválido. Use 'openai' ou 'gemini'.")

    setting = db.query(AppSetting).filter(AppSetting.key == key_name).first()
    if not setting:
        setting = AppSetting(key=key_name, value={"api_key": req.api_key.strip()})
        db.add(setting)
    else:
        setting.value = {"api_key": req.api_key.strip()}

    db.commit()
    return {"status": "success", "message": f"Chave de API {provider_clean.title()} configurada com sucesso!"}

@router.post("/generate")
async def generate_ads(
    req: GenerateAdRequest,
    db: Session = Depends(get_db)
):
    """
    Gera 3 variações completas de anúncios com ganchos, textos e scripts de vídeo
    a partir de uma oferta concorrente e dados do produto, eliminando riscos de copyright.
    """
    product = None
    title = req.product_title
    niche = req.niche
    price = req.price or 27.0

    if req.product_id:
        product = db.query(Product).filter(Product.id == req.product_id).first()
        if product:
            if not title:
                title = product.title
            if not niche or niche == "Geral":
                niche = product.niche
            if not req.price or req.price == 27.0:
                price = float(product.price)

    if not title:
        raise HTTPException(status_code=400, detail="Título do produto ou product_id é obrigatório.")

    # Executa a geração com IA + Blindagem de Direitos Autorais
    result = await ai_copywriter.generate_ads(
        product_title=title,
        niche=niche or "Geral",
        price=price,
        competitor_offer=req.competitor_offer,
        target_audience=req.target_audience,
        tone=req.tone or "Direto ao ponto, empático e de alta conversão",
        db=db
    )

    # Se solicitado ou vinculado a um produto, salva no registro
    if req.save_to_product and product:
        product.ad_copies = result
        db.commit()
        db.refresh(product)
        result["saved_to_product_id"] = product.id

    return result

@router.get("/product/{product_id}")
def get_product_ads(product_id: int, db: Session = Depends(get_db)):
    """Retorna os anúncios previamente gerados e salvos para um produto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return {
        "product_id": product.id,
        "product_title": product.title,
        "ad_copies": product.ad_copies
    }
