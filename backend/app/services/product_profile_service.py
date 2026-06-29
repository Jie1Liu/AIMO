from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.company import Company
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductProfileService:
    def create_product(self, db: Session, payload: ProductCreate) -> Product:
        company_id = payload.company_id
        if company_id is None:
            company = Company(name=payload.company_name or "AIMO Demo Company")
            db.add(company)
            db.flush()
            company_id = company.id
        elif not db.get(Company, company_id):
            raise NotFoundError("Company not found.")

        data = payload.model_dump(exclude={"company_id", "company_name"})
        product = Product(company_id=company_id, **data)
        db.add(product)
        db.flush()
        return product

    def update_product(self, product: Product, payload: ProductUpdate) -> Product:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        return product
