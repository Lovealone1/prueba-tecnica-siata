from dependency_injector import containers, providers
from app.v1_0.modules.auth.service import AuthService
from app.v1_0.modules.auth.repository import UserRepository
from app.v1_0.modules.auth.otp import DevOtpSender, ProdOtpSender
from app.v1_0.modules.customer.repository import CustomerRepository
from app.v1_0.modules.customer.service import CustomerService
from app.v1_0.modules.product.repository import ProductRepository
from app.v1_0.modules.product.service import ProductService
from app.v1_0.modules.logistics.repository import WarehouseRepository, SeaportRepository
from app.v1_0.modules.logistics.service import LogisticsNodeService
from app.v1_0.modules.shipment.repository import ShipmentRepository
from app.v1_0.modules.shipment.service import ShipmentService
from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport
from app.v1_0.modules.user.repository import AdminUserRepository
from app.v1_0.modules.user.service import AdminUserService


class APIContainer(containers.DeclarativeContainer):
    """
    Container of dependencies specific to the v1_0 API version.
    Here you can inject repositories, services and use cases.
    """
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.v1_0.modules.auth.router",
            "app.v1_0.modules.customer.router",
            "app.v1_0.modules.product.router",
            "app.v1_0.modules.logistics.warehouse_router",
            "app.v1_0.modules.logistics.seaport_router",
            "app.v1_0.modules.shipment.router",
            "app.v1_0.modules.user.router",
        ]
    )
    db_session = providers.Dependency()
    redis_cache_service = providers.Dependency()
    mail_service = providers.Dependency()
    app_env = providers.Dependency()

    user_repository = providers.Factory(
        UserRepository,
        db_maker=db_session
    )

    otp_sender = providers.Selector(
        app_env,
        development=providers.Factory(DevOtpSender),
        production=providers.Factory(ProdOtpSender, mail_service=mail_service)
    )

    auth_service = providers.Singleton(
        AuthService,
        user_repository=user_repository,
        redis_cache=redis_cache_service,
        otp_sender=otp_sender
    )

    # Customer

    customer_repository = providers.Factory(
        CustomerRepository,
        db_maker=db_session,
    )

    customer_service = providers.Singleton(
        CustomerService,
        customer_repository=customer_repository,
    )

    # Product

    product_repository = providers.Factory(
        ProductRepository,
        db_maker=db_session,
    )

    product_service = providers.Singleton(
        ProductService,
        product_repository=product_repository,
    )

    # Logistics — Warehouse

    warehouse_repository = providers.Factory(
        WarehouseRepository,
        db_maker=db_session,
        model_class=providers.Object(Warehouse),
    )

    warehouse_service = providers.Singleton(
        LogisticsNodeService,
        repository=warehouse_repository,
        model_class=providers.Object(Warehouse),
    )

    # Logistics — Seaport

    seaport_repository = providers.Factory(
        SeaportRepository,
        db_maker=db_session,
        model_class=providers.Object(Seaport),
    )

    seaport_service = providers.Singleton(
        LogisticsNodeService,
        repository=seaport_repository,
        model_class=providers.Object(Seaport),
    )

    # Shipment

    shipment_repository = providers.Factory(
        ShipmentRepository,
        db_maker=db_session,
    )

    shipment_service = providers.Singleton(
        ShipmentService,
        shipment_repo=shipment_repository,
        customer_repo=customer_repository,
        product_repo=product_repository,
        warehouse_repo=warehouse_repository,
        seaport_repo=seaport_repository,
        redis_cache=redis_cache_service,
    )

    # User Admin

    admin_user_repository = providers.Factory(
        AdminUserRepository,
        db_maker=db_session,
    )

    admin_user_service = providers.Singleton(
        AdminUserService,
        user_repository=admin_user_repository,
        redis_cache=redis_cache_service,
    )
