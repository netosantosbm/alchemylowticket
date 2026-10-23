import re
import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from models import Product, Order, OrderStatus, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/api/products", tags=["Products"])

def generate_slug(text: str) -> str:
    cleaned = re.sub(r'[^\w\s-]', '', text.lower().strip())
    slug = re.sub(r'[-\s]+', '-', cleaned)
    return f"{slug}-{uuid.uuid4().hex[:6]}"

@router.get("", response_model=List[ProductResponse])
def get_products(
    status: Optional[str] = None,
    niche: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if status and status != "Todos":
        query = query.filter(Product.status == status)
    if niche and niche != "Todos":
        query = query.filter(Product.niche == niche)
    
    products = query.order_by(desc(Product.created_at)).all()
    
    # Calculate order aggregates per product (using gross_amount)
    product_stats = db.query(
        Order.product_id,
        func.count(Order.id).label("sales_count"),
        func.sum(Order.gross_amount).label("total_revenue")
    ).filter(Order.status == OrderStatus.PAID).group_by(Order.product_id).all()
    
    stats_map = {p_id: (count, float(revenue or 0.0)) for p_id, count, revenue in product_stats if p_id is not None}
    
    results = []
    for prod in products:
        count, rev = stats_map.get(prod.id, (0, 0.0))
        results.append(ProductResponse(
            id=prod.id,
            title=prod.title,
            slug=prod.slug,
            niche=prod.niche,
            description=prod.description,
            price=float(prod.price),
            checkout_url=prod.checkout_url,
            delivery_url=prod.delivery_url,
            status=prod.status,
            ad_copies=prod.ad_copies,
            trend_id=prod.trend_id,
            created_at=prod.created_at,
            updated_at=prod.updated_at,
            total_sales=count,
            total_revenue=rev
        ))
    return results

@router.post("", response_model=ProductResponse)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    data = product_in.model_dump()
    if not data.get("slug"):
        data["slug"] = generate_slug(data["title"])

    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=product.id,
        title=product.title,
        slug=product.slug,
        niche=product.niche,
        description=product.description,
        price=float(product.price),
        checkout_url=product.checkout_url,
        delivery_url=product.delivery_url,
        status=product.status,
        ad_copies=product.ad_copies,
        trend_id=product.trend_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
        total_sales=0,
        total_revenue=0.0
    )

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    sales_info = db.query(
        func.count(Order.id),
        func.sum(Order.gross_amount)
    ).filter(Order.product_id == product_id, Order.status == OrderStatus.PAID).first()
    
    count = sales_info[0] or 0
    revenue = float(sales_info[1] or 0.0)
    
    return ProductResponse(
        id=product.id,
        title=product.title,
        slug=product.slug,
        niche=product.niche,
        description=product.description,
        price=float(product.price),
        checkout_url=product.checkout_url,
        delivery_url=product.delivery_url,
        status=product.status,
        ad_copies=product.ad_copies,
        trend_id=product.trend_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
        total_sales=count,
        total_revenue=revenue
    )

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, update_data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    sales_info = db.query(
        func.count(Order.id),
        func.sum(Order.gross_amount)
    ).filter(Order.product_id == product_id, Order.status == OrderStatus.PAID).first()
    
    return ProductResponse(
        id=product.id,
        title=product.title,
        slug=product.slug,
        niche=product.niche,
        description=product.description,
        price=float(product.price),
        checkout_url=product.checkout_url,
        delivery_url=product.delivery_url,
        status=product.status,
        ad_copies=product.ad_copies,
        trend_id=product.trend_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
        total_sales=sales_info[0] or 0,
        total_revenue=float(sales_info[1] or 0.0)
    )

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(product)
    db.commit()
    return {"message": "Produto removido com sucesso"}
