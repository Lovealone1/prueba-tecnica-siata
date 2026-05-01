from dependency_injector import containers, providers
from app.v1_0.auth.service import AuthService
from app.v1_0.auth.repository import UserRepository
from app.v1_0.auth.otp import DevOtpSender, ProdOtpSender

class APIContainer(containers.DeclarativeContainer):
    """
    Container of dependencies specific to the v1_0 API version.
    Here you can inject repositories, services and use cases.
    """
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
