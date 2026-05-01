from dependency_injector import containers, providers
from app.v1_0.modules.auth.service import AuthService
from app.v1_0.modules.auth.repository import UserRepository
from app.v1_0.modules.auth.otp import DevOtpSender, ProdOtpSender
from app.v1_0.modules.customer.repository import CustomerRepository
from app.v1_0.modules.customer.service import CustomerService
from app.v1_0.modules.product.repository import ProductRepository
from app.v1_0.modules.product.service import ProductService


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
