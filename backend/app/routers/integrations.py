import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from models import AppSetting
from app.services.kiwify import KiwifyService

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])

class KiwifyConfigPayload(BaseModel):
    client_id: str
    client_secret: str
    account_id: Optional[str] = None

class KiwifyConfigResponse(BaseModel):
    configured: bool
    client_id: Optional[str] = None
    account_id: Optional[str] = None
    masked_secret: Optional[str] = None
    updated_at: Optional[str] = None

def get_saved_kiwify_config(db: Session) -> dict:
    setting = db.query(AppSetting).filter(AppSetting.key == "kiwify").first()
    if setting and setting.value:
        return setting.value
    # Fallback to env vars if present
    env_id = os.getenv("KIWIFY_CLIENT_ID")
    env_secret = os.getenv("KIWIFY_CLIENT_SECRET")
    if env_id and env_secret:
        return {
            "client_id": env_id,
            "client_secret": env_secret,
            "account_id": os.getenv("KIWIFY_ACCOUNT_ID", env_id)
        }
    return {}

@router.get("/kiwify", response_model=KiwifyConfigResponse)
def get_kiwify_settings(db: Session = Depends(get_db)):
    """Retorna as configurações atuais da Kiwify com segredo mascarado."""
    config = get_saved_kiwify_config(db)
    if not config or not config.get("client_id") or not config.get("client_secret"):
        return KiwifyConfigResponse(configured=False)
    
    secret = config.get("client_secret", "")
    masked = f"{secret[:4]}...{secret[-4:]}" if len(secret) > 8 else "****"
    
    setting = db.query(AppSetting).filter(AppSetting.key == "kiwify").first()
    updated_str = setting.updated_at.isoformat() if setting and setting.updated_at else None

    return KiwifyConfigResponse(
        configured=True,
        client_id=config.get("client_id"),
        account_id=config.get("account_id"),
        masked_secret=masked,
        updated_at=updated_str
    )

@router.post("/kiwify")
def save_kiwify_settings(payload: KiwifyConfigPayload, db: Session = Depends(get_db)):
    """Salva ou atualiza as credenciais da API da Kiwify."""
    client_id = payload.client_id.strip()
    client_secret = payload.client_secret.strip()
    account_id = payload.account_id.strip() if payload.account_id else client_id

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Client ID e Client Secret são obrigatórios")

    setting = db.query(AppSetting).filter(AppSetting.key == "kiwify").first()
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "account_id": account_id,
        "updated_at": datetime.now().isoformat()
    }

    if setting:
        setting.value = data
    else:
        setting = AppSetting(key="kiwify", value=data)
        db.add(setting)

    db.commit()
    return {"message": "Credenciais da Kiwify salvas com sucesso!", "success": True}

@router.post("/kiwify/test")
async def test_kiwify_connection(payload: Optional[KiwifyConfigPayload] = None, db: Session = Depends(get_db)):
    """Testa se as credenciais da Kiwify conseguem se conectar."""
    if payload and payload.client_id and payload.client_secret:
        cid = payload.client_id
        csec = payload.client_secret
    else:
        config = get_saved_kiwify_config(db)
        cid = config.get("client_id")
        csec = config.get("client_secret")

    if not cid or not csec:
        raise HTTPException(status_code=400, detail="Nenhuma credencial informada ou salva")

    res = await KiwifyService.test_connection(cid, csec)
    return res

@router.post("/kiwify/sync")
async def sync_kiwify_products(db: Session = Depends(get_db)):
    """Sincroniza todos os produtos da Kiwify para o Kanban do Supabase."""
    config = get_saved_kiwify_config(db)
    cid = config.get("client_id")
    csec = config.get("client_secret")
    acc_id = config.get("account_id")

    if not cid or not csec:
        raise HTTPException(
            status_code=400, 
            detail="Configure a API da Kiwify (Client ID e Secret) antes de sincronizar"
        )

    res = await KiwifyService.sync_to_database(db, cid, csec, acc_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Erro ao sincronizar com Kiwify"))

    return res
