from dependency_injector import containers, providers
from app.v1_0.v1_containers import APIContainer
from app.core import async_session
from app.core.settings import settings
from app.infraestructure.redis import get_redis_client, close_redis_client, RedisCacheService
from app.infraestructure.mail import MailService

async def init_redis_resource():
    client = await get_redis_client()
    try:
        yield client
    finally:
        await close_redis_client(client)

class ApplicationContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.v1_0.modules.auth.dependencies",
            "app.middlewares.auth",
            "app.middlewares.roles",
            "app.middlewares.audit",
            "app.v1_0.modules.auth.router",
            "app.v1_0.modules.customer.router",
        ]
    )
    db_session = providers.Object(async_session)

    redis_client = providers.Resource(init_redis_resource)

    redis_cache_service = providers.Singleton(
        RedisCacheService,
        redis_client=redis_client
    )

    mail_service = providers.Singleton(
        MailService
    )

    api_container = providers.Container(
        APIContainer,
        db_session=db_session,
        redis_cache_service=redis_cache_service,
        mail_service=mail_service,
        app_env=providers.Object(settings.APP_ENV)
    )


    async def init_resources(self):
        """Initialize asynchronous resources if necessary"""
        await self.redis_client()

    async def shutdown_resources(self):
        """Clean resources if necessary"""
        await self.redis_client.shutdown()
