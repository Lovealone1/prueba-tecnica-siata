from typing import Dict, List
from pydantic import BaseModel


class DestinationCount(BaseModel):
    country: str | None
    count: int


class ShipmentStatusCounts(BaseModel):
    PENDING: int = 0
    SENT: int = 0
    DELIVERED: int = 0


class ShipmentStatsDTO(BaseModel):
    total_shipments: int
    total_revenue: float
    status_counts: ShipmentStatusCounts
    top_destinations: List[DestinationCount]


class RecentShipmentDTO(BaseModel):
    guide_number: str
    shipping_status: str
    shipping_type: str
    total_price: float
    registry_date: str


class DashboardReportDTO(BaseModel):
    total_customers: int
    total_products: int
    total_warehouses: int
    total_seaports: int
    shipment_stats: ShipmentStatsDTO
    recent_shipments: List[RecentShipmentDTO]
