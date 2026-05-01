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
        """
        Initializes the generic service with a specific repository and model class.

        Args:
            repository: Data access layer for the specific node type (Warehouse/Seaport).
            model_class: The SQLAlchemy model class (Warehouse or Seaport).
        """
        self.repo = repository
        self.model_class = model_class

    async def list_nodes(
        self,
        skip: int = 0,
        limit: int = 100,
        continent: Optional[str] = None,
        country: Optional[str] = None,
    ) -> LogisticsNodeListResponseDTO:
        """
        Retrieves a paginated and filtered list of logistics nodes.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            continent: Optional filter by continent name.
            country: Optional filter by country name.

        Returns:
            LogisticsNodeListResponseDTO containing the list of nodes and total count.
        """
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
        """
        Retrieves a specific logistics node by its unique identifier.

        Args:
            node_id: The unique identifier of the node.

        Returns:
            LogisticsNodeResponseDTO containing the node details.

        Raises:
            HTTPException: 404 if the node is not found.
        """
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )
        return LogisticsNodeResponseDTO.model_validate(node)

    async def create_node(
        self, payload: LogisticsNodeCreateDTO
    ) -> LogisticsNodeResponseDTO:
        """
        Creates a new logistics node and persists it to the system.

        Workflow:
        1. Initializes the target entity class (Warehouse/Seaport) with provided data.
        2. Relies on the ORM's @validates("country") trigger to auto-derive the continent.
        3. Persists the node and logs the creation event including the resolved geography.

        Args:
            payload: Data transfer object containing the new node's details.

        Returns:
            LogisticsNodeResponseDTO with the created node data.
        """
        node = self.model_class(
            name=payload.name,
            address=payload.address,
            city=payload.city,
            country=payload.country,
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
        Updates an existing logistics node's attributes partially.

        Workflow:
        1. Retrieves the node and verifies its existence.
        2. Identifies which fields are being updated for the audit trail.
        3. If `country` is changed, the ORM re-derives the `continent` automatically.
        4. Persists the changes and calculates the before/after state diff.
        5. Pushes the diff into the global audit context for middleware processing.

        Args:
            node_id: The unique identifier of the node to update.
            payload: Data transfer object containing the fields to update.

        Returns:
            LogisticsNodeResponseDTO with the updated node details.

        Raises:
            HTTPException: 404 if the node is not found.
        """
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        audit_fields = list(update_data.keys())
        if "country" in audit_fields and "continent" not in audit_fields:
            audit_fields.append("continent")
        before_state = {field: getattr(node, field) for field in audit_fields}

        for field, value in update_data.items():
            setattr(node, field, value)

        updated = await self.repo.update(node)

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
        """
        Permanently removes a logistics node from the system.

        Workflow:
        1. Retrieves the node and verifies it exists.
        2. Invokes the repository to delete the record.

        Args:
            node_id: The unique identifier of the node to delete.

        Raises:
            HTTPException: 404 if the node is not found.
        """
        node = await self.repo.get_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} '{node_id}' not found",
            )
        await self.repo.delete(node)
