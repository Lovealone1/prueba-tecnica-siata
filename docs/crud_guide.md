# Guide: How to create a basic CRUD with Clean Architecture

> Reference generated from the `Customer` module. Follow these steps **in the same order** every time you need a new CRUD.

---

## File structure to create

```
app/v1_0/modules/<entity>/
├── __init__.py
├── domain.py          
├── repository.py      
├── service.py         
├── router.py          
└── dto/
    ├── __init__.py
    └── schemas.py     
```

---

## Step 1 — Create the ORM model (if it doesn't exist)

The model goes in `app/infraestructure/models/<entity>.py`.

```python
from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.infraestructure.models.base import Base

class MyEntity(Base):
    __tablename__ = "my_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )
```

---

## Step 2 — Alembic Migration

Create scripts in `alembic/versions/<timestamp>_create_<entity>_table.py`:

```python
async def _up(conn):
    await conn.execute(text("""
        CREATE TABLE my_entities (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name        VARCHAR(255) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))

async def _down(conn):
    await conn.execute(text("DROP TABLE IF EXISTS my_entities;"))
```

---

## Step 3 — Domain Layer (`domain.py`)

Define the abstract repository interface. The rule is: **the service only knows this contract**.

```python
import uuid
from typing import Optional, List
from abc import ABC, abstractmethod
from app.infraestructure.models.my_entity import MyEntity

class IMyEntityRepository(ABC):
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MyEntity]: ...
    @abstractmethod
    async def count_all(self) -> int: ...
    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[MyEntity]: ...
    @abstractmethod
    async def create(self, entity: MyEntity) -> MyEntity: ...
    @abstractmethod
    async def update(self, entity: MyEntity) -> MyEntity: ...
    @abstractmethod
    async def delete(self, entity: MyEntity) -> None: ...
```

---

## Step 4 — DTOs (`dto/schemas.py`)

Three categories: **CreateDTO**, **UpdateDTO** (partial, for PATCH), and **ResponseDTO**.

```python
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class MyEntityCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class MyEntityUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

class MyEntityResponseDTO(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class MyEntityListResponseDTO(BaseModel):
    data: list[MyEntityResponseDTO]
    total: int
    skip: int
    limit: int
```

---

## Step 5 — Repository (`repository.py`)

Implement the port using `async_sessionmaker`. Follow the established pattern:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, func
from .domain import IMyEntityRepository
from app.infraestructure.models.my_entity import MyEntity

class MyEntityRepository(IMyEntityRepository):
    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_all(self, skip=0, limit=100):
        async with self.db_maker() as session:
            result = await session.execute(
                select(MyEntity).offset(skip).limit(limit)
                               .order_by(MyEntity.created_at.desc())
            )
            return list(result.scalars().all())

    async def count_all(self) -> int:
        async with self.db_maker() as session:
            result = await session.execute(
                select(func.count()).select_from(MyEntity)
            )
            return result.scalar_one()

    async def get_by_id(self, entity_id):
        async with self.db_maker() as session:
            result = await session.execute(
                select(MyEntity).where(MyEntity.id == entity_id)
            )
            return result.scalar_one_or_none()

    async def create(self, entity):
        async with self.db_maker() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity):
        async with self.db_maker() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, entity):
        async with self.db_maker() as session:
            existing = await session.get(MyEntity, entity.id)
            if existing:
                await session.delete(existing)
                await session.commit()
```

---

## Step 6 — Service (`service.py`)

Here lives **all** the business logic. It does not care about SQLAlchemy or FastAPI Request.

```python
import uuid
from fastapi import HTTPException, status
from app.core.logger import logger
from app.infraestructure.models.my_entity import MyEntity
from .domain import IMyEntityRepository
from .dto.schemas import MyEntityCreateDTO, MyEntityUpdateDTO, MyEntityListResponseDTO, MyEntityResponseDTO

class MyEntityService:
    def __init__(self, my_entity_repository: IMyEntityRepository) -> None:
        self.repo = my_entity_repository

    async def list(self, skip=0, limit=100) -> MyEntityListResponseDTO:
        items = await self.repo.get_all(skip=skip, limit=limit)
        total = await self.repo.count_all()
        return MyEntityListResponseDTO(
            data=[MyEntityResponseDTO.model_validate(i) for i in items],
            total=total, skip=skip, limit=limit,
        )

    async def get(self, entity_id: uuid.UUID) -> MyEntityResponseDTO:
        item = await self.repo.get_by_id(entity_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        return MyEntityResponseDTO.model_validate(item)

    async def create(self, payload: MyEntityCreateDTO) -> MyEntityResponseDTO:
        entity = MyEntity(name=payload.name)
        created = await self.repo.create(entity)
        logger.info(f"[MY_ENTITY] Created id={created.id}")
        return MyEntityResponseDTO.model_validate(created)

    async def update(self, entity_id: uuid.UUID, payload: MyEntityUpdateDTO) -> MyEntityResponseDTO:
        item = await self.repo.get_by_id(entity_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        updated = await self.repo.update(item)
        return MyEntityResponseDTO.model_validate(updated)

    async def delete(self, entity_id: uuid.UUID) -> None:
        item = await self.repo.get_by_id(entity_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        await self.repo.delete(item)
```

---

## Step 7 — Router (`router.py`)

### Security Rules

| Method | Auth | Roles | Audit Log |
|--------|------|-------|-----------|
| GET (list + detail) | ✅ `require_roles` | USER, ADMIN | ❌ |
| POST | ✅ `require_roles` | USER, ADMIN | ❌ |
| PATCH | ✅ via `audit_log` | USER, ADMIN | ✅ |
| DELETE | ✅ via `audit_log` | USER, ADMIN | ✅ |

> **Important**: `audit_log` internally already calls `require_authenticated`, which validates the JWT. For PATCH and DELETE use `audit_log` as a direct dependency instead of `require_roles`. For GET and POST use `require_roles` directly.

```python
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject
from app.infraestructure.models.user import User, GlobalRole
from app.middlewares import require_roles, audit_log
from .dto.schemas import MyEntityCreateDTO, MyEntityUpdateDTO, MyEntityResponseDTO, MyEntityListResponseDTO
from .service import MyEntityService

router = APIRouter(prefix="/my-entities", tags=["MyEntity"])
_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))

@router.get("/", response_model=MyEntityListResponseDTO)
@inject
async def list_entities(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    _u: User = _allowed_roles,
    service: MyEntityService = Depends(Provide["my_entity_service"]),
):
    return await service.list(skip=skip, limit=limit)

@router.get("/{entity_id}", response_model=MyEntityResponseDTO)
@inject
async def get_entity(
    entity_id: uuid.UUID,
    _u: User = _allowed_roles,
    service: MyEntityService = Depends(Provide["my_entity_service"]),
):
    return await service.get(entity_id)

@router.post("/", response_model=MyEntityResponseDTO, status_code=status.HTTP_201_CREATED)
@inject
async def create_entity(
    payload: MyEntityCreateDTO,
    _u: User = _allowed_roles,
    service: MyEntityService = Depends(Provide["my_entity_service"]),
):
    return await service.create(payload)

@router.patch("/{entity_id}", response_model=MyEntityResponseDTO)
@inject
async def update_entity(
    entity_id: uuid.UUID,
    payload: MyEntityUpdateDTO,
    _u: User = Depends(audit_log(action="my_entity.update", metadata={"entity": "MyEntity"})),
    service: MyEntityService = Depends(Provide["my_entity_service"]),
):
    return await service.update(entity_id, payload)

@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_entity(
    entity_id: uuid.UUID,
    _u: User = Depends(audit_log(action="my_entity.delete", metadata={"entity": "MyEntity"})),
    service: MyEntityService = Depends(Provide["my_entity_service"]),
):
    await service.delete(entity_id)
```

---

## Step 8 — Register in DI container (`v1_containers.py`)

```python
from app.v1_0.modules.my_entity.repository import MyEntityRepository
from app.v1_0.modules.my_entity.service import MyEntityService

my_entity_repository = providers.Factory(
    MyEntityRepository,
    db_maker=db_session,
)

my_entity_service = providers.Singleton(
    MyEntityService,
    my_entity_repository=my_entity_repository,
)
```

---

## Step 9 — Register the router (`v1_0/routers/__init__.py`)

```python
from app.v1_0.modules.my_entity.router import router as my_entity_router

defined_routers: List[APIRouter] = [
    auth_router,
    customer_router,
    my_entity_router,   
]
```

---

## Step 10 — Add wiring config (`app_containers.py`)

```python
wiring_config = containers.WiringConfiguration(
    modules=[
        "app.v1_0.modules.my_entity.router",  
    ]
)
```

---

## Verification Checklist

- [ ] ORM Model created in `app/infraestructure/models/`
- [ ] Alembic Migration with `_up` and `_down`
- [ ] `domain.py` with abstract interface `IXxxRepository`
- [ ] `dto/schemas.py` with `CreateDTO`, `UpdateDTO`, `ResponseDTO` and `ListResponseDTO`
- [ ] `repository.py` implementing the interface with `async_sessionmaker`
- [ ] `service.py` with all business logic and port injection
- [ ] `router.py` with proper security: `require_roles` on GET/POST, `audit_log` on PATCH/DELETE
- [ ] Provider registered in `v1_containers.py` (factory for repo, singleton for service)
- [ ] Router registered in `v1_0/routers/__init__.py`
- [ ] Router module in `wiring_config` of `app_containers.py`

---

## Key Project Conventions

| Concept | Rule |
|----------|-------|
| Table name | plural `snake_case` (`customers`, `products`) |
| Primary UUID | `server_default=func.uuid_generate_v4()` |
| Timestamps | `created_at` + `updated_at` with timezone, `server_default=func.now()` |
| Email | Use `CITEXT` for case-insensitive search |
| Repo provider | `providers.Factory` (new instance per call) |
| Service provider | `providers.Singleton` (shared instance) |
| Audit log | Only on mutations with irreversible effects: PATCH, DELETE |
| Basic logging | `logger.info(...)` in the service after creation operations |
