from uuid import UUID

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import get_current_user_id

router = APIRouter(prefix='/products', tags=['products'])


# ----- GET /products - список всех объявлений -----
@router.get('/')
async def get_products(
        session: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
) -> list[ProductResponse]:
    """Получить список всех объявлений"""
    query = select(Product.__table__.columns)
    result = await session.execute(query)
    mapping_result = result.mappings().all()
    return [ProductResponse(**elem) for elem in mapping_result] if mapping_result else []


# ----- GET /products/{product_id} - одна задача -----
@router.get('/{product_id}')
async def get_product(
        product_id: UUID,
        session: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
) -> ProductResponse:
    """Получить объявление по ID"""
    query = select(Product.__table__.columns).filter_by(id=product_id)
    result = await session.execute(query)
    mapping_result = result.mappings().one_or_none()
    if not mapping_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')
    return ProductResponse(**mapping_result)


# ----- POST /products - создать объявление -----
@router.post('/', status_code=201)
async def create_product(
        product: ProductCreate,
        session: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
) -> ProductResponse:
    """Создать новое объявление"""
    values = product.model_dump()
    values["seller_id"] = user_id
    query = insert(Product).values(**values).returning(Product.__table__.columns)
    result = await session.execute(query)
    await session.commit()
    mapping_result = result.mappings().one_or_none()
    return ProductResponse(**mapping_result)


# ----- PUT /products/{product_id} - обновить объявление -----
@router.put('/{product_id}')
async def update_product(
        product_id: UUID,
        product: ProductCreate,
        session: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
) -> ProductResponse:
    """Обновить существующее объявление"""
    query = select(Product.__table__.columns).filter_by(id=product_id)
    result = await session.execute(query)
    mapping_result = result.mappings().one_or_none()
    if not mapping_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')

    query = update(Product).filter_by(id=product_id).values(**product.model_dump()).returning(Product.__table__.columns)
    result = await session.execute(query)
    await session.commit()
    mapping_result = result.mappings().one_or_none()
    return ProductResponse(**mapping_result)


# ----- DELETE /products/{product_id} - удалить объявление -----
@router.delete('/{product_id}', status_code=204)
async def delete_product(
        product_id: UUID,
        session: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
) -> None:
    """Удалить объявление"""
    query = select(Product.__table__.columns).filter_by(id=product_id)
    result = await session.execute(query)
    mapping_result = result.mappings().one_or_none()
    if not mapping_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')

    query = delete(Product).filter_by(id=product_id)
    await session.execute(query)
    await session.commit()
