from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")

class PaginationParams(BaseModel):
    """
    Input parameters for pagination.
    """
    page: int = Field(default=1, ge=1, description="Page number (starts at 1)")
    size: int = Field(default=10, ge=1, le=100, description="Number of items per page")

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized response structure for paginated data.
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

async def paginate(
    session: AsyncSession,
    query: Select,
    params: PaginationParams,
) -> PaginatedResponse:
    """
    Applies offset-based pagination to a SQLAlchemy query.
    
    Args:
        session: SQLAlchemy async session.
        query: Original query (Select object).
        params: Pagination parameters (page, size).
        
    Returns:
        PaginatedResponse containing items and pagination metadata.
    """
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    offset = (params.page - 1) * params.size
    paginated_query = query.offset(offset).limit(params.size)
    
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    
    pages = (total + params.size - 1) // params.size if total > 0 else 0

    return PaginatedResponse(
        items=list(items),
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )
