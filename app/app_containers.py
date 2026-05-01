from dependency_injector import containers, providers
from app.v1_0.v1_containers import APIContainer
from app.core import async_session

class ApplicationContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[

        ]
    )
    
    db_session = providers.Object(async_session)

    api_container = providers.Container(
        APIContainer
    )

    async def init_resources(self):
        """Initialize asynchronous resources if necessary"""
        pass

    async def shutdown_resources(self):
        """Clean resources if necessary"""
        pass
