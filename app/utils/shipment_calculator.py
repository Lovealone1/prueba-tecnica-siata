from datetime import datetime, timedelta
from typing import Tuple

from app.infraestructure.models.shipment import ShippingType
from app.infraestructure.models.product import ProductSize

class ShipmentCalculator:
    """
    Calculates Shipping Type, ETA, and Base Cost based on geographical distance
    and product size.
    """

    # Multipliers for different product sizes
    SIZE_MULTIPLIERS = {
        ProductSize.SMALL: 0.5,
        ProductSize.MEDIUM: 0.75,
        ProductSize.LARGE: 1.25,
        ProductSize.EXTRA_LARGE: 2.0
    }

    # Base pricing and ETA per unit for geographic zones
    # (cost_base, eta_days)
    ZONES = {
        "NATIONAL": {"cost": 50.0, "eta_days": 2, "type": ShippingType.LAND},
        "INTERNATIONAL_SAME_CONTINENT": {"cost": 150.0, "eta_days": 5, "type": ShippingType.LAND},
        "INTERCONTINENTAL": {"cost": 500.0, "eta_days": 25, "type": ShippingType.MARITIME}
    }

    # Thresholds and extra fees if quantity is exceeded
    THRESHOLDS = {
        ProductSize.SMALL: {"limit": 100, "fee": 20.0},
        ProductSize.MEDIUM: {"limit": 50, "fee": 50.0},
        ProductSize.LARGE: {"limit": 25, "fee": 100.0},
        ProductSize.EXTRA_LARGE: {"limit": 10, "fee": 200.0}
    }

    @classmethod
    def calculate(
        cls, 
        dispatch_country: str, 
        dispatch_continent: str, 
        dest_country: str, 
        dest_continent: str, 
        product_size: ProductSize, 
        quantity: int,
        registry_date: datetime
    ) -> Tuple[ShippingType, datetime, float, float]:
        """
        Determines the shipping parameters.
        
        Returns:
            Tuple containing:
            - ShippingType
            - Shipping Date (ETA)
            - Base Fee Price (before extra fees)
            - Applied Extra Fee (if threshold exceeded)
        """
        
        d_country = dispatch_country.strip().upper()
        d_continent = dispatch_continent.strip().upper()
        dest_c = dest_country.strip().upper()
        dest_cont = dest_continent.strip().upper()

        if d_country == dest_c:
            zone_key = "NATIONAL"
        elif d_continent == dest_cont:
            zone_key = "INTERNATIONAL_SAME_CONTINENT"
        else:
            zone_key = "INTERCONTINENTAL"

        zone_data = cls.ZONES[zone_key]
        shipping_type = zone_data["type"]
        eta = registry_date + timedelta(days=zone_data["eta_days"])
        
        # 1. Base price calculation
        size_multiplier = cls.SIZE_MULTIPLIERS.get(product_size, 1.0)
        base_fee_per_unit = zone_data["cost"] * size_multiplier
        total_base_price = base_fee_per_unit * quantity

        # 2. Extra fee logic
        extra_fee = 0.0
        threshold = cls.THRESHOLDS.get(product_size)
        if threshold and quantity > threshold["limit"]:
            extra_fee = threshold["fee"]

        return shipping_type, eta, total_base_price, extra_fee

