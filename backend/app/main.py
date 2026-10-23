import logging
from decimal import Decimal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from models import (
    MarketTrend,
    Product,
    Order,
    TrendStatus,
    ProductStatus,
    Platform,
    OrderStatus
)
from app.routers import trends, products, orders, webhooks, competitors, integrations, ai_ads, ebooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lowticket-api")

def seed_initial_data():
    """Seed initial realistic data matching the Supabase schema (apenas uma vez)."""
    db = SessionLocal()
    try:
        # Verifica se o seed inicial já foi executado. Se sim, respeita os dados e exclusões do usuário!
        already_seeded = db.query(AppSetting).filter(AppSetting.key == "system_initial_seed").first()
        if already_seeded:
            logger.info("Seed inicial já executado anteriormente. Preservando exclusões e estado do banco.")
            return

        # Check if trends exist
        if db.query(MarketTrend).count() == 0:
            logger.info("Populando tendências iniciais (schema Supabase)...")
            initial_trends = [
                MarketTrend(
                    keyword="Apostila Concurso Caixa 2026",
                    niche="Concursos",
                    source="google_trends",
                    relative_interest=96,
                    trend_growth_pct=142.50,
                    status=TrendStatus.APPROVED,
                    raw_metadata={"region": "BR", "rising_queries": ["edital caixa 2026", "concurso bancario"]}
                ),
                MarketTrend(
                    keyword="Planner Financeiro Notion 2026",
                    niche="Finanças",
                    source="google_trends",
                    relative_interest=88,
                    trend_growth_pct=98.00,
                    status=TrendStatus.APPROVED,
                    raw_metadata={"region": "BR", "category": "Finanças Pessoais"}
                ),
                MarketTrend(
                    keyword="Guia Prático Amigurumi para Iniciantes",
                    niche="Artesanato",
                    source="google_trends",
                    relative_interest=74,
                    trend_growth_pct=45.20,
                    status=TrendStatus.ANALYZING,
                    raw_metadata={"region": "BR", "cpa_estimate": 8.50}
                ),
                MarketTrend(
                    keyword="Caderno de Questões OAB 1a Fase",
                    niche="Direito & Concursos",
                    source="google_trends",
                    relative_interest=82,
                    trend_growth_pct=67.80,
                    status=TrendStatus.APPROVED,
                    raw_metadata={"region": "BR"}
                ),
                MarketTrend(
                    keyword="Protocolo Treino em Casa 15 Minutos",
                    niche="Saúde & Fitness",
                    source="google_trends",
                    relative_interest=65,
                    trend_growth_pct=32.40,
                    status=TrendStatus.NEW,
                    raw_metadata={"region": "BR"}
                ),
            ]
            db.add_all(initial_trends)
            db.commit()

        # Check if products exist
        if db.query(Product).count() == 0:
            logger.info("Populando produtos e pedidos no backoffice...")
            p1 = Product(
                title="Apostila Digital Caixa Econômica 2026 (Reta Final)",
                slug="apostila-caixa-2026-reta-final",
                niche="Concursos",
                description="Resumos estratégicos, mapas mentais e 500 questões comentadas focadas na banca.",
                price=Decimal("37.00"),
                checkout_url="https://pay.kiwify.com.br/demo-caixa-2026",
                delivery_url="https://drive.google.com/drive/folders/demo-caixa-pdf",
                status=ProductStatus.ACTIVE,
                trend_id=1
            )
            p2 = Product(
                title="Planner Financeiro Definitivo Notion + Planilha",
                slug="planner-financeiro-definitivo-notion",
                niche="Finanças",
                description="Template pronto para controle de gastos, investimentos e metas financeiras.",
                price=Decimal("27.90"),
                checkout_url="https://pay.kiwify.com.br/demo-planner-notion",
                delivery_url="https://notion.so/templates/demo-planner-template",
                status=ProductStatus.ACTIVE,
                trend_id=2
            )
            p3 = Product(
                title="Guia Ilustrado Amigurumi Passo a Passo",
                slug="guia-amigurumi-iniciantes",
                niche="Artesanato",
                description="Mais de 30 receitas exclusivas com vídeos de suporte para confecção rápida.",
                price=Decimal("19.90"),
                checkout_url="https://pay.hotmart.com/demo-amigurumi",
                delivery_url="https://alchemylow.shop/entrega/amigurumi",
                status=ProductStatus.IN_PRODUCTION,
                trend_id=3
            )
            p4 = Product(
                title="Super Combo 1000 Questões OAB Comentadas",
                slug="combo-1000-questoes-oab",
                niche="Direito & Concursos",
                description="Banco de questões separadas por disciplina com gabarito fundamentado.",
                price=Decimal("47.00"),
                checkout_url=None,
                delivery_url=None,
                status=ProductStatus.IDEA,
                trend_id=4
            )
            db.add_all([p1, p2, p3, p4])
            db.commit()

            # Seed orders
            o1 = Order(
                platform=Platform.KIWIFY,
                external_order_id="KWF-98347201",
                product_id=p1.id,
                gross_amount=Decimal("37.00"),
                net_amount=Decimal("33.67"),
                currency="BRL",
                status=OrderStatus.PAID,
                customer_name="Mariana Souza",
                customer_email="mariana.souza@gmail.com",
                customer_phone="+5511998877665",
                payload_raw={"source": "seed"}
            )
            o2 = Order(
                platform=Platform.KIWIFY,
                external_order_id="KWF-98347202",
                product_id=p1.id,
                gross_amount=Decimal("37.00"),
                net_amount=Decimal("33.67"),
                currency="BRL",
                status=OrderStatus.PAID,
                customer_name="Carlos Eduardo Lima",
                customer_email="carlos.edu@hotmail.com",
                payload_raw={"source": "seed"}
            )
            o3 = Order(
                platform=Platform.HOTMART,
                external_order_id="HOT-10492811",
                product_id=p2.id,
                gross_amount=Decimal("27.90"),
                net_amount=Decimal("24.84"),
                currency="BRL",
                status=OrderStatus.PAID,
                customer_name="Rodrigo Nogueira",
                customer_email="rodrigo.nog@gmail.com",
                payload_raw={"source": "seed"}
            )
            db.add_all([o1, o2, o3])
            db.commit()

        # Marca permanentemente no banco Supabase que o seed inicial já foi feito
        if not db.query(AppSetting).filter(AppSetting.key == "system_initial_seed").first():
            db.add(AppSetting(key="system_initial_seed", value={"completed": True}))
            db.commit()

    except Exception as e:
        logger.error(f"Erro ao popular dados iniciais: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables using the unified models.py
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

app = FastAPI(
    title="Plataforma LowTicket API",
    description="Motor de Inteligência de Mercado e Backoffice de Infoprodutos Low Ticket (Supabase Ready)",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(trends.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(webhooks.router)
app.include_router(competitors.router)
app.include_router(integrations.router)
app.include_router(ai_ads.router)
app.include_router(ebooks.router)

@app.get("/api/health")
def api_health():
    return {
        "app": "Plataforma LowTicket API",
        "version": "2.0.0",
        "status": "online",
        "database_target": "Supabase PostgreSQL Ready",
        "docs_url": "/docs"
    }

# Static Frontend SPA serving (for Docker / Easypanel container deployment)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

# Detect frontend dist location (Docker container or local workspace)
frontend_dist = os.environ.get("FRONTEND_DIST")
if not frontend_dist or not os.path.exists(frontend_dist):
    # Check Docker path
    if os.path.exists("/app/frontend_dist"):
        frontend_dist = "/app/frontend_dist"
    else:
        # Check relative local repo path
        local_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
        if os.path.exists(local_dist):
            frontend_dist = local_dist

if frontend_dist and os.path.exists(os.path.join(frontend_dist, "index.html")):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Prevent hijacking API, docs, and schema endpoints
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="API route not found")
        target_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target_path):
            return FileResponse(target_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": "Plataforma LowTicket API",
            "version": "2.0.0",
            "status": "online",
            "database_target": "Supabase PostgreSQL Ready",
            "models_schema": "models.py",
            "docs_url": "/docs"
        }

