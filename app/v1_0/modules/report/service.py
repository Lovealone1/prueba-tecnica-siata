from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.customer import Customer
from app.infraestructure.models.product import Product
from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport
from app.infraestructure.models.shipment import Shipment, ShippingStatus
from .dto.schemas import (
    DashboardReportDTO,
    ShipmentStatsDTO,
    ShipmentStatusCounts,
    DestinationCount,
    RecentShipmentDTO,
)


class ReportService:
    """
    Aggregates stats from multiple repositories in a single optimized
    DB session to power the dashboard report endpoint.
    """

    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_dashboard_stats(self) -> DashboardReportDTO:
        from app.core.logger import logger
        try:
            async with self.db_maker() as session:
                # ── Totals ───────────────────────────────────────────────────────
                total_customers = (await session.execute(select(func.count(Customer.id)))).scalar_one()
                total_products = (await session.execute(select(func.count(Product.id)))).scalar_one()
                total_warehouses = (await session.execute(select(func.count(Warehouse.id)))).scalar_one()
                total_seaports = (await session.execute(select(func.count(Seaport.id)))).scalar_one()
                total_shipments = (await session.execute(select(func.count(Shipment.id)))).scalar_one()
                
                total_revenue_val = (await session.execute(select(func.sum(Shipment.total_price)))).scalar()
                total_revenue = float(total_revenue_val or 0.0)

                # ── Shipments by Status ──────────────────────────────────────────
                status_res = await session.execute(
                    select(Shipment.shipping_status, func.count(Shipment.id))
                    .group_by(Shipment.shipping_status)
                )
                raw_status = {row[0].value: row[1] for row in status_res.all()}
                status_counts = ShipmentStatusCounts(
                    PENDING=raw_status.get("PENDING", 0),
                    SENT=raw_status.get("SENT", 0),
                    DELIVERED=raw_status.get("DELIVERED", 0),
                )

                # ── Top Destinations ────────────────────────────────────────────
                dest_expr = func.coalesce(Warehouse.country, Seaport.country)
                dest_res = await session.execute(
                    select(
                        dest_expr.label("country"),
                        func.count(Shipment.id).label("count"),
                    )
                    .outerjoin(Warehouse, Shipment.warehouse_id == Warehouse.id)
                    .outerjoin(Seaport, Shipment.seaport_id == Seaport.id)
                    .group_by(dest_expr)
                    .order_by(func.count(Shipment.id).desc())
                    .limit(5)
                )
                top_destinations: List[DestinationCount] = [
                    DestinationCount(country=row.country, count=row.count)
                    for row in dest_res.all()
                ]

                # ── Recent Shipments (last 5) ────────────────────────────────────
                recent_res = await session.execute(
                    select(Shipment)
                    .order_by(desc(Shipment.created_at))
                    .limit(5)
                )
                recent_shipments: List[RecentShipmentDTO] = [
                    RecentShipmentDTO(
                        guide_number=s.guide_number,
                        shipping_status=s.shipping_status.value,
                        shipping_type=s.shipping_type.value,
                        total_price=float(s.total_price),
                        registry_date=s.registry_date.isoformat() if s.registry_date else "",
                    )
                    for s in recent_res.scalars().all()
                ]

            return DashboardReportDTO(
                total_customers=total_customers,
                total_products=total_products,
                total_warehouses=total_warehouses,
                total_seaports=total_seaports,
                shipment_stats=ShipmentStatsDTO(
                    total_shipments=total_shipments,
                    total_revenue=total_revenue,
                    status_counts=status_counts,
                    top_destinations=top_destinations,
                ),
                recent_shipments=recent_shipments,
            )
        except Exception as e:
            logger.error(f"Error generating dashboard report: {str(e)}", exc_info=True)
            raise e
