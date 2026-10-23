from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- ENUMS ---

class TrendStatus(str, Enum):
    NEW = "new"              # Recém-minerado
    ANALYZING = "analyzing"  # Em validação de concorrência
    APPROVED = "approved"    # Aprovado para virar produto
    REJECTED = "rejected"    # Baixo volume ou inviável


class ProductStatus(str, Enum):
    IDEA = "idea"                  # Rascunho / Brainstorm
    IN_PRODUCTION = "in_production" # Escrevendo apostila / montando material
    READY = "ready"                # Pronto para tráfego
    ACTIVE = "active"              # Vendendo com tráfego ativo
    PAUSED = "paused"              # Pausado / Descontinuado


class Platform(str, Enum):
    KIWIFY = "kiwify"
    HOTMART = "hotmart"
    EDUZZ = "eduzz"
    BRAIP = "braip"
    OTHER = "other"


class OrderStatus(str, Enum):
    PAID = "paid"          # Aprovado / Pago
    WAITING_PAYMENT = "waiting_payment"  # Pix / Boleto gerado
    REFUNDED = "refunded"  # Reembolsado
    CHARGEBACK = "chargeback"
    CANCELED = "canceled"


# --- TABELAS ---

class MarketTrend(Base):
    """Armazena termos e nichos minerados de ferramentas como Google Trends, Meta Ads, etc."""
    __tablename__ = "market_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    niche: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(50), default="google_trends")  # ex: google_trends, meta_ads
    
    relative_interest: Mapped[int] = mapped_column(Integer, default=0) # 0 a 100 (Google Trends)
    trend_growth_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 2)) # Crescimento percentual
    
    status: Mapped[TrendStatus] = mapped_column(
        SQLEnum(TrendStatus, native_enum=False),
        default=TrendStatus.NEW,
        index=True
    )
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON) # Salva dados brutos adicionais
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relacionamento caso a tendência vire diretamente um produto
    products: Mapped[List["Product"]] = relationship(back_populates="origin_trend")


class Product(Base):
    """Catálogo de infoprodutos / apostilas de baixo ticket."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    niche: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Preço habitual do low ticket (ex: R$ 19,90 a R$ 97,00)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    checkout_url: Mapped[Optional[str]] = mapped_column(String(500))
    delivery_url: Mapped[Optional[str]] = mapped_column(String(500)) # Link do PDF / Drive / Área de membros
    
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, native_enum=False),
        default=ProductStatus.IDEA,
        index=True
    )
    
    # Anúncios e copys geradas por IA para este produto
    ad_copies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Conteúdo didático, fluxogramas de estudo e slides gerados por IA
    delivery_content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # FK opcional apontando para a tendência que gerou este produto
    trend_id: Mapped[Optional[int]] = mapped_column(ForeignKey("market_trends.id"), nullable=True)
    origin_trend: Mapped[Optional["MarketTrend"]] = relationship(back_populates="products")

    # Relacionamento com as vendas
    orders: Mapped[List["Order"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class Order(Base):
    """Transações e vendas recebidas via webhooks de checkouts."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificadores da plataforma de pagamento
    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform, native_enum=False),
        nullable=False,
        index=True
    )
    external_order_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Associação com o produto cadastrado (opcional caso a venda venha com ID desconhecido)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    product: Mapped[Optional["Product"]] = relationship(back_populates="orders")
    
    # Dados da transação financeira
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False) # Valor bruto pago
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))         # Valor líquido após taxas
    currency: Mapped[str] = mapped_column(String(10), default="BRL")
    
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False),
        default=OrderStatus.PAID,
        index=True
    )
    
    # Dados do cliente
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Payload completo recebido do webhook para auditoria/debug
    payload_raw: Mapped[Optional[dict]] = mapped_column(JSON)
    
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppSetting(Base):
    """Armazena configurações dinâmicas do sistema (ex: chaves de API da Kiwify, Hotmart, etc.)"""
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

