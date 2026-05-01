import uuid
from typing import Optional, Type, TypeVar

from fastapi import HTTPException, status

from app.core.logger import logger
from app.core.context import audit_context
from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport
from .domain import ILogisticsNodeRepository
from .dto.schemas import (
    LogisticsNodeCreateDTO,
    LogisticsNodeUpdateDTO,
    LogisticsNodeResponseDTO,
    LogisticsNodeListResponseDTO,
)

T = TypeVar("T", Warehouse, Seaport)


class LogisticsNodeService:
    """
    Generic domain service for logistics nodes (Warehouse / Seaport).

    Business rules:
    - `continent` is NEVER set directly by the service or client.
      It is auto-derived by the ORM model via @validates("country")
      calling LocationHelper.get_continent_by_country().
    - Updating `country` automatically re-derives `continent`.
    - `continent` cannot be patched independently (not present in UpdateDTO).
    """

    def __init__(
        self,
        repository: ILogisticsNodeRepository,
        model_class: Type,
    ) -> None:
        self.repo = repository
        self.model_class = model_class

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    async def list_nodes(
        self,
        skip: int = 0,
        limit: int = 100,
        continent: Optional[str] = None,
        country: Optional[str] = None,
    ) -> LogisticsNodeListResponseDTO:
        """Returns a paginated list of logistics nodes."""
        nodes = await self.repo.get_all(
            skip=skip, limit=limit, continent=continent, country=country
        )
        total = await self.repo.count_all(continent=continent, country=country)
        return LogisticsNodeListResponseDTO(
            data=[LogisticsNodeResponseDTO.model_validate(n) for n in nodes],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_node(self, node_id: uuid.UUID) -> LogisticsNodeResponseDTO:
        """Retrieves a logistics node by UUID. Raises 404 if not found."""
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )
        return LogisticsNodeResponseDTO.model_validate(node)

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    async def create_node(
        self, payload: LogisticsNodeCreateDTO
    ) -> LogisticsNodeResponseDTO:
        """
        Creates a new logistics node.

        The ORM @validates("country") trigger fires automatically when
        `country` is set, mapping the correct continent via LocationHelper.
        No manual continent assignment is needed here.
        """
        node = self.model_class(
            name=payload.name,
            address=payload.address,
            city=payload.city,
            country=payload.country,
            # continent is intentionally omitted — derived by the ORM validator
        )
        created = await self.repo.create(node)
        logger.info(
            f"[{self.model_class.__name__.upper()}] Created id={created.id} "
            f"country={created.country} continent={created.continent}"
        )
        return LogisticsNodeResponseDTO.model_validate(created)

    async def update_node(
        self,
        node_id: uuid.UUID,
        payload: LogisticsNodeUpdateDTO,
    ) -> LogisticsNodeResponseDTO:
        """
        Partially updates a logistics node (PATCH).

        - If `country` is included, the ORM @validates trigger re-derives
          `continent` automatically.
        - `continent` is never part of the payload, so it cannot be
          set to an inconsistent value (e.g. Colombia → Africa).
        - Captures a before/after diff and stores it in the audit context.
        """
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Capture 'before' state for audit diff
        # Include continent so the audit log reflects its potential change
        audit_fields = list(update_data.keys())
        if "country" in audit_fields and "continent" not in audit_fields:
            audit_fields.append("continent")
        before_state = {field: getattr(node, field) for field in audit_fields}

        # Apply updates — if country changes, @validates re-derives continent
        for field, value in update_data.items():
            setattr(node, field, value)

        updated = await self.repo.update(node)

        # Build diff and push to audit context
        diff = {}
        for field, old_val in before_state.items():
            new_val = getattr(updated, field)
            if str(old_val) != str(new_val):
                diff[field] = {"old": old_val, "new": new_val}

        if diff:
            ctx = audit_context.get().copy()
            ctx["diff"] = diff
            audit_context.set(ctx)

        return LogisticsNodeResponseDTO.model_validate(updated)

    async def delete_node(self, node_id: uuid.UUID) -> None:
        """Deletes a logistics node. Raises 404 if not found."""
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )
        await self.repo.delete(node)
