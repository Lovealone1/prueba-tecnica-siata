import pytest
from datetime import datetime, timezone
from app.utils.shipment_calculator import ShipmentCalculator
from app.infraestructure.models.shipment import ShippingType
from app.infraestructure.models.product import ProductSize

def test_calculate_national_shipping():
    # Setup
    registry_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
    
    # Execute
    shipping_type, eta, base_price, extra_fee = ShipmentCalculator.calculate(
        dispatch_country="Colombia",
        dispatch_continent="South America",
        dest_country="Colombia",
        dest_continent="South America",
        product_size=ProductSize.SMALL,
        quantity=5,
        registry_date=registry_date
    )
    
    # Assert
    assert shipping_type == ShippingType.LAND
    assert eta.day == 3 # 2 days ETA
    # Small multiplier is 0.5. National cost is 50.0. 
    # 50.0 * 0.5 * 5 = 125.0
    assert base_price == 125.0
    assert extra_fee == 0.0

def test_calculate_international_same_continent():
    # Setup
    registry_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
    
    # Execute
    shipping_type, eta, base_price, extra_fee = ShipmentCalculator.calculate(
        dispatch_country="Colombia",
        dispatch_continent="South America",
        dest_country="Brazil",
        dest_continent="South America",
        product_size=ProductSize.MEDIUM,
        quantity=10,
        registry_date=registry_date
    )
    
    # Assert
    assert shipping_type == ShippingType.LAND
    assert eta.day == 6 # 5 days ETA
    # Medium multiplier is 0.75. Same continent cost is 150.0.
    # 150.0 * 0.75 * 10 = 1125.0
    assert base_price == 1125.0
    assert extra_fee == 0.0

def test_calculate_intercontinental_maritime():
    # Setup
    registry_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
    
    # Execute
    shipping_type, eta, base_price, extra_fee = ShipmentCalculator.calculate(
        dispatch_country="Colombia",
        dispatch_continent="South America",
        dest_country="China",
        dest_continent="Asia",
        product_size=ProductSize.LARGE,
        quantity=2,
        registry_date=registry_date
    )
    
    # Assert
    assert shipping_type == ShippingType.MARITIME
    assert (eta - registry_date).days == 25
    # Large multiplier is 1.25. Intercontinental cost is 500.0.
    # 500.0 * 1.25 * 2 = 1250.0
    assert base_price == 1250.0

def test_calculate_extra_fee_threshold_exceeded():
    # Setup
    registry_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
    
    # Extra Large threshold is 10. Fee is 200.0.
    # Execute
    _, _, _, extra_fee = ShipmentCalculator.calculate(
        dispatch_country="USA",
        dispatch_continent="North America",
        dest_country="Mexico",
        dest_continent="North America",
        product_size=ProductSize.EXTRA_LARGE,
        quantity=11,
        registry_date=registry_date
    )
    
    # Assert
    assert extra_fee == 200.0

def test_calculate_no_extra_fee_at_limit():
    # Setup
    registry_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
    
    # Small threshold is 100.
    # Execute
    _, _, _, extra_fee = ShipmentCalculator.calculate(
        dispatch_country="USA",
        dispatch_continent="North America",
        dest_country="USA",
        dest_continent="North America",
        product_size=ProductSize.SMALL,
        quantity=100,
        registry_date=registry_date
    )
    
    # Assert
    assert extra_fee == 0.0
